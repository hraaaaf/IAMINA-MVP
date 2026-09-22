import pytest

from core.contracts.domain_context import DomainContext
from diabetes.services.clinical.engine import DiabetesEngine
from diabetes.services.clinical.monitoring_decision import (
    resolve_monitoring_interpretation,
)
from diabetes.services.clinical.monitoring_narration_verifier import (
    verified_monitoring_narration_or_fallback,
    verify_monitoring_narration,
)


def _context():
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
        has_sufficient_data=True,
        language="fr",
    )


def _resolution():
    resolution = resolve_monitoring_interpretation(
        "Explique-moi ma tendance glycémique cette semaine",
        _context(),
        language="fr",
    )
    assert resolution is not None
    return resolution


def test_current_monitoring_fallback_passes_verifier():
    resolution = _resolution()

    result = verify_monitoring_narration(
        resolution.decision,
        resolution.reply,
    )

    assert result.passed
    assert result.violations == ()


@pytest.mark.parametrize(
    ("candidate", "expected"),
    [
        (
            "Réduis ta dose de moitié.",
            "forbidden:change_treatment",
        ),
        (
            "Prends 4 unités avec ton repas.",
            "forbidden:calculate_insulin_dose",
        ),
        (
            "Ton diabète s'améliore nettement.",
            "forbidden:declare_clinical_improvement_or_deterioration",
        ),
        (
            "Marche 30 minutes pour faire baisser ton glucose.",
            "forbidden:recommend_compensatory_activity",
        ),
        (
            "Tes chiffres prouvent que tu as une hyperglycémie.",
            "forbidden:diagnose_from_monitoring",
        ),
    ],
)
def test_monitoring_verifier_rejects_unauthorized_clinical_claims(candidate, expected):
    resolution = _resolution()

    result = verify_monitoring_narration(resolution.decision, candidate)

    assert not result.passed
    assert expected in result.violations


def test_invalid_candidate_uses_verified_monitoring_fallback():
    resolution = _resolution()

    selected = verified_monitoring_narration_or_fallback(
        resolution.decision,
        "Réduis ta dose de moitié.",
        resolution.reply,
    )

    assert selected == resolution.reply


def test_diabetes_engine_dispatches_monitoring_to_monitoring_verifier():
    resolution = _resolution()

    selected = DiabetesEngine().verify_advice_reply(
        resolution,
        resolution.reply,
    )

    assert selected == resolution.reply


def test_unknown_governed_family_fails_closed():
    resolution = _resolution()
    decision = resolution.decision
    object.__setattr__(decision, "rule_id", "diabetes.unknown.rule")

    with pytest.raises(PermissionError, match="unsupported governed advice verifier"):
        DiabetesEngine().verify_advice_reply(resolution, resolution.reply)
