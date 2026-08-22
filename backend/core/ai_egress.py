"""Central authorization boundary for patient data leaving IAmina.

Authorization is provider-agnostic and lazy. Declaring a scope never performs
an external operation; consent and payload checks happen immediately before
real egress so deterministic safety paths remain available without AI.
"""

from __future__ import annotations

import inspect
import logging
import re
import unicodedata
from collections.abc import Mapping
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from functools import wraps
from types import MappingProxyType
from typing import Callable, Iterator, get_type_hints

from django.utils import timezone

from core.models import AIMediaConsentGrant, BasePatientProfile

logger = logging.getLogger(__name__)

TEXT = "text"
AUDIO = "audio"
IMAGE = "image"
DOCUMENT = "document"
_RAW_MEDIA_MODALITIES = frozenset({AUDIO, IMAGE, DOCUMENT})

# Unknown purposes and undeclared modalities are denied by construction.
_PURPOSE_MODALITIES: dict[str, frozenset[str]] = {
    "clinical_summary": frozenset({TEXT}),
    "doctor_brief": frozenset({TEXT}),
    "companion_chat": frozenset({TEXT}),
    "meal_vision": frozenset({IMAGE}),
    "glucometer_ocr": frozenset({IMAGE}),
    "voice_chat": frozenset({AUDIO, TEXT}),
    "voice_transcription": frozenset({AUDIO}),
    "document_ingest": frozenset({DOCUMENT, IMAGE, TEXT}),
}

_TEXT_PAYLOAD_FIELDS = frozenset({"system_prompt", "user_prompt"})
_TEXT_PAYLOAD_LIMITS: dict[str, dict[str, int]] = {
    "clinical_summary": {"system_prompt": 12_000, "user_prompt": 24_000},
    "doctor_brief": {"system_prompt": 12_000, "user_prompt": 16_000},
    "companion_chat": {"system_prompt": 20_000, "user_prompt": 24_000},
    "voice_chat": {"system_prompt": 20_000, "user_prompt": 24_000},
    "document_ingest": {"system_prompt": 12_000, "user_prompt": 48_000},
}

_DLP_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "email",
        re.compile(r"(?<![\w.+-])[\w.+-]+@[\w-]+(?:\.[\w-]+)+(?![\w.-])", re.IGNORECASE),
    ),
    (
        "phone",
        re.compile(r"(?<!\w)(?:\+?\d[\s.()\-/]*){8,15}(?!\w)"),
    ),
    (
        "moroccan_national_id",
        re.compile(r"(?<!\w)[A-Z]{1,2}[\s-]?\d{5,8}(?!\w)", re.IGNORECASE),
    ),
    (
        "uuid",
        re.compile(
            r"(?<![0-9a-f])[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}(?![0-9a-f])",
            re.IGNORECASE,
        ),
    ),
    (
        "firebase_uid",
        re.compile(r"(?<![A-Za-z0-9_-])[A-Za-z0-9_-]{24,128}(?![A-Za-z0-9_-])"),
    ),
    (
        "date_of_birth",
        re.compile(
            r"(?<!\d)(?:0?[1-9]|[12]\d|3[01])[\s./-](?:0?[1-9]|1[0-2])[\s./-](?:19|20)\d{2}(?!\d)"
        ),
    ),
)

_IDENTITY_LABEL_PATTERN = re.compile(
    r"(?:\b(?:nom(?:\s+complet)?|prenom|prénom|name|full\s+name|"
    r"telephone|téléphone|phone|mobile|email|e-mail|courriel|adresse|address|"
    r"cin|cni|passeport|passport|firebase\s*uid|django\s*id|patient\s*id|"
    r"date\s+de\s+naissance|date\s+of\s+birth|dob)\b|"
    r"(?:الاسم|الهاتف|البريد\s+الإلكتروني|العنوان|رقم\s+البطاقة|تاريخ\s+الميلاد))"
    r"\s*[:=\-–—]\s*\S+",
    re.IGNORECASE,
)

_ALLOWED_DLP_PLACEHOLDERS = frozenset(
    {
        "[PATIENT_NAME]",
        "[EMAIL]",
        "[PHONE]",
        "[ADDRESS]",
        "[NATIONAL_ID]",
        "[PATIENT_ID]",
        "[FIREBASE_UID]",
        "[DATE_OF_BIRTH]",
    }
)


class AIEgressDenied(PermissionError):
    """Raised when an external model operation is not policy-authorized."""


class AIConsentRequired(AIEgressDenied):
    """Raised when the required global or granular consent is absent."""


class AIPayloadDenied(AIEgressDenied):
    """Raised when an external AI payload violates its purpose contract."""


@dataclass(frozen=True)
class AIEgressContext:
    patient_id: int
    purpose: str
    modalities: frozenset[str]


