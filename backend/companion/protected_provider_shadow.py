"""Fail-closed provider candidate generator for protected narration shadow.

This module may only send locale/script plus an opaque body token. It never sends
patient text, deterministic clinical copy, facts, history, or AdviceDecision data.
The feature is OFF by default and processor policy is checked before a provider
adapter is constructed.
"""
from __future__ import annotations

from dataclasses import dataclass

from django.conf import settings

from companion.protected_shadow_telemetry import record_protected_narration_shadow
from core.ai_processor_policy import authorize_processor_policy
from core.contracts.narration_envelope import NarrationEnvelope
from llm.provider_registry import build_openai_compatible_provider

_PROVIDER = "groq"
_PURPOSE = "companion_chat"
_MODALITY = "text"
_SYSTEM = (
    "Generate one very short non-clinical relational wrapper around the exact "
    "opaque token. Keep the token unchanged exactly once. Do not add facts, "
    "numbers, health content, advice, questions, actions, diagnosis, treatment, "
    "dose, urgency, or clinical concepts. Return plain text only."
)


@dataclass(frozen=True, slots=True)
class ProtectedProviderShadowRequest:
    locale: str
    script: str
    protected_body_token: str

    def user_prompt(self) -> str:
        return (
            f"locale={self.locale}\n"
            f"script={self.script}\n"
            f"protected_body_token={self.protected_body_token}"
        )


def build_protected_provider_shadow_request(
    envelope: NarrationEnvelope,
) -> ProtectedProviderShadowRequest:
    """Build the only payload shape allowed for provider-backed shadow."""
    return ProtectedProviderShadowRequest(
        locale=envelope.locale.locale,
        script=envelope.locale.script,
        protected_body_token=envelope.protected_body_token,
    )


def generate_protected_provider_shadow_candidate(
    envelope: NarrationEnvelope,
) -> str | None:
    """Return a provider wrapper candidate, or None while shadow is disabled.

    Authorization is checked before adapter construction, so an accidental flag
    flip cannot bypass processor policy or create network traffic.
    """
    if not getattr(settings, "NARRATION_PROTECTED_PROVIDER_SHADOW", False):
        record_protected_narration_shadow(status="disabled")
        return None

    try:
        authorize_processor_policy(_PROVIDER, _PURPOSE, _MODALITY)
    except Exception:
        record_protected_narration_shadow(status="blocked")
        raise

    request = build_protected_provider_shadow_request(envelope)
    try:
        provider = build_openai_compatible_provider(_PROVIDER)
        response = provider.complete(_SYSTEM, request.user_prompt())
    except Exception:
        record_protected_narration_shadow(status="error")
        raise
    if not isinstance(response.content, str) or not response.content.strip():
        record_protected_narration_shadow(status="error")
        raise PermissionError("protected provider shadow returned an empty candidate")
    return response.content.strip()


__all__ = [
    "ProtectedProviderShadowRequest",
    "build_protected_provider_shadow_request",
    "generate_protected_provider_shadow_candidate",
]
