"""Default-off runtime seam for the frozen Intent Envelope V1.

This module never constructs a network provider. The authenticated runtime must
receive an explicitly governed provider from its caller. Enabling the feature
without a provider therefore fails closed through the frozen pipeline.
"""
from __future__ import annotations

import os

from companion.intent_pipeline import IntentPipelineOutcome, analyze_unresolved_turn
from core.ai_egress import (
    TEXT,
    AIEgressDenied,
    ai_egress_scope,
    authorize_text_payload,
)
from core.ai_processor_policy import AIProcessorPolicyDenied, authorize_processor_policy
from llm.base import BaseLLMProvider

_RUNTIME_FLAG = "IAMINA_INTENT_ENVELOPE_RUNTIME_ENABLED"


class _RuntimePayloadGuard:
    """Apply patient consent + payload DLP immediately before external egress."""

    def __init__(self, provider: BaseLLMProvider):
        self._provider = provider

    def __getattr__(self, name: str):
        attribute = getattr(self._provider, name)
        if name not in {"complete", "complete_json_schema"} or not callable(attribute):
            return attribute

        def guarded(system: str, user: str, *args, **kwargs):
            payload = authorize_text_payload(
                {"system_prompt": system, "user_prompt": user}
            )
            return attribute(
                payload.system_prompt,
                payload.user_prompt,
                *args,
                **kwargs,
            )

        return guarded


def intent_runtime_enabled() -> bool:
    value = os.environ.get(_RUNTIME_FLAG, "").strip().lower()
    return value in {"1", "true", "yes"}


def analyze_runtime_turn(
    message: str,
    language: str,
    *,
    provider: BaseLLMProvider | None,
    patient_id: int | None = None,
) -> IntentPipelineOutcome | None:
    """Return a frozen-V1 decision only when every runtime gate is satisfied."""

    if not intent_runtime_enabled():
        return None
    if provider is None:
        return analyze_unresolved_turn(
            message,
            language,
            provider=None,
        )

    policy_key = getattr(provider, "processor_policy_key", "")
    if not isinstance(policy_key, str) or not policy_key.strip():
        return analyze_unresolved_turn(
            message,
            language,
            provider=None,
        )
    try:
        processor_policy = authorize_processor_policy(
            policy_key,
            "intent_classification",
            TEXT,
        )
    except AIProcessorPolicyDenied:
        return analyze_unresolved_turn(
            message,
            language,
            provider=None,
        )

    if not processor_policy.external_egress:
        return analyze_unresolved_turn(
            message,
            language,
            provider=provider,
        )

    if patient_id is None:
        return analyze_unresolved_turn(
            message,
            language,
            provider=None,
        )

    try:
        with ai_egress_scope(patient_id, "intent_classification", TEXT):
            return analyze_unresolved_turn(
                message,
                language,
                provider=_RuntimePayloadGuard(provider),
            )
    except AIEgressDenied:
        return analyze_unresolved_turn(
            message,
            language,
            provider=None,
        )


def clarify_reply(language: str, *, prefer_latin_script: bool = False) -> str:
    if language == "en":
        return (
            "I’m not fully sure what you want yet. Do you want me to retrieve a "
            "recorded item, explain something generally, or just chat?"
        )
    if language == "ar-MA" and prefer_latin_script:
        return (
            "Mazal ma fhemtch bddabt chno bghiti. Bghiti nqleb 3la data msjla, "
            "nchra7 lik chi haja b sifa 3amma, wela ghir nhdro?"
        )
    if language in {"ar", "ar-MA", "ar-SA", "ar-AE", "ar-KW", "ar-QA", "ar-OM"}:
        return (
            "لست متأكدًا تمامًا مما تريده. هل تريد استرجاع معلومة مسجلة، "
            "شرحًا عامًا، أم مجرد محادثة؟"
        )
    return (
        "Je ne suis pas encore certain de ce que tu veux. Tu veux que je retrouve "
        "une donnée enregistrée, que je t’explique quelque chose en général, "
        "ou simplement discuter ?"
    )


__all__ = ["analyze_runtime_turn", "clarify_reply", "intent_runtime_enabled"]
