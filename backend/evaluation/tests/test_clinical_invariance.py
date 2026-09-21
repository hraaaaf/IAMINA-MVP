import pytest

from evaluation.clinical_invariance import (
    ClinicalDecisionSnapshot,
    compare_clinical_decisions,
    require_hard_invariance,
)


def _snapshot(**overrides):
    values = {
        "intent": "food_permission",
        "authority_level": "L2",
        "decision": "constrain",
        "allowed_actions": ["request_food_label_or_portion"],
        "forbidden_actions": ["calculate_insulin_dose"],
        "rule_id": "diabetes.food.permission",
        "rule_version": "1",
        "language": "fr",
    }
    values.update(overrides)
    return ClinicalDecisionSnapshot.from_mapping(values)


def test_equivalent_paraphrases_keep_same_clinical_decision():
    baseline = _snapshot()
    candidate = _snapshot(language="en")

    result = compare_clinical_decisions(baseline, candidate)

    assert result.passed
    assert result.mismatches == ()


def test_authority_or_action_drift_is_hard_failure():
    baseline = _snapshot()
    candidate = _snapshot(
        authority_level="L3",
        allowed_actions=["request_food_label_or_portion", "change_treatment"],
    )

    result = compare_clinical_decisions(baseline, candidate)

    assert not result.passed
    assert set(result.mismatches) == {"authority_level", "allowed_actions"}


def test_rule_version_drift_is_visible():
    result = compare_clinical_decisions(_snapshot(), _snapshot(rule_version="2"))

    assert not result.passed
    assert result.mismatches == ("rule_version",)


def test_hard_gate_requires_every_candidate_to_match():
    baseline = _snapshot()
    with pytest.raises(AssertionError, match="clinical decision drift"):
        require_hard_invariance(
            baseline,
            (
                _snapshot(language="en"),
                _snapshot(decision="allow"),
            ),
        )


def test_mapping_rejects_malformed_action_collection():
    with pytest.raises(ValueError, match="allowed_actions"):
        ClinicalDecisionSnapshot.from_mapping(
            {
                "intent": "food_permission",
                "authority_level": "L2",
                "decision": "constrain",
                "allowed_actions": "request_food_label_or_portion",
                "forbidden_actions": [],
                "rule_id": "diabetes.food.permission",
                "rule_version": "1",
                "language": "fr",
            }
        )
