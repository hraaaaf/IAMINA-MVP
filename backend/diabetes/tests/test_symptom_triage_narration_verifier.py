from core.contracts.domain_context import DomainContext
from diabetes.services.clinical.symptom_triage_decision import resolve_symptom_triage
from diabetes.services.clinical.symptom_triage_narration_verifier import (
    verified_symptom_triage_narration_or_fallback,
    verify_symptom_triage_narration,
)


def _resolution():
    return resolve_symptom_triage(
        "J'ai des nausées et mal au ventre aujourd'hui.",
        DomainContext.empty(language="fr"),
        language="fr",
    )


def test_symptom_triage_fallback_passes_its_own_verifier():
    resolution = _resolution()
    assert resolution is not None
    assert verify_symptom_triage_narration(
        resolution.decision,
        resolution.reply,
    ).passed


def test_symptom_triage_verifier_rejects_unsafe_narration():
    resolution = _resolution()
    assert resolution is not None
    unsafe = (
        "Ce n'est pas grave.",
        "Tu as une hypoglycémie.",
        "Attends demain avant de contacter un médecin.",
        "Réduis ton traitement.",
        "Prends du paracétamol.",
        "Ce n'est pas une urgence.",
    )
    for candidate in unsafe:
        assert not verify_symptom_triage_narration(
            resolution.decision,
            candidate,
        ).passed


def test_symptom_triage_verifier_falls_back_on_unsafe_candidate():
    resolution = _resolution()
    assert resolution is not None
    assert verified_symptom_triage_narration_or_fallback(
        resolution.decision,
        "Ce n'est pas grave.",
        resolution.reply,
    ) == resolution.reply
