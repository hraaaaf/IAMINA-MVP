from unittest.mock import patch

import pytest

from core.contracts.advice_decision import (
    AdviceAuthorityLevel,
    AdviceDecision,
    AdviceDisposition,
)
from core.contracts.advice_resolution import AdviceResolution
from diabetes.services.clinical.clinical_validation import (
    RULE_FAMILY_VALIDATION,
    RuleFamilyValidation,
    ValidationStatus,
    enforce_clinical_validation,
)


def _resolution(
    *,
    rule_id: str,
    level: AdviceAuthorityLevel,
    disposition: AdviceDisposition = AdviceDisposition.CONSTRAIN,
) -> AdviceResolution:
    escalation = (
        "professional_validation"
        if disposition is AdviceDisposition.ESCALATE
        else None
    )
    return AdviceResolution(
        decision=AdviceDecision(
            intent="ci10_test",
            authority_level=level,
            decision=disposition,
            rule_id=rule_id,
            rule_version="1",
            allowed_actions=(
                ("bounded_action",)
                if disposition in {AdviceDisposition.ALLOW, AdviceDisposition.CONSTRAIN}
                else ()
            ),
            forbidden_actions=("change_treatment",),
            evidence_refs=(
                ("rule.test.v1",)
                if level
                in {
                    AdviceAuthorityLevel.L2_LOW_RISK_PRACTICAL,
                    AdviceAuthorityLevel.L3_CONTEXTUAL_CLINICAL,
                }
                else ()
            ),
            escalation=escalation,
        ),
        reply="Réponse déterministe.",
    )


def test_all_current_runtime_families_have_explicit_validation_policy():
    prefixes = {item.prefix for item in RULE_FAMILY_VALIDATION}
    assert prefixes == {
        "diabetes.food.",
        "diabetes.monitoring.",
        "diabetes.activity.",
        "diabetes.symptom.",
        "diabetes.clinician_prep.",
        "diabetes.longitudinal.",
    }


def test_validated_l2_food_scope_passes():
    resolution = _resolution(
        rule_id="diabetes.food.permission",
        level=AdviceAuthorityLevel.L2_LOW_RISK_PRACTICAL,
    )
    assert enforce_clinical_validation(resolution) is resolution


def test_longitudinal_cannot_be_raised_above_certified_l1():
    resolution = _resolution(
        rule_id="diabetes.longitudinal.descriptive_personalization",
        level=AdviceAuthorityLevel.L2_LOW_RISK_PRACTICAL,
    )
    with pytest.raises(PermissionError, match="exceeds validated scope"):
        enforce_clinical_validation(resolution)


def test_unregistered_family_fails_closed():
    resolution = _resolution(
        rule_id="diabetes.unknown.rule",
        level=AdviceAuthorityLevel.L1_EDUCATION,
    )
    with pytest.raises(PermissionError, match="unregistered clinical validation family"):
        enforce_clinical_validation(resolution)


def test_disabled_family_fails_closed():
    disabled = (
        RuleFamilyValidation(
            prefix="diabetes.food.",
            status=ValidationStatus.DISABLED,
            max_authority=AdviceAuthorityLevel.L2_LOW_RISK_PRACTICAL,
            evidence_basis=("test",),
            limitation="disabled_for_test",
        ),
    )
    resolution = _resolution(
        rule_id="diabetes.food.permission",
        level=AdviceAuthorityLevel.L1_EDUCATION,
    )
    with patch(
        "diabetes.services.clinical.clinical_validation.RULE_FAMILY_VALIDATION",
        disabled,
    ):
        with pytest.raises(PermissionError, match="clinical rule family disabled"):
            enforce_clinical_validation(resolution)


def test_experimental_family_cannot_exceed_l1():
    experimental = (
        RuleFamilyValidation(
            prefix="diabetes.food.",
            status=ValidationStatus.EXPERIMENTAL,
            max_authority=AdviceAuthorityLevel.L2_LOW_RISK_PRACTICAL,
            evidence_basis=("test",),
            limitation="experimental_for_test",
        ),
    )
    resolution = _resolution(
        rule_id="diabetes.food.permission",
        level=AdviceAuthorityLevel.L2_LOW_RISK_PRACTICAL,
    )
    with patch(
        "diabetes.services.clinical.clinical_validation.RULE_FAMILY_VALIDATION",
        experimental,
    ):
        with pytest.raises(PermissionError, match="experimental clinical family"):
            enforce_clinical_validation(resolution)


def test_l4_symptom_escalation_remains_human_gated_and_passes():
    resolution = _resolution(
        rule_id="diabetes.symptom.professional_triage",
        level=AdviceAuthorityLevel.L4_PROFESSIONAL_VALIDATION,
        disposition=AdviceDisposition.ESCALATE,
    )
    assert enforce_clinical_validation(resolution) is resolution



def test_l3_is_blocked_without_dedicated_clinical_validation():
    l3_policy = (
        RuleFamilyValidation(
            prefix="diabetes.food.",
            status=ValidationStatus.VALIDATED,
            max_authority=AdviceAuthorityLevel.L3_CONTEXTUAL_CLINICAL,
            evidence_basis=("software_evals_only",),
            limitation="test",
        ),
    )
    resolution = _resolution(
        rule_id="diabetes.food.contextual",
        level=AdviceAuthorityLevel.L3_CONTEXTUAL_CLINICAL,
    )
    with patch(
        "diabetes.services.clinical.clinical_validation.RULE_FAMILY_VALIDATION",
        l3_policy,
    ):
        with pytest.raises(PermissionError, match="L3 requires dedicated clinical validation"):
            enforce_clinical_validation(resolution)
