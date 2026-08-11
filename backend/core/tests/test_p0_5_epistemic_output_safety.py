from core.medical_safety import sanitize_patient_visible


def _unsafe_insight() -> dict:
    return {
        "code": "INTERNAL_DIAGNOSTIC_LABEL",
        "priority": 1,
        "icon": "shield",
        "title": "Confirmed named phenomenon",
        "content": "This proves the mechanism and diagnosis.",
        "action": "Take rapid-acting insulin before the meal.",
    }


def test_structured_insight_preserves_only_stable_metadata():
    insight = sanitize_patient_visible(_unsafe_insight(), "en")

    assert insight["code"] == "INTERNAL_DIAGNOSTIC_LABEL"
    assert insight["priority"] == 1
    assert insight["icon"] == "shield"
    assert insight["title"] == "Observation in your data"
    assert "Confirmed" not in insight["title"]
    assert "mechanism" not in insight["content"]
    assert "insulin" not in insight["action"].lower()


def test_french_observation_envelope_states_evidence_ceiling():
    insight = sanitize_patient_visible(_unsafe_insight(), "fr")

    assert insight["title"] == "Observation dans tes données"
    assert "établir une cause ou un diagnostic" in insight["content"]
    assert "professionnel de santé" in insight["action"]


def test_msa_observation_envelope_is_non_causal_and_non_prescriptive():
    insight = sanitize_patient_visible(_unsafe_insight(), "ar")

    assert insight["title"] == "ملاحظة في بياناتك"
    assert "لا تكفي لإثبات سبب أو تشخيص" in insight["content"]
    assert "جرعة" not in insight["action"]
    assert "أنسولين" not in insight["action"]


def test_darija_observation_envelope_uses_arabic_script_and_evidence_ceiling():
    insight = sanitize_patient_visible(_unsafe_insight(), "ar-MA")

    assert insight["title"] == "ملاحظة فالمعطيات ديالك"
    assert "ما كتكفيش باش نحددو السبب" in insight["content"]
    assert "المختص الصحي" in insight["action"]
    assert "insulin" not in insight["action"].lower()


def test_unrelated_dict_keeps_recursive_no_prescription_behavior():
    value = {"message": "Increase your insulin dose tonight."}

    sanitized = sanitize_patient_visible(value, "en")

    assert "I cannot prescribe treatment" in sanitized["message"]
