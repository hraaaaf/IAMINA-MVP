import re

import pytest

from core.contracts.advice_decision import AdviceAuthorityLevel, AdviceDisposition
from diabetes.services.clinical.food_decision import (
    ADA_2026_NUTRITION,
    NICE_NG17_DIETARY,
    NICE_NG28_DIETARY,
    FoodDecisionIntent,
    classify_food_decision,
    resolve_food_decision,
)

_ARABIC_RE = re.compile(r"[\u0600-\u06ff\u0750-\u077f]")


@pytest.mark.parametrize(
    ("message", "language"),
    [
        ("je peux manger un mille feuille !?", "fr"),
        ("Est-ce que ce dessert est autorisé ?", "fr"),
        ("Puis-je manger du couscous ?", "fr"),
        ("jpeux manger du gateau ?", "fr"),
        ("Can I eat a slice of cake?", "en"),
        ("Is it okay if I have cake?", "en"),
        ("wash nqder nakol gateau?", "fr"),
        ("wach n9dr nakol gateau?", "ar-MA"),
        ("wach n9dar nchrob jus?", "fr"),
        ("واش نقدر ناكل الحلوى؟", "ar-MA"),
        ("هل أقدر آكل قطعة حلوى؟", "ar"),
        ("هل يمكنني تناول قطعة حلوى؟", "ar"),
        ("عادي آكل كيك؟", "ar-SA"),
    ],
)
def test_food_permission_paraphrases_converge_to_same_governed_decision(message, language):
    resolution = resolve_food_decision(message, language=language)

    assert resolution is not None
    decision = resolution.decision
    assert decision.intent == FoodDecisionIntent.PERMISSION.value
    assert decision.authority_level is AdviceAuthorityLevel.L2_LOW_RISK_PRACTICAL
    assert decision.decision is AdviceDisposition.CONSTRAIN
    assert decision.rule_id == "diabetes.food.permission"
    assert set(decision.evidence_refs) == {
        ADA_2026_NUTRITION,
        NICE_NG17_DIETARY,
        NICE_NG28_DIETARY,
    }
    assert "approve_food_personally" in decision.forbidden_actions
    assert "forbid_food_personally" in decision.forbidden_actions
    assert "calculate_insulin_dose" in decision.forbidden_actions
    assert "change_treatment" in decision.forbidden_actions
    assert "compensate_food_with_activity" in decision.forbidden_actions
    assert resolution.reply


@pytest.mark.parametrize(
    ("message", "language"),
    [
        ("Combien de glucides contient ce mille-feuille ?", "fr"),
        ("Combien de gluc dans ce gateau ?", "fr"),
        ("How many carbs are in this?", "en"),
        ("ch7al men glucides f had lmakla?", "fr"),
        ("كم كربوهيدرات في هذه الوجبة؟", "ar"),
    ],
)
def test_food_nutrition_questions_are_education_not_binary_permission(message, language):
    resolution = resolve_food_decision(message, language=language)

    assert resolution is not None
    assert resolution.decision.intent == FoodDecisionIntent.PORTION_CARBOHYDRATE.value
    assert resolution.decision.authority_level is AdviceAuthorityLevel.L1_EDUCATION
    assert resolution.decision.rule_id == "diabetes.food.portion_carbohydrate"
    assert set(resolution.decision.evidence_refs) == {
        ADA_2026_NUTRITION,
        NICE_NG17_DIETARY,
        NICE_NG28_DIETARY,
    }
    assert "approve_food_personally" in resolution.decision.forbidden_actions


@pytest.mark.parametrize(
    ("message", "language"),
    [
        ("Quel est le meilleur à manger, riz ou pâtes ?", "fr"),
        ("Which is better to eat, rice or pasta?", "en"),
        ("chno ahssen nakol, khobz wla riz?", "fr"),
        ("أيهما أفضل للأكل، خبز أم رز؟", "ar"),
    ],
)
def test_food_comparisons_are_bounded_to_portion_and_carbohydrate(message, language):
    resolution = resolve_food_decision(message, language=language)

    assert resolution is not None
    assert resolution.decision.intent == FoodDecisionIntent.COMPARISON.value
    assert resolution.decision.authority_level is AdviceAuthorityLevel.L2_LOW_RISK_PRACTICAL
    assert resolution.decision.rule_id == "diabetes.food.comparison"
    assert "compare_food_options_by_portion_and_carbohydrate" in resolution.decision.allowed_actions
    assert "no_universal_allowed_forbidden_label" in resolution.decision.limitations


@pytest.mark.parametrize(
    "message",
    [
        "Puis-je prendre mon médicament ?",
        "Compare mon rapport avec celui du médecin.",
        "Quelle portion du rapport dois-je lire ?",
        "Je mange avec ma famille ce soir.",
        "Can I have the report by email?",
    ],
)
def test_food_classifier_fails_closed_on_non_food_phrasing(message):
    assert classify_food_decision(message) is None


def test_exact_mille_feuille_regression_does_not_give_binary_permission_or_activity_compensation():
    resolution = resolve_food_decision("je peux manger un mille feuille !?", language="fr")

    assert resolution is not None
    reply = resolution.reply.lower()
    assert "oui, tu peux" not in reply
    assert "bien sûr" not in reply
    assert "allerg" not in reply
    assert "activité" not in reply
    assert "marche" not in reply
    assert "portion" in reply
    assert "glucides" in reply


def test_latin_darija_food_reply_is_script_clean():
    resolution = resolve_food_decision("wach n9dar nakol gateau?", language="ar-MA")

    assert resolution is not None
    assert not _ARABIC_RE.search(resolution.reply)
    assert "lportion" in resolution.reply
    assert "glucides" in resolution.reply


def test_arabic_darija_food_reply_stays_arabic_script():
    resolution = resolve_food_decision("واش نقدر ناكل الحلوى؟", language="ar-MA")

    assert resolution is not None
    assert _ARABIC_RE.search(resolution.reply)
    assert "الكربوهيدرات" in resolution.reply


def test_gulf_food_reply_does_not_drift_to_moroccan_markers():
    resolution = resolve_food_decision("عادي آكل كيك؟", language="ar-SA")

    assert resolution is not None
    assert "أقدر" in resolution.reply
    for marker in ("شنو", "واش", "بغيت", "مزيان", "إيوا"):
        assert marker not in resolution.reply
