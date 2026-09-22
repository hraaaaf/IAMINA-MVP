"""Strict V1 narration verifier for governed longitudinal personalization."""
from __future__ import annotations

from dataclasses import dataclass

from core.contracts.advice_decision import AdviceDecision


@dataclass(frozen=True, slots=True)
class LongitudinalNarrationVerification:
    passed: bool
    violations: tuple[str, ...]


def verify_longitudinal_narration(
    decision: AdviceDecision,
    candidate: str,
    fallback: str,
) -> LongitudinalNarrationVerification:
    if not decision.rule_id.startswith("diabetes.longitudinal."):
        return LongitudinalNarrationVerification(False, ("wrong_rule_family",))
    if not isinstance(candidate, str) or not candidate.strip():
        return LongitudinalNarrationVerification(False, ("malformed_narration",))
    if candidate.strip() != fallback.strip():
        return LongitudinalNarrationVerification(
            False,
            ("altered_longitudinal_narration_not_authorized_v1",),
        )
    return LongitudinalNarrationVerification(True, ())


def verified_longitudinal_narration_or_fallback(
    decision: AdviceDecision,
    candidate: str,
    fallback: str,
) -> str:
    fallback_check = verify_longitudinal_narration(decision, fallback, fallback)
    if not fallback_check.passed:
        raise PermissionError(
            "deterministic longitudinal fallback failed verification: "
            + ", ".join(fallback_check.violations)
        )
    candidate_check = verify_longitudinal_narration(decision, candidate, fallback)
    return candidate.strip() if candidate_check.passed else fallback.strip()


__all__ = [
    "LongitudinalNarrationVerification",
    "verified_longitudinal_narration_or_fallback",
    "verify_longitudinal_narration",
]
