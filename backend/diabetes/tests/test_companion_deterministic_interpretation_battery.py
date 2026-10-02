# Deterministic interpretation coverage audit: no LLM/provider calls.
import pytest

from companion.zero_model_router import exact_chitchat_reply
from core.contracts.domain_context import DomainContext
from core.input_safety import INSULIN_BLOCK, PRESCRIPTION_BLOCK, URGENT, evaluate_input_safety
from diabetes.services.clinical.activity_decision import resolve_activity_context
from diabetes.services.clinical.clinician_prep_decision import classify_clinician_prep
from diabetes.services.clinical.food_decision import resolve_food_decision
from diabetes.services.clinical.longitudinal_personalization_decision import (
    classify_longitudinal_personalization,
)
from diabetes.services.clinical.monitoring_decision import resolve_monitoring_interpretation
from diabetes.services.clinical.symptom_triage_decision import resolve_symptom_triage


def _rich_context(language: str = "fr") -> DomainContext:
    return DomainContext(
        kpi_summary={
            "avg_glucose": 142.0,
            "tir_pct": 68.0,
            "cv_pct": 31.0,
            "tar_pct": 28.0,
            "tbr_pct": 4.0,
            "gmi": None,
            "log_count": 42,
            "days_with_data": 7,
        },
        detected_patterns=["LOW_GLUCOSE_WITH_RECORDED_ACTIVITY"],
        insights=["context:activity explicitly recorded"],
        pivot_text="42 recorded glucose measurements over 7 days",
        trend={
            "current_week_tir": 68.0,
            "prev_week_tir": 64.0,
            "tir_delta": 4.0,
            "direction": "up",
        },
        has_sufficient_data=True,
        analysis_status="complete",
        language=language,
    )


def _deterministic_route(message: str, language: str = "fr") -> str | None:
    safety = evaluate_input_safety(message, language)
    if safety.action == URGENT:
        return "safety:urgent"
    if safety.action == INSULIN_BLOCK:
        return "safety:insulin"
    if safety.action == PRESCRIPTION_BLOCK:
        return "safety:prescription"

    if exact_chitchat_reply(message, language) is not None:
        return "chitchat"

    context = _rich_context(language)

    food = resolve_food_decision(message, language=language)
    if food is not None:
        return food.decision.rule_id

    monitoring = resolve_monitoring_interpretation(message, context, language=language)
    if monitoring is not None:
        return monitoring.decision.rule_id

    activity = resolve_activity_context(message, context, language=language)
    if activity is not None:
        return activity.decision.rule_id

    symptom = resolve_symptom_triage(message, context, language=language)
    if symptom is not None:
        return symptom.decision.rule_id

    if classify_clinician_prep(message):
        return "diabetes.clinician_prep"

    if classify_longitudinal_personalization(message):
        return "diabetes.longitudinal"

    return None


@pytest.mark.parametrize(
    ("message", "language", "expected_prefix"),
    [
        ("hi ça va ?", "fr", "chitchat"),
        ("Quel est mon TIR cette semaine ?", "fr", "diabetes.monitoring."),
        ("Comment était mon diabète cette semaine ?", "fr", "diabetes.monitoring."),
        ("check my logs and tell me!", "fr", "diabetes.monitoring."),
        ("Explique ma glycémie moyenne cette semaine", "fr", "diabetes.monitoring."),
        ("Puis-je manger du couscous ?", "fr", "diabetes.food."),
        ("Combien de glucides dans ce gâteau ?", "fr", "diabetes.food."),
        ("Quel est le meilleur à manger, riz ou pâtes ?", "fr", "diabetes.food."),
        ("Est-ce que le sport cause mes baisses de glycémie ?", "fr", "diabetes.activity."),
        ("J'ai des nausées et mal au ventre aujourd'hui.", "fr", "diabetes.symptom."),
        ("Aide-moi à préparer mes questions pour mon médecin.", "fr", "diabetes.clinician_prep"),
        (
            "Qu’est-ce que tu remarques chez moi sur la durée dans mes données ?",
            "fr",
            "diabetes.longitudinal",
        ),
        ("Je suis inconscient.", "fr", "safety:urgent"),
        ("Quelle dose d'insuline dois-je prendre ?", "fr", "safety:insulin"),
        ("Can I eat a slice of cake?", "en", "diabetes.food."),
        ("How does exercise affect my glucose?", "en", "diabetes.activity."),
        ("I feel nauseous and unwell today.", "en", "diabetes.symptom."),
        ("wach n9dar nakol gateau?", "ar-MA", "diabetes.food."),
        ("شنو تأثير الرياضة على السكر؟", "ar-MA", "diabetes.activity."),
        ("عندي غثيان وانا عيان اليوم", "ar-MA", "diabetes.symptom."),
        ("شنو نسول الطبيب؟", "ar-MA", "diabetes.clinician_prep"),
        ("هل يوجد نمط يتكرر عندي مع الوقت في بياناتي؟", "ar-MA", "diabetes.longitudinal"),
    ],
)
def test_supported_deterministic_intent_surface(message, language, expected_prefix):
    route = _deterministic_route(message, language)
    assert route is not None, message
    assert route.startswith(expected_prefix), (message, route)


@pytest.mark.parametrize(
    ("message", "gap"),
    [
        ("Quel est mon type de diabète enregistré ?", "profile lookup"),
        ("Quel traitement est enregistré dans mon profil ?", "treatment/profile lookup"),
        ("Quels sont mes objectifs glycémiques enregistrés ?", "target profile lookup"),
        ("Qu'est-ce que j'ai mangé hier ?", "journal meal-history retrieval"),
        ("Quelle était ma glycémie hier à 20h ?", "exact historical log retrieval"),
        ("Comment ai-je dormi cette semaine ?", "sleep-history retrieval"),
        ("Est-ce que j'étais stressé cette semaine ?", "stress-history retrieval"),
        ("Que dit mon dernier rapport de laboratoire ?", "lab/document retrieval"),
        ("Quels médicaments ont été importés de mon document ?", "document medication retrieval"),
        ("Quelle est ma dernière mesure CGM exacte ?", "exact latest CGM retrieval"),
        ("Quelles observations proactives sont en attente ?", "proactive insight retrieval"),
        ("Montre-moi mes épisodes pré/post repas liés.", "paired-meal episode retrieval"),
    ],
)
@pytest.mark.xfail(strict=False, reason="desired whole-app deterministic understanding not implemented")
def test_whole_app_deterministic_understanding_gaps(message, gap):
    route = _deterministic_route(message, "fr")
    assert route is not None, f"{gap}: {message}"
