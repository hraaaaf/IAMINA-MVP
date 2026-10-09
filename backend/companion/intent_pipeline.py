"""Candidate companion intent pipeline orchestration.

This module is intentionally not wired into production chat yet. It proves the
ordering and fail-closed behavior before the architecture is frozen.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from companion.intent_envelope import (
    BackendIntentDecision,
    IntentEnvelope,
    IntentTarget,
    RouteKind,
    decide_backend_route,
)
from companion.intent_model import IntentModelUnavailable, IntentPayloadDenied, classify_intent
from core.input_safety import INSULIN_BLOCK, PRESCRIPTION_BLOCK, URGENT, evaluate_input_safety
from llm.base import BaseLLMProvider


@dataclass(frozen=True, slots=True)
class IntentPipelineOutcome:
    decision: BackendIntentDecision
    envelope: IntentEnvelope | None
    source: str
    fallback_copy_key: str


def _clarify(reason: str) -> IntentPipelineOutcome:
    return IntentPipelineOutcome(
        decision=BackendIntentDecision(
            route=RouteKind.CLARIFY,
            target=IntentTarget.NONE,
            reason=reason,
        ),
        envelope=None,
        source="local_fail_closed",
        fallback_copy_key="intent_clarify",
    )


def analyze_unresolved_turn(
    message: str,
    language: str = "fr",
    *,
    provider: BaseLLMProvider | None = None,
    classifier: Callable[..., IntentEnvelope] = classify_intent,
) -> IntentPipelineOutcome:
    """Run safety first, then bounded intent classification, then backend routing.

    The caller is expected to run existing deterministic fast paths before this
    function. This function is for previously unresolved turns only.
    """

    text = (message or "").strip()
    if not text:
        return _clarify("empty_message")

    safety = evaluate_input_safety(text, language)
    if safety.action in {URGENT, INSULIN_BLOCK, PRESCRIPTION_BLOCK}:
        return IntentPipelineOutcome(
            decision=BackendIntentDecision(
                route=RouteKind.SAFETY_LOCAL,
                target=IntentTarget.NONE,
                reason=f"input_safety:{safety.action}",
            ),
            envelope=None,
            source="input_safety",
            fallback_copy_key="safety_authority",
        )

    try:
        envelope = classifier(text, language, provider=provider)
    except (IntentModelUnavailable, IntentPayloadDenied, ValueError):
        return _clarify("intent_classifier_unavailable_or_rejected")

    decision = decide_backend_route(envelope)
    return IntentPipelineOutcome(
        decision=decision,
        envelope=envelope,
        source="intent_envelope_v1",
        fallback_copy_key=(
            "intent_clarify" if decision.route is RouteKind.CLARIFY else ""
        ),
    )
