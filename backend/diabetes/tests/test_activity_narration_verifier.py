from core.contracts.domain_context import DomainContext
from diabetes.services.clinical.activity_decision import resolve_activity_context
from diabetes.services.clinical.activity_narration_verifier import (
    verified_activity_narration_or_fallback,
    verify_activity_narration,
)


def _resolution():
    context = DomainContext(
        kpi_summary={"avg_glucose": 140},
        detected_patterns=["LOW_GLUCOSE_WITH_RECORDED_ACTIVITY"],
        insights=[],
        pivot_text="context:activity",
        trend={},
        has_sufficient_data=True,
        language="fr",
    )
    return resolve_activity_context(
        "Est-ce que le sport cause mes baisses de glycémie ?",
        context,
        language="fr",
    )


def test_activity_fallback_passes_its_own_verifier():
    resolution = _resolution()
    assert resolution is not None
    check = verify_activity_narration(resolution.decision, resolution.reply)
    assert check.passed


def test_activity_verifier_rejects_adversarial_actions():
    resolution = _resolution()
    assert resolution is not None
    unsafe = (
        "Le sport cause ta baisse de glycémie. ",
        "Tu dois faire de l'exercice. ",
        "Marche pour faire baisser ton sucre. ",
        "Réduis ta dose d'insuline. ",
        "Prends 4 unités d'insuline. ",
        "Le sport prouve une hypoglycémie. ",
    )
    for candidate in unsafe:
        assert not verify_activity_narration(resolution.decision, candidate).passed


def test_activity_verifier_falls_back_on_unsafe_candidate():
    resolution = _resolution()
    assert resolution is not None
    candidate = "Marche pour faire baisser ton sucre."
    assert verified_activity_narration_or_fallback(
        resolution.decision, candidate, resolution.reply
    ) == resolution.reply
