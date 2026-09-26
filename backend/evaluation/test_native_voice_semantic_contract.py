from evaluation.native_voice_batched_benchmark import APPROVED_SEMANTICS, _scenario_prompt
from evaluation.native_voice_shadow_benchmark import SCENARIOS


def test_governed_clinical_turn_has_explicit_approved_semantics():
    contract = APPROVED_SEMANTICS["governed_clinical"]

    assert contract["speech_act"] == "EXPLAIN_APPROVED_DATA"
    assert contract["required_claims"]
    assert "Any additional clinical finding" in contract["forbidden_claims"]


def test_safety_boundary_forbids_dose_generation():
    contract = APPROVED_SEMANTICS["safety_boundary"]

    assert "Do not provide an insulin dose." in contract["required_claims"]
    assert "A dose amount" in contract["forbidden_claims"]


def test_clinician_prep_forbids_treatment_recommendation():
    contract = APPROVED_SEMANTICS["clinician_prep"]

    assert "Treatment recommendation" in contract["forbidden_claims"]
    assert "Dose change" in contract["forbidden_claims"]


def test_prompt_embeds_contract_on_clinical_turns():
    prompt = _scenario_prompt(SCENARIOS[0])

    assert '"approved_semantic_contract"' in prompt
    assert '"EXPLAIN_APPROVED_DATA"' in prompt
    assert '"RESTORE_AUTHORITY_BOUNDARY"' in prompt
    assert '"PREPARE_CLINICIAN_QUESTIONS"' in prompt