@dataclass(frozen=True)
class AuthorizedTextPayload:
    """Immutable text payload that passed consent, allowlist, size and DLP checks."""

    purpose: str
    fields: Mapping[str, str]

    @property
    def system_prompt(self) -> str:
        return self.fields["system_prompt"]

    @property
    def user_prompt(self) -> str:
        return self.fields["user_prompt"]


_CURRENT_EGRESS: ContextVar[AIEgressContext | None] = ContextVar(
    "iamina_ai_egress_context",
    default=None,
)


def _validate_scope(purpose: str, modalities: frozenset[str]) -> None:
    policy_modalities = _PURPOSE_MODALITIES.get(purpose)
    if policy_modalities is None:
        raise AIEgressDenied(f"Unknown AI egress purpose: {purpose}")
    if not modalities or not modalities.issubset(policy_modalities):
        raise AIEgressDenied(
            f"Modalities {sorted(modalities)} are not authorized for purpose {purpose}"
        )


def _validate_raw_media_grant(purpose: str, modality: str) -> None:
    if modality not in _RAW_MEDIA_MODALITIES:
        raise AIEgressDenied(f"Modality {modality} is not a raw-media consent modality")
    _validate_scope(purpose, frozenset({modality}))


def grant_media_consent(
    patient_id: int,
    purpose: str,
    modality: str,
) -> AIMediaConsentGrant:
    """Create or reactivate one explicit purpose/modality media grant."""
    if not isinstance(patient_id, int) or patient_id <= 0:
        raise AIEgressDenied("A valid patient id is required for media consent")
    _validate_raw_media_grant(purpose, modality)
    now = timezone.now()
    grant, _ = AIMediaConsentGrant.objects.update_or_create(
        patient_id=patient_id,
        purpose=purpose,
        modality=modality,
        defaults={"granted_at": now, "revoked_at": None},
    )
    return grant


def revoke_media_consent(patient_id: int, purpose: str, modality: str) -> bool:
    """Revoke one grant; return False when no active grant existed."""
    if not isinstance(patient_id, int) or patient_id <= 0:
        raise AIEgressDenied("A valid patient id is required for media consent")
    _validate_raw_media_grant(purpose, modality)
    updated = AIMediaConsentGrant.objects.filter(
        patient_id=patient_id,
        purpose=purpose,
        modality=modality,
        revoked_at__isnull=True,
    ).update(revoked_at=timezone.now())
    return updated == 1


@contextmanager
def ai_egress_scope(
    patient_id: int,
    purpose: str,
    *modalities: str,
) -> Iterator[AIEgressContext]:
    """Declare the patient/purpose context for a possible external call."""
    if not isinstance(patient_id, int) or patient_id <= 0:
        raise AIEgressDenied("A valid patient id is required for AI egress")

    modality_set = frozenset(modalities)
    _validate_scope(purpose, modality_set)
    context = AIEgressContext(
        patient_id=patient_id,
        purpose=purpose,
        modalities=modality_set,
    )
    token = _CURRENT_EGRESS.set(context)
    try:
        yield context
    finally:
        _CURRENT_EGRESS.reset(token)


def assert_ai_egress_allowed(modality: str) -> AIEgressContext:
    """Authorize one real external model operation or raise before egress."""
    context = _CURRENT_EGRESS.get()
    if context is None:
        raise AIEgressDenied("External AI call attempted outside an authorized egress scope")
    if modality not in context.modalities:
        raise AIEgressDenied(
            f"Modality {modality} is not authorized for purpose {context.purpose}"
        )

    try:
        profile = BasePatientProfile.objects.only("ai_consent_given_at").get(
            patient_id=context.patient_id
        )
    except BasePatientProfile.DoesNotExist as exc:
        raise AIConsentRequired("Patient AI consent record is missing") from exc

    if profile.ai_consent_given_at is None:
        raise AIConsentRequired("Explicit patient AI consent is required")

    if modality in _RAW_MEDIA_MODALITIES:
        has_grant = AIMediaConsentGrant.objects.filter(
            patient_id=context.patient_id,
            purpose=context.purpose,
            modality=modality,
            revoked_at__isnull=True,
        ).exists()
        if not has_grant:
            raise AIConsentRequired(
                "Explicit media consent is required for "
                f"purpose={context.purpose} modality={modality}"
            )

    logger.debug(
        "ai_egress authorized patient_id=%s purpose=%s modality=%s",
        context.patient_id,
        context.purpose,
        modality,
    )
    return context


def _normalise_for_dlp(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value)
    return "".join(
        " " if unicodedata.category(char) in {"Zl", "Zp", "Zs"} else char
        for char in normalized
        if unicodedata.category(char) not in {"Cf"}
    )


