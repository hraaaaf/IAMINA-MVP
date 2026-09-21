import pytest

from diabetes.services.clinical.food_decision import resolve_food_decision
from diabetes.services.clinical.food_narration_verifier import (
    observe_food_narration_actions,
    verified_food_narration_or_fallback,
    verify_food_narration,
)


@pytest.mark.parametrize(
    ("message", "language"),
    [
        ("je peux manger un mille feuille !?", "fr"),
        ("Can I eat a slice of cake?", "en"),
        ("واش نقدر ناكل الحلوى؟", "ar-MA"),
        ("Combien de glucides contient ce mille-feuille ?", "fr"),
        ("Which is better to eat, rice or pasta?", "en"),
    ],
)
def test_current_deterministic_food_replies_pass_verifier(message, language):
    resolution = resolve_food_decision(message, language=language)

    assert resolution is not None
    result = verify_food_narration(resolution.decision, resolution.reply)

    assert result.passed
    assert result.violations == ()


@pytest.mark.parametrize(
    ("candidate", "expected"),
    [
        (
            "Oui, tu peux manger ce gâteau.",
            "forbidden:approve_food_personally",
        ),
        (
            "Ne mange pas ce dessert.",
            "forbidden:forbid_food_personally",
        ),
        (
            "Prends 4 units d'insuline avec ce dessert.",
            "forbidden:calculate_insulin_dose",
        ),
        (
            "Change ton traitement avant de manger.",
            "forbidden:change_treatment",
        ),
        (
            "Fais une marche après ce dessert pour compenser.",
            "forbidden:compensate_food_with_activity",
        ),
        (
            "Parce que ta glycémie est haute, choisis cette option.",
            "unauthorized:infer_patient_specific_causality",
        ),
        (
            "Au-dessus de 30 g de glucides, évite ce dessert.",
            "unauthorized:introduce_unapproved_threshold",
        ),
    ],
)
def test_food_verifier_rejects_actions_or_claims_outside_decision(candidate, expected):
    resolution = resolve_food_decision("je peux manger un gâteau ?", language="fr")

    assert resolution is not None
    result = verify_food_narration(resolution.decision, candidate)

    assert not result.passed
    assert expected in result.violations


def test_observer_exposes_allowed_food_actions_for_core_verifier():
    observed = observe_food_narration_actions(
        "Regardons la portion et les glucides. Donne-moi la portion ou l'étiquette."
    )

    assert "review_portion_and_carbohydrate_context" in observed
    assert "request_food_label_or_portion" in observed


def test_invalid_candidate_uses_verified_deterministic_fallback():
    resolution = resolve_food_decision("je peux manger un gâteau ?", language="fr")

    assert resolution is not None
    selected = verified_food_narration_or_fallback(
        resolution.decision,
        "Oui, tu peux manger ce gâteau.",
        resolution.reply,
    )

    assert selected == resolution.reply


def test_unsafe_fallback_fails_closed():
    resolution = resolve_food_decision("je peux manger un gâteau ?", language="fr")

    assert resolution is not None
    with pytest.raises(PermissionError, match="fallback failed"):
        verified_food_narration_or_fallback(
            resolution.decision,
            "Oui, tu peux manger ce gâteau.",
            "Prends 4 units d'insuline avec ce dessert.",
        )
