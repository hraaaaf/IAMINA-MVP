"""Controlled registry for OpenAI-compatible text inference candidates.

The registry describes transport/runtime capabilities only. It never grants patient
egress: processor authorization remains a separate fail-closed boundary in
``core.ai_processor_policy`` and pricing remains controlled by ``llm.pricing``.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from .lowcost_openai_compatible import OpenAICompatibleLowCostProvider


@dataclass(frozen=True, slots=True)
class OpenAICompatibleProviderSpec:
    provider_id: str
    settings_prefix: str
    default_endpoint: str
    default_model: str
    capabilities: frozenset[str]
    locale_quality_status: str
    pricing_evidence_reference: str
    timeout_seconds: float
    cache_support: str
    benchmark_evidence: str
    processor_policy_key: str

    def validate(self) -> None:
        required = {
            "provider_id": self.provider_id,
            "settings_prefix": self.settings_prefix,
            "locale_quality_status": self.locale_quality_status,
            "pricing_evidence_reference": self.pricing_evidence_reference,
            "cache_support": self.cache_support,
            "benchmark_evidence": self.benchmark_evidence,
            "processor_policy_key": self.processor_policy_key,
        }
        missing = tuple(name for name, value in required.items() if not value.strip())
        if missing:
            raise ValueError("incomplete provider spec: " + ", ".join(missing))
        if not self.capabilities:
            raise ValueError("provider capabilities are required")
        if self.timeout_seconds <= 0:
            raise ValueError("provider timeout must be positive")


_SPECS: Mapping[str, OpenAICompatibleProviderSpec] = MappingProxyType(
    {
        "deepseek": OpenAICompatibleProviderSpec(
            provider_id="deepseek",
            settings_prefix="DEEPSEEK",
            default_endpoint="",
            default_model="",
            capabilities=frozenset({"text", "streaming", "provider_usage"}),
            locale_quality_status="not-certified",
            pricing_evidence_reference="controlled-pricing-registry-required",
            timeout_seconds=15.0,
            cache_support="provider-dependent",
            benchmark_evidence="no-current-IAMINA-parity-certificate",
            processor_policy_key="deepseek",
        ),
        "qwen": OpenAICompatibleProviderSpec(
            provider_id="qwen",
            settings_prefix="QWEN",
            default_endpoint="",
            default_model="",
            capabilities=frozenset({"text", "streaming", "provider_usage"}),
            locale_quality_status="not-certified",
            pricing_evidence_reference="controlled-pricing-registry-required",
            timeout_seconds=15.0,
            cache_support="provider-dependent",
            benchmark_evidence="no-current-IAMINA-parity-certificate",
            processor_policy_key="qwen",
        ),
        "groq": OpenAICompatibleProviderSpec(
            provider_id="groq",
            settings_prefix="GROQ",
            default_endpoint="https://api.groq.com/openai/v1",
            default_model="openai/gpt-oss-120b",
            capabilities=frozenset({"text", "streaming", "provider_usage"}),
            locale_quality_status="pending-IAMINA-multilingual-parity",
            pricing_evidence_reference="issue-430-groq-evidence-2026-08-20",
            timeout_seconds=15.0,
            cache_support="provider-reported-usage-when-available",
            benchmark_evidence="candidate-only; no patient-egress certificate",
            processor_policy_key="groq",
        ),
    }
)


def get_openai_compatible_provider_spec(provider_id: str) -> OpenAICompatibleProviderSpec:
    spec = _SPECS.get(provider_id)
    if spec is None:
        raise RuntimeError(f"unknown OpenAI-compatible provider: {provider_id}")
    spec.validate()
    return spec


def registered_openai_compatible_provider_specs() -> Mapping[str, OpenAICompatibleProviderSpec]:
    return _SPECS


def build_openai_compatible_provider(
    provider_id: str,
    *,
    model: str | None = None,
) -> OpenAICompatibleLowCostProvider:
    """Build one configured adapter without granting processor authorization."""
    spec = get_openai_compatible_provider_spec(provider_id)
    return OpenAICompatibleLowCostProvider(
        model=model,
        provider_id=spec.provider_id,
        settings_prefix=spec.settings_prefix,
        default_base_url=spec.default_endpoint,
        default_model=spec.default_model,
        timeout_seconds=spec.timeout_seconds,
        processor_policy_key=spec.processor_policy_key,
    )
