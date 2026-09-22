from core.contracts.domain_context import DomainContext
from diabetes.services.clinical.activity_decision import resolve_activity_context
from diabetes.services.clinical.engine import DiabetesEngine


def _context(*, activity=True):
    if not activity:
        return DomainContext.empty(language="fr")
    return DomainContext(
        kpi_summary={"avg_glucose": 142.0},
        detected_patterns=["LOW_GLUCOSE_WITH_RECORDED_ACTIVITY"],
        insights=[],
        pivot_text="context:activity explicitly recorded",
        trend={},
        has_sufficient_data=True,
        language="fr",
    )


def test_activity_context_is_descriptive_and_treatment_safe():
    resolution = resolve_activity_context(
        "Est-ce que le sport cause mes baisses de glycémie ?",
        _context(),
        language="fr",
    )

    assert resolution is not None
    assert resolution.decision.rule_id == "diabetes.activity.descriptive_context"
    assert resolution.decision.authority_level.value == "L2"
    assert "infer_activity_causality" in resolution.decision.forbidden_actions
    assert "recommend_compensatory_activity" in resolution.decision.forbidden_actions
    assert "calculate_insulin_dose" in resolution.decision.forbidden_actions
    assert "change_treatment" in resolution.decision.forbidden_actions
    assert resolution.decision.evidence_refs == (
        "rule.pattern.low-with-recorded-activity.v1",
        "rule.personal-response.repetition.v1",
    )
    assert "ne prouve pas" in resolution.reply
    assert "dose d’insuline" in resolution.reply


def test_activity_context_fails_closed_without_explicit_recorded_activity():
    resolution = resolve_activity_context(
        "Quel est l'effet du sport sur ma glycémie ?",
        _context(activity=False),
        language="fr",
    )

    assert resolution is not None
    assert resolution.decision.rule_id == "diabetes.activity.insufficient_data"
    assert resolution.decision.authority_level.value == "L1"
    assert resolution.decision.missing_facts == ("sufficient_recorded_activity_context",)
    assert "change_treatment" in resolution.decision.forbidden_actions


def test_activity_context_does_not_claim_unrelated_activity_question():
    for message in (
        "Quel sport est le plus populaire au Maroc ?",
        "Je veux organiser ma marche de demain.",
        "What exercise equipment should I buy?",
    ):
        assert resolve_activity_context(message, _context(), language="fr") is None


def test_activity_context_supports_english_and_arabic_queries():
    for message, language in (
        ("How does exercise affect my glucose?", "en"),
        ("شنو تأثير الرياضة على السكر؟", "ar-MA"),
    ):
        resolution = resolve_activity_context(message, _context(), language=language)
        assert resolution is not None
        assert resolution.decision.rule_id == "diabetes.activity.descriptive_context"
        assert resolution.decision.language == language


def test_diabetes_engine_keeps_monitoring_precedence_and_then_routes_activity():
    engine = DiabetesEngine()

    monitoring = engine.resolve_advice(
        "Explique ma tendance glycémique cette semaine",
        _context(),
        language="fr",
    )
    activity = engine.resolve_advice(
        "Est-ce que le sport cause mes baisses de glycémie ?",
        _context(),
        language="fr",
    )

    assert monitoring is not None
    assert monitoring.decision.rule_id.startswith("diabetes.monitoring.")
    assert activity is not None
    assert activity.decision.rule_id.startswith("diabetes.activity.")
