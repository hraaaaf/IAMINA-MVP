"""Central authorization boundary for patient data leaving IAmina.

The boundary is deliberately provider-agnostic. It does not choose Gemini,
Claude, Kimi, or any future provider; it only decides whether an external model
operation is authorized for the current patient, purpose, and modality.

Authorization is lazy: entering a scope does not require AI consent. The consent
check happens only when an actual external egress is attempted. This preserves
fully deterministic emergency/safety responses for patients who declined AI.
"""

from __future__ import annotations

import inspect
import logging
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from functools import wraps
from typing import Callable, Iterator, get_type_hints

from core.models import BasePatientProfile

logger = logging.getLogger(__name__)

TEXT = "text"
AUDIO = "audio"
IMAGE = "image"
DOCUMENT = "document"

# Explicit purpose registry. Unknown purposes are denied by construction.
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


class AIEgressDenied(PermissionError):
    """Raised when an external model operation is not policy-authorized."""


class AIConsentRequired(AIEgressDenied):
    """Raised when a patient has not explicitly consented to AI processing."""


@dataclass(frozen=True)
class AIEgressContext:
    patient_id: int
    purpose: str
    modalities: frozenset[str]


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


@contextmanager
def ai_egress_scope(
    patient_id: int,
    purpose: str,
    *modalities: str,
) -> Iterator[AIEgressContext]:
    """Declare the patient/purpose context for a possible external model call.

    No consent check happens here. That check is intentionally deferred to
    :func:`assert_ai_egress_allowed`, immediately before provider/network egress.
    """
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

    logger.debug(
        "ai_egress authorized patient_id=%s purpose=%s modality=%s",
        context.patient_id,
        context.purpose,
        modality,
    )
    return context


def _resolved_signature(func: Callable) -> inspect.Signature:
    """Return a signature with forward annotations resolved in the endpoint module.

    Decorators live in ``core.ai_egress`` while Ninja endpoints may annotate
    parameters with module-local types such as ``UploadedFile``. Without resolving
    those annotations before wrapping, Django Ninja later tries to resolve them in
    this module's globals and OpenAPI generation fails.
    """
    signature = inspect.signature(func)
    try:
        hints = get_type_hints(func, include_extras=True)
    except (NameError, TypeError):
        # A non-Ninja helper may contain an intentionally unresolved annotation.
        # Keep its original signature rather than breaking runtime decoration.
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

        # Django Ninja introspects the decorated callable. Preserve a signature whose
        # annotations are concrete objects, not forward-ref strings tied to func globals.
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
