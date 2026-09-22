from core.contracts.domain_context import DomainContext
from core.input_safety import URGENT, evaluate_input_safety
from diabetes.services.clinical.engine import DiabetesEngine
from diabetes.services.clinical.symptom_triage_decision import resolve_symptom_triage


def _context(language="fr"):
    return DomainContext.empty(language=language)


def test_symptom_triage_escalates_without_diagnosis_or_treatment():
    resolution = resolve_symptom_triage(
        "J'ai des nausées et mal au ventre aujourd'hui.",
        _context(),
        language="fr",
    )
    assert resolution is not None
    assert resolution.decision.intent == "symptom_triage"
    assert resolution.decision.authority_level.value == "L4"
    assert resolution.decision.decision.value == "escalate"
    assert resolution.decision.rule_id == "diabetes.symptom.professional_triage"
    assert resolution.decision.escalation == "contact_clinical_team_for_symptom_assessment"
    assert resolution.decision.allowed_actions == ()
    assert "diagnose_from_symptom" in resolution.decision.forbidden_actions
    assert "calculate_insulin_dose" in resolution.decision.forbidden_actions
    assert "change_treatment" in resolution.decision.forbidden_actions


def test_symptom_triage_never_shadows_shared_urgent_gate():
    urgent_messages = (
        "Je suis inconscient.",
        "I am going to faint and my vision is blurred.",
        "عندي دوخة وغادي يغمى عليا",
    )
    for message in urgent_messages:
        assert evaluate_input_safety(message).action == URGENT, message
        assert resolve_symptom_triage(message, _context(), language="fr") is None


def test_symptom_triage_ignores_generic_education_and_non_symptom_requests():
    messages = (
        "Quels sont les symptômes possibles du diabète ?",
        "What are the symptoms of DKA?",
        "Explique-moi mon TIR cette semaine.",
        "Quel sport est populaire au Maroc ?",
    )
    for message in messages:
        assert resolve_symptom_triage(message, _context(), language="fr") is None


def test_symptom_triage_supports_english_and_arabic_current_reports():
    cases = (
        ("I feel nauseous and unwell today.", "en"),
        ("عندي غثيان وانا عيان اليوم", "ar-MA"),
    )
    for message, language in cases:
        resolution = resolve_symptom_triage(message, _context(language), language=language)
        assert resolution is not None
        assert resolution.decision.rule_id == "diabetes.symptom.professional_triage"
        assert resolution.decision.language == language


def test_diabetes_engine_routes_symptom_after_lower_risk_families():
    engine = DiabetesEngine()
    resolution = engine.resolve_advice(
        "J'ai des nausées et mal au ventre aujourd'hui.",
        _context(),
        language="fr",
    )
    assert resolution is not None
    assert resolution.decision.rule_id.startswith("diabetes.symptom.")
