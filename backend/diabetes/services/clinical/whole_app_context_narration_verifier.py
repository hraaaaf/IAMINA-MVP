"""Verifier for deterministic whole-app context replies."""

from __future__ import annotations

from core.contracts.advice_decision import AdviceDecision


def verified_whole_app_context_or_fallback(
    decision: AdviceDecision,
    candidate: str,
    fallback: str,
) -> str:
    """Accept only the deterministic resolver copy for patient-owned data reads."""

    if not decision.rule_id.startswith("diabetes.context."):
        return fallback
    if not isinstance(candidate, str) or not candidate.strip():
        return fallback
    return candidate.strip() if candidate.strip() == fallback.strip() else fallback.strip()


__all__ = ["verified_whole_app_context_or_fallback"]
