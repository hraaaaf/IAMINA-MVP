"""Progressive clinical validation policy for diabetes advice families."""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from core.contracts.advice_decision import AdviceAuthorityLevel, AdviceDisposition
from core.contracts.advice_resolution import AdviceResolution


class ValidationStatus(StrEnum):
    EXPERIMENTAL = "experimental"
    VALIDATED = "validated"
    DISABLED = "disabled"


_AUTHORITY_ORDER = {
    AdviceAuthorityLevel.L0_CONVERSATION: 0,
    AdviceAuthorityLevel.L1_EDUCATION: 1,
    AdviceAuthorityLevel.L2_LOW_RISK_PRACTICAL: 2,
    AdviceAuthorityLevel.L3_CONTEXTUAL_CLINICAL: 3,
    AdviceAuthorityLevel.L4_PROFESSIONAL_VALIDATION: 4,
    AdviceAuthorityLevel.L5_PROHIBITED: 5,
}


@dataclass(frozen=True, slots=True)
class RuleFamilyValidation:
    prefix: str
    status: ValidationStatus
    max_authority: AdviceAuthorityLevel
    evidence_basis: tuple[str, ...]
    limitation: str


RULE_FAMILY_VALIDATION = (
    RuleFamilyValidation(
        prefix="diabetes.food.",
        status=ValidationStatus.VALIDATED,
        max_authority=AdviceAuthorityLevel.L2_LOW_RISK_PRACTICAL,
        evidence_basis=("evals.food", "ci3", "ci4", "ci5"),
        limitation="validated_for_current_release_governed_scope_not_clinical_efficacy",
    ),
    RuleFamilyValidation(
        prefix="diabetes.monitoring.",
        status=ValidationStatus.VALIDATED,
        max_authority=AdviceAuthorityLevel.L2_LOW_RISK_PRACTICAL,
        evidence_basis=("evals.monitoring", "ci6.monitoring"),
        limitation="descriptive_monitoring_scope_only",
    ),
    RuleFamilyValidation(
        prefix="diabetes.activity.",
        status=ValidationStatus.VALIDATED,
        max_authority=AdviceAuthorityLevel.L2_LOW_RISK_PRACTICAL,
        evidence_basis=("evals.activity", "ci6.activity"),
        limitation="descriptive_activity_context_only",
    ),
    RuleFamilyValidation(
        prefix="diabetes.symptom.",
        status=ValidationStatus.VALIDATED,
        max_authority=AdviceAuthorityLevel.L4_PROFESSIONAL_VALIDATION,
        evidence_basis=("evals.symptom_triage", "ci6.symptom_triage"),
        limitation="professional_validation_only_no_autonomous_treatment_authority",
    ),
    RuleFamilyValidation(
        prefix="diabetes.clinician_prep.",
        status=ValidationStatus.VALIDATED,
        max_authority=AdviceAuthorityLevel.L2_LOW_RISK_PRACTICAL,
        evidence_basis=("evals.clinician_prep", "ci6.clinician_prep"),
        limitation="review_support_only",
    ),
    RuleFamilyValidation(
        prefix="diabetes.longitudinal.",
        status=ValidationStatus.VALIDATED,
        max_authority=AdviceAuthorityLevel.L1_EDUCATION,
        evidence_basis=("ci7",),
        limitation="descriptive_longitudinal_scope_only",
    ),
)


def validation_for_rule(rule_id: str) -> RuleFamilyValidation:
    for item in RULE_FAMILY_VALIDATION:
        if rule_id.startswith(item.prefix):
            return item
    raise PermissionError(f"unregistered clinical validation family: {rule_id}")


def enforce_clinical_validation(resolution: AdviceResolution) -> AdviceResolution:
    """Fail closed if a runtime family is disabled/unregistered or exceeds proven scope."""
    if not isinstance(resolution, AdviceResolution):
        raise TypeError("resolution must be an AdviceResolution")

    policy = validation_for_rule(resolution.decision.rule_id)
    if policy.status is ValidationStatus.DISABLED:
        raise PermissionError(
            f"clinical rule family disabled: {resolution.decision.rule_id}"
        )

    if resolution.decision.decision in {
        AdviceDisposition.ALLOW,
        AdviceDisposition.CONSTRAIN,
    }:
        actual = _AUTHORITY_ORDER[resolution.decision.authority_level]
        maximum = _AUTHORITY_ORDER[policy.max_authority]
        if actual > maximum:
            raise PermissionError(
                f"clinical authority exceeds validated scope for {resolution.decision.rule_id}"
            )

        if (
            policy.status is ValidationStatus.EXPERIMENTAL
            and actual > _AUTHORITY_ORDER[AdviceAuthorityLevel.L1_EDUCATION]
        ):
            raise PermissionError(
                f"experimental clinical family cannot exceed L1: {resolution.decision.rule_id}"
            )

    return resolution


__all__ = [
    "RULE_FAMILY_VALIDATION",
    "RuleFamilyValidation",
    "ValidationStatus",
    "enforce_clinical_validation",
    "validation_for_rule",
]
