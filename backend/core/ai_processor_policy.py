"""Executable processor policy registry for external AI egress.

Policies are immutable, provider-specific and fail closed. Network-capable providers
must be explicitly approved with complete governance metadata before patient data can
leave IAmina. Local/static fallbacks may be approved because they perform no external
egress.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

APPROVED = "approved"
PENDING = "pending"
FORBIDDEN = "forbidden"


class AIProcessorPolicyDenied(PermissionError):
    """Raised when a provider has no complete approved processor policy."""


@dataclass(frozen=True)
class AIProcessorPolicy:
    provider: str
    processor: str
    subprocessors: tuple[str, ...]
    processing_regions: tuple[str, ...]
    data_residency: str
    retention_policy: str
    max_retention_days: int
    training_use: str
    legal_basis: str
    allowed_modalities: frozenset[str]
    allowed_purposes: frozenset[str]
    status: str
    external_egress: bool = True

    def validate(self) -> None:
        if self.status not in {APPROVED, PENDING, FORBIDDEN}:
            raise AIProcessorPolicyDenied(
                f"Provider {self.provider} has an invalid policy status"
            )
        if not self.processor.strip():
            raise AIProcessorPolicyDenied(
                f"Provider {self.provider} has no declared processor"
            )
        if not self.allowed_modalities or not self.allowed_purposes:
            raise AIProcessorPolicyDenied(
                f"Provider {self.provider} has an incomplete purpose/modality policy"
            )
        if self.external_egress:
            required_text = {
                "data_residency": self.data_residency,
                "retention_policy": self.retention_policy,
                "training_use": self.training_use,
                "legal_basis": self.legal_basis,
            }
            missing = sorted(
                name for name, value in required_text.items() if not value.strip()
            )
            if missing:
                raise AIProcessorPolicyDenied(
                    f"Provider {self.provider} is missing governance metadata: {missing}"
                )
            if not self.processing_regions:
                raise AIProcessorPolicyDenied(
                    f"Provider {self.provider} has no declared processing region"
                )
            if self.max_retention_days < 0:
                raise AIProcessorPolicyDenied(
                    f"Provider {self.provider} has an invalid retention duration"
                )


_ALL_TEXT_PURPOSES = frozenset(
    {
        "clinical_summary",
        "doctor_brief",
        "companion_chat",
        "voice_chat",
        "document_ingest",
    }
)

# Network providers remain PENDING until contractual and deployment-specific facts
# are approved. This deliberately prevents configuration alone from enabling egress.
_POLICIES: Mapping[str, AIProcessorPolicy] = MappingProxyType(
    {
        "gemini": AIProcessorPolicy(
            provider="gemini",
            processor="Google",
            subprocessors=(),
            processing_regions=(),
            data_residency="",
            retention_policy="",
            max_retention_days=0,
            training_use="",
            legal_basis="",
            allowed_modalities=frozenset({"text", "audio", "image"}),
            allowed_purposes=_ALL_TEXT_PURPOSES
            | frozenset({"voice_transcription", "meal_vision", "glucometer_ocr"}),
            status=PENDING,
        ),
        "kimi": AIProcessorPolicy(
            provider="kimi",
            processor="Kimi endpoint operator",
            subprocessors=(),
            processing_regions=(),
            data_residency="",
            retention_policy="",
            max_retention_days=0,
            training_use="",
            legal_basis="",
            allowed_modalities=frozenset({"text"}),
            allowed_purposes=_ALL_TEXT_PURPOSES,
            status=PENDING,
        ),
        "claude": AIProcessorPolicy(
            provider="claude",
            processor="Anthropic",
            subprocessors=(),
            processing_regions=(),
            data_residency="",
            retention_policy="",
            max_retention_days=0,
            training_use="",
            legal_basis="",
            allowed_modalities=frozenset({"text"}),
            allowed_purposes=_ALL_TEXT_PURPOSES,
            status=PENDING,
        ),
        "deepseek": AIProcessorPolicy(
            provider="deepseek",
            processor="DeepSeek endpoint operator",
            subprocessors=(),
            processing_regions=(),
            data_residency="",
            retention_policy="",
            max_retention_days=0,
            training_use="",
            legal_basis="",
            allowed_modalities=frozenset({"text"}),
            allowed_purposes=_ALL_TEXT_PURPOSES,
            status=PENDING,
        ),
        "qwen": AIProcessorPolicy(
            provider="qwen",
            processor="Qwen endpoint operator",
            subprocessors=(),
            processing_regions=(),
            data_residency="",
            retention_policy="",
            max_retention_days=0,
            training_use="",
            legal_basis="",
            allowed_modalities=frozenset({"text"}),
            allowed_purposes=_ALL_TEXT_PURPOSES,
            status=PENDING,
        ),
        "groq": AIProcessorPolicy(
            provider="groq",
            processor="Groq, Inc.",
            subprocessors=(),
            processing_regions=("United States",),
            data_residency="US GCP when retained per provider documentation",
            retention_policy="up to 30 days unless IAMINA account-level ZDR is verified",
            max_retention_days=30,
            training_use="not used for training unless explicitly permitted by customer",
            legal_basis="",
            allowed_modalities=frozenset({"text"}),
            allowed_purposes=_ALL_TEXT_PURPOSES,
            status=PENDING,
        ),
        "fallback": AIProcessorPolicy(
            provider="fallback",
            processor="IAmina local runtime",
            subprocessors=(),
            processing_regions=("local",),
            data_residency="local-only",
            retention_policy="no external transfer",
            max_retention_days=0,
            training_use="none",
            legal_basis="not applicable: no external processing",
            allowed_modalities=frozenset({"text"}),
            allowed_purposes=_ALL_TEXT_PURPOSES,
            status=APPROVED,
            external_egress=False,
        ),
        "quota-exhausted": AIProcessorPolicy(
            provider="quota-exhausted",
            processor="IAmina local runtime",
            subprocessors=(),
            processing_regions=("local",),
            data_residency="local-only",
            retention_policy="no external transfer",
            max_retention_days=0,
            training_use="none",
            legal_basis="not applicable: no external processing",
            allowed_modalities=frozenset({"text"}),
            allowed_purposes=_ALL_TEXT_PURPOSES,
            status=APPROVED,
            external_egress=False,
        ),
    }
)


def get_processor_policy(provider: str) -> AIProcessorPolicy:
    policy = _POLICIES.get(provider)
    if policy is None:
        raise AIProcessorPolicyDenied(f"Unknown AI processor policy: {provider}")
    return policy


def authorize_processor_policy(
    provider: str,
    purpose: str,
    modality: str,
) -> AIProcessorPolicy:
    policy = get_processor_policy(provider)
    if policy.status != APPROVED:
        raise AIProcessorPolicyDenied(
            f"Provider {provider} is not approved for patient-data egress"
        )
    policy.validate()
    if purpose not in policy.allowed_purposes:
        raise AIProcessorPolicyDenied(
            f"Provider {provider} is not approved for purpose {purpose}"
        )
    if modality not in policy.allowed_modalities:
        raise AIProcessorPolicyDenied(
            f"Provider {provider} is not approved for modality {modality}"
        )
    return policy


def registered_processor_policies() -> Mapping[str, AIProcessorPolicy]:
    return _POLICIES
