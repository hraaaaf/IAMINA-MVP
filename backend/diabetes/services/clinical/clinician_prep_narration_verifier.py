"""Strict narration verifier for CLINICIAN_PREP V1.

The certified consultation brief permits narration, but CI-6 keeps the first
patient-facing rule family stricter: only the deterministic copy generated from
the approved structured envelope is accepted. Any altered candidate falls back
to that exact copy, preventing invented patient facts or clinical conclusions.
"""
from __future__ import annotations

from dataclasses import dataclass

from core.contracts.advice_decision import AdviceDecision


@dataclass(frozen=True, slots=True)
class ClinicianPrepNarrationVerification:
    passed: bool
    violations: tuple[str, ...]


def verify_clinician_prep_narration(
    decision: AdviceDecision,
    candidate: str,
    fallback: str,
) -> ClinicianPrepNarrationVerification:
    if not decision.rule_id.startswith("diabetes.clinician_prep."):
        return ClinicianPrepNarrationVerification(False, ("wrong_rule_family",))
    if not isinstance(candidate, str) or not candidate.strip():
        return ClinicianPrepNarrationVerification(False, ("malformed_narration",))
    if candidate.strip() != fallback.strip():
        return ClinicianPrepNarrationVerification(
            False,
            ("altered_structured_brief_narration_not_authorized_v1",),
        )
    return ClinicianPrepNarrationVerification(True, ())


def verified_clinician_prep_narration_or_fallback(
    decision: AdviceDecision,
    candidate: str,
    fallback: str,
) -> str:
    fallback_check = verify_clinician_prep_narration(decision, fallback, fallback)
    if not fallback_check.passed:
        raise PermissionError(
            "deterministic CLINICIAN_PREP fallback failed verification: "
            + ", ".join(fallback_check.violations)
        )
    candidate_check = verify_clinician_prep_narration(decision, candidate, fallback)
    return candidate.strip() if candidate_check.passed else fallback.strip()


__all__ = [
    "ClinicianPrepNarrationVerification",
    "verified_clinician_prep_narration_or_fallback",
    "verify_clinician_prep_narration",
]
