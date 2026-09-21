from core.clinical_policy import (
    NarrationMode,
    NarrationPolicyRequest,
    authorize_narration,
    clinical_context_authorized,
    narration_authorized,
    narration_policy_block,
    policy_denied_reply,
)
from core.contracts.advice_decision import AdviceAuthorityLevel, AdviceDisposition


def _request(**overrides):
    values = {
        "mode": NarrationMode.PRACTICAL,
        "language": "fr",
        "has_approved_context": False,
        "has_sufficient_data": False,
        "analysis_status": "complete",
    }
    values.update(overrides)
    return NarrationPolicyRequest(**values)


def test_plain_conversation_never_receives_clinical_action_authority():
    decision = authorize_narration(_request())

    assert decision.authority_level is AdviceAuthorityLevel.L0_CONVERSATION
    assert decision.decision is AdviceDisposition.CONSTRAIN
    assert "patient_facing_clinical_action" in decision.forbidden_actions
    assert narration_authorized(decision)


def test_approved_context_is_l1_descriptive_only():
    decision = authorize_narration(
        _request(has_approved_context=True, has_sufficient_data=True)
    )

    assert decision.authority_level is AdviceAuthorityLevel.L1_EDUCATION
    assert decision.allowed_actions == ("explain_approved_data",)
    assert "no_new_clinical_action" in decision.limitations


def test_recap_can_only_summarize_and_explain_approved_context():
    decision = authorize_narration(
        _request(
            mode=NarrationMode.RECAP,
            has_approved_context=True,
            has_sufficient_data=True,
        )
    )

    assert set(decision.allowed_actions) == {
        "summarize_approved_data",
        "explain_approved_data",
    }
    assert decision.authority_level is AdviceAuthorityLevel.L1_EDUCATION


def test_clinician_prep_cannot_select_treatment():
    decision = authorize_narration(_request(mode=NarrationMode.CLINICIAN_PREP))

    assert decision.allowed_actions == ("prepare_clinician_questions",)
    assert "change_treatment" in decision.forbidden_actions
    assert "no_treatment_selection" in decision.limitations


def test_degraded_analysis_fails_closed_before_narration():
    decision = authorize_narration(
        _request(
            has_approved_context=True,
            has_sufficient_data=True,
            analysis_status="partial",
        )
    )

    assert decision.authority_level is AdviceAuthorityLevel.L5_PROHIBITED
    assert decision.decision is AdviceDisposition.REFUSE
    assert not narration_authorized(decision)


def test_policy_block_contains_versioned_authority_without_patient_data():
    decision = authorize_narration(
        _request(has_approved_context=True, has_sufficient_data=True)
    )
    block = narration_policy_block(decision)

    assert "L1" in block
    assert "core.narration.approved_context@1" in block
    assert "explain_approved_data" in block
    assert "patient_facing_clinical_action" in block


def test_emotional_l0_stays_available_when_clinical_analysis_is_degraded():
    decision = authorize_narration(
        _request(
            mode=NarrationMode.EMOTIONAL,
            analysis_status="partial",
            has_approved_context=True,
            has_sufficient_data=True,
        )
    )

    assert decision.authority_level is AdviceAuthorityLevel.L0_CONVERSATION
    assert narration_authorized(decision)


def test_degraded_analysis_without_approved_context_stays_l0_not_clinical():
    decision = authorize_narration(
        _request(
            analysis_status="unavailable",
            has_approved_context=False,
            has_sufficient_data=False,
        )
    )

    assert decision.authority_level is AdviceAuthorityLevel.L0_CONVERSATION
    assert narration_authorized(decision)


def test_clinician_prep_does_not_authorize_patient_clinical_context():
    decision = authorize_narration(_request(mode=NarrationMode.CLINICIAN_PREP))
    assert not clinical_context_authorized(decision)


def test_approved_data_explanation_explicitly_authorizes_clinical_context():
    decision = authorize_narration(
        _request(has_approved_context=True, has_sufficient_data=True)
    )
    assert clinical_context_authorized(decision)


def test_policy_denied_copy_is_condition_agnostic():
    assert "évaluation" in policy_denied_reply("fr")
    assert "evaluation" in policy_denied_reply("en").lower()
    assert "البيانات" not in policy_denied_reply("ar")