def _mask_allowed_placeholders(value: str) -> str:
    masked = value
    for placeholder in _ALLOWED_DLP_PLACEHOLDERS:
        masked = masked.replace(placeholder, " ")
    return masked


def _detect_sensitive_text(value: str) -> frozenset[str]:
    inspected = _mask_allowed_placeholders(_normalise_for_dlp(value))
    findings = {
        finding_name
        for finding_name, pattern in _DLP_PATTERNS
        if pattern.search(inspected)
    }
    if _IDENTITY_LABEL_PATTERN.search(inspected):
        findings.add("explicit_identity_label")
    return frozenset(findings)


def authorize_text_payload(payload: Mapping[str, object]) -> AuthorizedTextPayload:
    """Validate and freeze the exact text payload immediately before egress."""
    context = assert_ai_egress_allowed(TEXT)
    limits = _TEXT_PAYLOAD_LIMITS.get(context.purpose)
    if limits is None:
        raise AIPayloadDenied(
            f"Purpose {context.purpose} has no registered text payload contract"
        )
    if not isinstance(payload, Mapping):
        raise AIPayloadDenied("Text payload must be a mapping")

    fields = frozenset(payload.keys())
    unknown = fields - _TEXT_PAYLOAD_FIELDS
    missing = _TEXT_PAYLOAD_FIELDS - fields
    if unknown:
        raise AIPayloadDenied(f"Unknown text payload fields: {sorted(unknown)}")
    if missing:
        raise AIPayloadDenied(f"Missing text payload fields: {sorted(missing)}")

    from core.phi_privacy import current_patient_identity, redact_identity_values

    patient_identity = current_patient_identity()
    authorized: dict[str, str] = {}
    for field_name in sorted(_TEXT_PAYLOAD_FIELDS):
        value = payload[field_name]
        if not isinstance(value, str):
            raise AIPayloadDenied(f"Text payload field {field_name} must be a string")
        if "\x00" in value:
            raise AIPayloadDenied(f"Text payload field {field_name} contains a NUL byte")
        if len(value) > limits[field_name]:
            raise AIPayloadDenied(
                f"Text payload field {field_name} exceeds the {limits[field_name]} character limit "
                f"for purpose {context.purpose}"
            )

        findings = set(_detect_sensitive_text(value))
        inspected = _mask_allowed_placeholders(_normalise_for_dlp(value))
        if redact_identity_values(inspected, patient_identity) != inspected:
            findings.add("current_patient_identity")
        if findings:
            logger.warning(
                "ai_text_payload denied patient_id=%s purpose=%s field=%s findings=%s",
                context.patient_id,
                context.purpose,
                field_name,
                sorted(findings),
            )
            raise AIPayloadDenied(
                f"Text payload field {field_name} contains prohibited identifiers: "
                f"{sorted(findings)}"
            )
        authorized[field_name] = value

    logger.debug(
        "ai_text_payload authorized patient_id=%s purpose=%s system_chars=%s user_chars=%s",
        context.patient_id,
        context.purpose,
        len(authorized["system_prompt"]),
        len(authorized["user_prompt"]),
    )
    return AuthorizedTextPayload(
        purpose=context.purpose,
        fields=MappingProxyType(authorized),
    )


def _resolved_signature(func: Callable) -> inspect.Signature:
    signature = inspect.signature(func)
    try:
        hints = get_type_hints(func, include_extras=True)
    except (NameError, TypeError):
        return signature

    parameters = [
        parameter.replace(annotation=hints.get(name, parameter.annotation))
        for name, parameter in signature.parameters.items()
    ]
    return signature.replace(
        parameters=parameters,
        return_annotation=hints.get("return", signature.return_annotation),
    )


def patient_ai_egress_scope(
    purpose: str,
    *modalities: str,
) -> Callable:
    """Decorator for authenticated Ninja endpoints that may invoke external AI."""
    modality_set = frozenset(modalities)
    _validate_scope(purpose, modality_set)

    def decorator(func: Callable) -> Callable:
        resolved_signature = _resolved_signature(func)

        @wraps(func)
        def wrapped(request, *args, **kwargs):
            user = getattr(request, "user", None) or getattr(request, "auth", None)
            patient_id = getattr(user, "id", None)
            with ai_egress_scope(patient_id, purpose, *modalities):
                return func(request, *args, **kwargs)

        wrapped.__signature__ = resolved_signature
        wrapped.__annotations__ = {
            name: parameter.annotation
            for name, parameter in resolved_signature.parameters.items()
            if parameter.annotation is not inspect.Parameter.empty
        }
        if resolved_signature.return_annotation is not inspect.Signature.empty:
            wrapped.__annotations__["return"] = resolved_signature.return_annotation
        return wrapped

    return decorator
