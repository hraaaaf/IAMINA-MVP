"""Fail-closed provider candidate generator for protected narration shadow.

This module may only send locale/script plus an opaque body token. It never sends
patient text, deterministic clinical copy, facts, history, or AdviceDecision data.
The feature is OFF by default and processor policy is checked before a provider
adapter is constructed.
"""
from __future__ import annotations

from dataclasses import dataclass
import re

from django.conf import settings

from companion.protected_shadow_telemetry import record_protected_narration_shadow
from core.ai_processor_policy import (
    AIProcessorPolicyDenied,
    FORBIDDEN,
    authorize_processor_policy,
    get_processor_policy,
)
from core.contracts.narration_envelope import NarrationEnvelope
from llm.provider_registry import build_openai_compatible_provider

_PROVIDER = "groq"
_PURPOSE = "companion_chat"
_MODALITY = "text"
_BODY_TOKEN_RE = re.compile(r"^\{\{NVB_[A-F0-9]{32}\}\}$")
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
    *,
    internal_authorized: bool = False,
) -> str | None:
    """Return a provider wrapper candidate, or None while shadow is disabled.

    Authorization is checked before adapter construction, so an accidental flag
    flip cannot bypass processor policy or create network traffic.
    """
    if not getattr(settings, "NARRATION_PROTECTED_PROVIDER_SHADOW", False):
        record_protected_narration_shadow(status="disabled")
        return None
    if not internal_authorized:
        record_protected_narration_shadow(status="blocked")
        return None

    request = build_protected_provider_shadow_request(envelope)
    internal_live = bool(
        getattr(settings, "NARRATION_PROTECTED_PROVIDER_INTERNAL_LIVE", False)
    )

    try:
        if internal_live:
            policy = get_processor_policy(_PROVIDER)
            if policy.status == FORBIDDEN:
                raise AIProcessorPolicyDenied(
                    "provider is forbidden even for token-only internal live transport"
                )
            if _PURPOSE not in policy.allowed_purposes:
                raise AIProcessorPolicyDenied(
                    "provider does not allow protected wrapper purpose"
                )
            if _MODALITY not in policy.allowed_modalities:
                raise AIProcessorPolicyDenied(
                    "provider does not allow protected wrapper modality"
                )
            if request.locale != envelope.locale.locale:
                raise PermissionError("protected wrapper locale drift")
            if request.script != envelope.locale.script:
                raise PermissionError("protected wrapper script drift")
            if request.protected_body_token != envelope.protected_body_token:
                raise PermissionError("protected wrapper token drift")
            if not _BODY_TOKEN_RE.fullmatch(request.protected_body_token):
                raise PermissionError("protected wrapper token format invalid")
        else:
            authorize_processor_policy(_PROVIDER, _PURPOSE, _MODALITY)
    except Exception:
        record_protected_narration_shadow(status="blocked")
        raise

    try:
        provider = build_openai_compatible_provider(_PROVIDER)
        response = provider.complete_text(_SYSTEM, request.user_prompt())
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
