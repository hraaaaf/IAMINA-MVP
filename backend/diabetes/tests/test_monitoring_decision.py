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


def test_unrelated_message_is_not_claimed_by_monitoring_family():
    assert (
        resolve_monitoring_interpretation(
            "Bonjour, comment vas-tu ?",
            _context(),
            language="fr",
        )
        is None
    )
