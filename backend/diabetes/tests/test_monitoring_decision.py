from core.contracts.advice_decision import AdviceAuthorityLevel
from core.contracts.domain_context import DomainContext
from diabetes.services.clinical.monitoring_decision import (
    resolve_monitoring_interpretation,
)


def _context(*, sufficient=True):
    return DomainContext(
        kpi_summary={
            "avg_glucose": 142.0,
            "tir_pct": 68.0,
            "cv_pct": 31.0,
            "tar_pct": 28.0,
            "tbr_pct": 4.0,
        },
        detected_patterns=[],
        insights=[],
        pivot_text="",
        trend={
            "current_week_tir": 68.0,
            "prev_week_tir": 64.0,
            "tir_delta": 4.0,
            "direction": "up",
        },
        has_sufficient_data=sufficient,
        language="fr",
    )


def test_monitoring_interpretation_is_descriptive_and_treatment_safe():
    resolution = resolve_monitoring_interpretation(
        "Est-ce que mon TIR s'améliore cette semaine ?",
        _context(),
        language="fr",
    )

    assert resolution is not None
    assert resolution.decision.rule_id == "diabetes.monitoring.descriptive_interpretation"
    assert resolution.decision.authority_level is AdviceAuthorityLevel.L2_LOW_RISK_PRACTICAL
    assert "compare_descriptive_monitoring_trend" in resolution.decision.allowed_actions
    assert "change_treatment" in resolution.decision.forbidden_actions
    assert "calculate_insulin_dose" in resolution.decision.forbidden_actions
    assert "amélioration" in resolution.reply
    assert "modifier le traitement" in resolution.reply


def test_monitoring_interpretation_fails_closed_when_data_are_insufficient():
    resolution = resolve_monitoring_interpretation(
        "Explique-moi ma tendance glycémique",
        DomainContext.empty(language="fr"),
        language="fr",
    )

    assert resolution is not None
    assert resolution.decision.rule_id == "diabetes.monitoring.insufficient_data"
    assert resolution.decision.authority_level is AdviceAuthorityLevel.L1_EDUCATION
    assert resolution.decision.missing_facts == ("sufficient_monitoring_window",)
    assert "change_treatment" in resolution.decision.forbidden_actions


def test_monitoring_reply_exposes_available_summary_values():
    context = _context()
    context.kpi_summary.update({
        "log_count": 42,
        "days_with_data": 7,
        "gmi": None,
    })

    resolution = resolve_monitoring_interpretation(
        "Explique-moi ma glycémie moyenne et mon TIR.",
        context,
        language="fr",
    )

    assert resolution is not None
    assert "42 mesures sur 7 jours" in resolution.reply
    assert "142 mg/dL" in resolution.reply
    assert "TIR CGM vérifié 68 %" in resolution.reply
    assert "GMI indisponible" in resolution.reply


def test_broad_weekly_personal_diabetes_request_fails_closed_without_data():
    context = DomainContext(
        kpi_summary={
            "log_count": 0,
            "days_with_data": 0,
            "has_sufficient_data": False,
        },
        detected_patterns=[],
        insights=[],
        pivot_text="",
        language="fr",
        has_sufficient_data=False,
        analysis_status="insufficient_data",
    )

    resolution = resolve_monitoring_interpretation(
        "Comment était mon diabète cette semaine ?",
        context,
        language="fr",
    )

    assert resolution is not None
    assert resolution.decision.rule_id == "diabetes.monitoring.insufficient_data"
    assert "aucune glycémie enregistrée" in resolution.reply
    assert "sans inventer" in resolution.reply


def test_broad_weekly_personal_diabetes_request_with_data_uses_approved_narrator():
    resolution = resolve_monitoring_interpretation(
        "Comment était mon diabète cette semaine ?",
        _context(),
        language="fr",
    )

    assert resolution is None


def test_insufficient_monitoring_reply_exposes_known_measurement_coverage():
    context = DomainContext(
        kpi_summary={
            "log_count": 3,
            "days_with_data": 2,
            "has_sufficient_data": False,
        },
        detected_patterns=[],
        insights=[],
        pivot_text="",
        language="fr",
        has_sufficient_data=False,
        analysis_status="insufficient_data",
    )

    resolution = resolve_monitoring_interpretation(
        "Explique-moi ma tendance glycémique cette semaine.",
        context,
        language="fr",
    )

    assert resolution is not None
    assert "3 mesures" in resolution.reply
    assert "2 jours" in resolution.reply


def test_unrelated_message_is_not_claimed_by_monitoring_family():
    for message, language in (
        ("Bonjour, comment vas-tu ?", "fr"),
        ("What is the weather trend this week?", "en"),
        ("Peux-tu relire mon CV cette semaine ?", "fr"),
    ):
        assert (
            resolve_monitoring_interpretation(
                message,
                _context(),
                language=language,
            )
            is None
        )


def test_monitoring_family_supports_english_and_arabic_glucose_trend_queries():
    for message, language in (
        ("Explain my glucose trend this week", "en"),
        ("اشرح لي اتجاه السكر هذا الأسبوع", "ar-MA"),
    ):
        resolution = resolve_monitoring_interpretation(
            message,
            _context(),
            language=language,
        )

        assert resolution is not None
        assert resolution.decision.rule_id == "diabetes.monitoring.descriptive_interpretation"
        assert resolution.decision.language == language
