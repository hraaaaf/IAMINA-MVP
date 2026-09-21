import pytest

from core.contracts.advice_decision import (
    AdviceAuthorityLevel,
    AdviceDecision,
    AdviceDisposition,
)
from core.narration_verifier import require_verified_actions, verify_observed_actions


def _decision():
    return AdviceDecision(
        intent="food_permission",
        authority_level=AdviceAuthorityLevel.L2_LOW_RISK_PRACTICAL,
        decision=AdviceDisposition.CONSTRAIN,
        rule_id="diabetes.food.permission",
        rule_version="1",
        allowed_actions=("review_portion_and_carbohydrate_context",),
        forbidden_actions=("calculate_insulin_dose", "change_treatment"),
        evidence_refs=("ADA_SOC_2026_SECTION_5",),
    )


def test_allowed_action_passes():
    result = verify_observed_actions(
        _decision(),
        ("review_portion_and_carbohydrate_context",),
    )

    assert result.passed
    assert result.violations == ()


def test_forbidden_action_is_rejected():
    result = verify_observed_actions(
        _decision(),
        ("calculate_insulin_dose",),
    )

    assert not result.passed
    assert result.violations == ("forbidden:calculate_insulin_dose",)


def test_unknown_action_is_rejected():
    result = verify_observed_actions(
        _decision(),
        ("recommend_post_meal_walk",),
    )

    assert not result.passed
    assert result.violations == ("unauthorized:recommend_post_meal_walk",)


def test_malformed_observation_fails_closed():
    result = verify_observed_actions(_decision(), ("",))

    assert not result.passed
    assert result.violations == ("malformed_observed_action",)


def test_require_verified_actions_raises_on_any_violation():
    with pytest.raises(PermissionError, match="exceeds AdviceDecision"):
        require_verified_actions(
            _decision(),
            (
                "review_portion_and_carbohydrate_context",
                "change_treatment",
            ),
        )
