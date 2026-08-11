import pytest

from core.contracts.capabilities import (
    Authority,
    Capability,
    assert_capability_allowed,
    capability_allowed,
    rule_for,
)
from core.contracts.truth import TruthKind, TruthRecord
from core.llm_gateway import _assert_generative_capability


def test_model_inference_cannot_be_persisted_or_used_as_clinical_input():
    record = TruthRecord(
        key="possible_food_response",
        value="higher glucose after couscous",
        kind=TruthKind.MODEL_INFERENCE,
        source="companion.llm",
    )

    assert record.may_persist_as_patient_fact is False
    assert record.may_enter_deterministic_clinical_logic is False

    with pytest.raises(ValueError, match="cannot be persisted as a patient fact"):
        record.assert_patient_fact_persistence_allowed()
    with pytest.raises(ValueError, match="cannot enter deterministic clinical decision logic"):
        record.assert_deterministic_clinical_input_allowed()


def test_observed_fact_and_user_claim_keep_distinct_provenance_but_can_feed_deterministic_logic():
    observed = TruthRecord(
        key="glucose_mg_dl",
        value=142,
        kind=TruthKind.OBSERVED_FACT,
        source="journal.log",
    )
    claim = TruthRecord(
        key="reported_fatigue",
        value=True,
        kind=TruthKind.USER_CLAIM,
        source="journal.context",
    )

    assert observed.may_persist_as_patient_fact is True
    assert observed.may_enter_deterministic_clinical_logic is True
    assert claim.may_persist_as_patient_fact is True
    assert claim.may_enter_deterministic_clinical_logic is True

    observed.assert_deterministic_clinical_input_allowed()
    claim.assert_patient_fact_persistence_allowed()
    claim.assert_deterministic_clinical_input_allowed()
    assert claim.kind is TruthKind.USER_CLAIM


def test_deterministic_derivation_can_feed_deterministic_logic_but_is_not_patient_fact():
    derived = TruthRecord(
        key="tir_pct",
        value=68.2,
        kind=TruthKind.DETERMINISTIC_DERIVATION,
        source="diabetes.sql_analytics",
    )

    assert derived.may_enter_deterministic_clinical_logic is True
    assert derived.may_persist_as_patient_fact is False


def test_generative_model_is_limited_to_narration_style_capabilities():
    allowed = {
        Capability.EXPLAIN_APPROVED_DATA,
        Capability.SUMMARIZE_APPROVED_DATA,
        Capability.SURFACE_DETERMINISTIC_PATTERN,
        Capability.PREPARE_CLINICIAN_QUESTIONS,
    }

    for capability in allowed:
        assert capability_allowed(capability, Authority.GENERATIVE_MODEL)

    forbidden = {
        Capability.CLASSIFY_EMERGENCY,
        Capability.DIAGNOSE,
        Capability.PRESCRIBE,
        Capability.CALCULATE_DOSE,
        Capability.OPTIMIZE_TREATMENT,
        Capability.CHANGE_TREATMENT,
        Capability.PROMOTE_MODEL_INFERENCE_TO_FACT,
        Capability.AUTONOMOUS_CLINICAL_RECORD_WRITE,
    }

    for capability in forbidden:
        assert not capability_allowed(capability, Authority.GENERATIVE_MODEL)


def test_emergency_classification_is_deterministic_only():
    rule = rule_for(Capability.CLASSIFY_EMERGENCY)

    assert rule.allowed_authorities == frozenset({Authority.DETERMINISTIC_ENGINE})
    assert_capability_allowed(Capability.CLASSIFY_EMERGENCY, Authority.DETERMINISTIC_ENGINE)

    with pytest.raises(PermissionError):
        assert_capability_allowed(Capability.CLASSIFY_EMERGENCY, Authority.GENERATIVE_MODEL)


def test_diagnosis_prescription_and_treatment_optimization_are_disabled_for_every_authority():
    prohibited = (
        Capability.DIAGNOSE,
        Capability.PRESCRIBE,
        Capability.CALCULATE_DOSE,
        Capability.OPTIMIZE_TREATMENT,
        Capability.CHANGE_TREATMENT,
    )

    for capability in prohibited:
        assert rule_for(capability).allowed_authorities == frozenset()
        for authority in Authority:
            assert not capability_allowed(capability, authority)


def test_user_claim_and_preference_writes_require_confirmation():
    assert rule_for(Capability.RECORD_USER_CLAIM).requires_user_confirmation is True
    assert rule_for(Capability.UPDATE_USER_PREFERENCE).requires_user_confirmation is True


def test_llm_gateway_fails_closed_before_forbidden_capability_egress():
    _assert_generative_capability(Capability.EXPLAIN_APPROVED_DATA)

    with pytest.raises(PermissionError, match="generative_model is not allowed"):
        _assert_generative_capability(Capability.DIAGNOSE)
