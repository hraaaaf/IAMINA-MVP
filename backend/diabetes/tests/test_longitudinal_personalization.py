from unittest.mock import patch

import pytest

from core.contracts.companion_context import (
    CompanionAfterVisit,
    CompanionContext,
    CompanionPattern,
)
from core.contracts.domain_context import DomainContext
from diabetes.services.clinical.engine import DiabetesEngine
from diabetes.services.clinical.longitudinal_personalization_decision import (
    classify_longitudinal_personalization,
    resolve_longitudinal_personalization_from_context,
)
from diabetes.services.clinical.longitudinal_personalization_narration_verifier import (
    verified_longitudinal_narration_or_fallback,
    verify_longitudinal_narration,
)


def _pattern(
    key="context:activity",
    *,
    recurrence_count=3,
    evidence_density="moderate",
    state="active",
):
    return CompanionPattern(
        observation_key=key,
        current_state=state,
        markers=("persisting", "recurring"),
        evidence_density=evidence_density,
        recurrence_count=recurrence_count,
        baseline_direction="below_personal_window_baseline",
        baseline_movement="stable_relative_to_personal_window_baseline",
        first_observed_at="2026-08-10T10:00:00+00:00",
        last_observed_at="2026-09-20T10:00:00+00:00",
        evidence_id="rule.personal-response.repetition.v1",
        source_version="companion-personal-pattern-intelligence.v1",
        limitations=(
            "observational_association_only",
            "no_diagnosis_causality_treatment_response_or_future_prediction",
        ),
    )


def _context(*patterns):
    return CompanionContext(
        pattern_status="ready" if patterns else "no_governed_patterns",
        review_status="unavailable",
        review_anchor_captured_at=None,
        patterns=tuple(patterns),
        changes_since_review=(),
        after_visit=CompanionAfterVisit(
            status="no_recorded_visit",
            anchor_id=None,
            occurred_at=None,
            source=None,
            fact_count=0,
            latest_fact_at=None,
        ),
        safety_notice="descriptive only",
        source_version="companion-overview.v1",
        language="fr",
    )


@pytest.mark.parametrize(
    "message",
    (
        "Qu’est-ce que tu remarques chez moi sur la durée dans mes données ?",
        "Do you see recurring patterns in my data over time?",
        "Wach kayn chi pattern kayt3awd 3ndi f data dyali?",
        "هل يوجد نمط يتكرر عندي مع الوقت في بياناتي؟",
    ),
)
def test_classifier_requires_explicit_personal_longitudinal_intent(message):
    assert classify_longitudinal_personalization(message)


@pytest.mark.parametrize(
    "message",
    (
        "Mon médecin se répète souvent.",
        "Explain recurring patterns in diabetes generally.",
        "Tu te souviens de moi ?",
    ),
)
def test_classifier_rejects_non_personal_or_non_data_false_positives(message):
    assert not classify_longitudinal_personalization(message)


def test_personalization_uses_only_exact_governed_pattern_facts():
    resolution = resolve_longitudinal_personalization_from_context(
        "Qu’est-ce que tu remarques chez moi sur la durée dans mes données ?",
        _context(_pattern()),
        language="fr",
    )

    assert resolution is not None
    decision = resolution.decision
    assert decision.authority_level.value == "L1"
    assert decision.rule_id == "diabetes.longitudinal.descriptive_personalization"
    assert decision.allowed_actions == ("describe_governed_longitudinal_observation",)
    assert decision.evidence_refs == ("rule.personal-response.repetition.v1",)
    assert "infer_causality" in decision.forbidden_actions
    assert "predict_future_outcome" in decision.forbidden_actions
    assert "activité enregistrée" in resolution.reply
    assert "2026-08-10" in resolution.reply
    assert "2026-09-20" in resolution.reply
    assert "3 épisode(s)" in resolution.reply
    assert "densité de répétition modérée" in resolution.reply
    assert "ne prouve ni une cause" in resolution.reply


def test_topic_focus_does_not_substitute_an_unrelated_pattern():
    resolution = resolve_longitudinal_personalization_from_context(
        "Est-ce que le sport se répète souvent chez moi dans mes données ?",
        _context(_pattern("context:stress")),
        language="fr",
    )

    assert resolution is not None
    assert resolution.decision.rule_id == "diabetes.longitudinal.insufficient_data"
    assert resolution.decision.missing_facts == ("governed_longitudinal_pattern",)
    assert "pas assez d’observations longitudinales gouvernées" in resolution.reply


def test_topic_focus_selects_matching_governed_pattern_without_ranking_other_patterns():
    resolution = resolve_longitudinal_personalization_from_context(
        "Est-ce que le sport se répète souvent chez moi dans mes données ?",
        _context(_pattern("context:stress"), _pattern("context:activity", recurrence_count=4)),
        language="fr",
    )

    assert resolution is not None
    assert "activité enregistrée" in resolution.reply
    assert "4 épisode(s)" in resolution.reply
    assert "stress enregistré" not in resolution.reply


def test_unapproved_companion_provenance_fails_closed_as_integrity_error():
    context = _context(_pattern())
    bad = CompanionContext(
        pattern_status=context.pattern_status,
        review_status=context.review_status,
        review_anchor_captured_at=context.review_anchor_captured_at,
        patterns=context.patterns,
        changes_since_review=context.changes_since_review,
        after_visit=context.after_visit,
        safety_notice=context.safety_notice,
        source_version="unreviewed-context.v9",
        language=context.language,
    )

    with pytest.raises(ValueError, match="certified companion overview"):
        resolve_longitudinal_personalization_from_context(
            "Qu’est-ce que tu remarques chez moi sur la durée dans mes données ?",
            bad,
            language="fr",
        )


def test_unapproved_pattern_evidence_id_fails_closed():
    pattern = _pattern()
    bad = CompanionPattern(
        observation_key=pattern.observation_key,
        current_state=pattern.current_state,
        markers=pattern.markers,
        evidence_density=pattern.evidence_density,
        recurrence_count=pattern.recurrence_count,
        baseline_direction=pattern.baseline_direction,
        baseline_movement=pattern.baseline_movement,
        first_observed_at=pattern.first_observed_at,
        last_observed_at=pattern.last_observed_at,
        evidence_id="heuristic.unreviewed.v1",
        source_version=pattern.source_version,
        limitations=pattern.limitations,
    )

    with pytest.raises(ValueError, match="unapproved evidence id"):
        resolve_longitudinal_personalization_from_context(
            "Qu’est-ce que tu remarques chez moi sur la durée dans mes données ?",
            _context(bad),
            language="fr",
        )


def test_explicit_dose_request_yields_to_shared_safety_gate():
    assert not classify_longitudinal_personalization(
        "Dans mes données sur la durée, combien d’unités d’insuline dois-je prendre ?"
    )


def test_longitudinal_verifier_accepts_only_exact_deterministic_copy():
    resolution = resolve_longitudinal_personalization_from_context(
        "Qu’est-ce que tu remarques chez moi sur la durée dans mes données ?",
        _context(_pattern()),
        language="fr",
    )
    assert resolution is not None

    check = verify_longitudinal_narration(
        resolution.decision,
        resolution.reply,
        resolution.reply,
    )
    assert check.passed
    assert (
        verified_longitudinal_narration_or_fallback(
            resolution.decision,
            "Le sport fait clairement baisser ta glycémie.",
            resolution.reply,
        )
        == resolution.reply
    )


def test_engine_patient_aware_seam_consumes_companion_context_only_after_intent_match():
    engine = DiabetesEngine()
    context = _context(_pattern())
    with patch.object(engine, "companion_context", return_value=context) as companion:
        resolution = engine.resolve_patient_advice(
            42,
            "Qu’est-ce que tu remarques chez moi sur la durée dans mes données ?",
            DomainContext.empty(language="fr"),
            language="fr",
        )

    companion.assert_called_once_with(42, language="fr")
    assert resolution is not None
    assert resolution.decision.rule_id == "diabetes.longitudinal.descriptive_personalization"


def test_engine_does_not_fetch_companion_context_for_unrelated_message():
    engine = DiabetesEngine()
    with patch.object(engine, "companion_context") as companion:
        resolution = engine.resolve_patient_advice(
            42,
            "Raconte-moi une blague.",
            DomainContext.empty(language="fr"),
            language="fr",
        )

    companion.assert_not_called()
    assert resolution is None


def test_latin_darija_longitudinal_reply_keeps_latin_script():
    resolution = resolve_longitudinal_personalization_from_context(
        "Wach kayn chi pattern kayt3awd 3ndi f data dyali?",
        _context(_pattern()),
        language="ar-MA",
    )

    assert resolution is not None
    assert not any("\u0600" <= ch <= "\u06ff" for ch in resolution.reply)


def test_inconsistent_pattern_status_fails_closed():
    context = _context(_pattern())
    bad = CompanionContext(
        pattern_status="available",
        review_status=context.review_status,
        review_anchor_captured_at=context.review_anchor_captured_at,
        patterns=context.patterns,
        changes_since_review=context.changes_since_review,
        after_visit=context.after_visit,
        safety_notice=context.safety_notice,
        source_version=context.source_version,
        language=context.language,
    )

    with pytest.raises(ValueError, match="governed pattern status"):
        resolve_longitudinal_personalization_from_context(
            "Qu’est-ce que tu remarques chez moi sur la durée dans mes données ?",
            bad,
            language="fr",
        )


def test_unknown_or_quarantined_observation_key_fails_closed():
    pattern = _pattern()
    bad = CompanionPattern(
        observation_key="legacy:food_sensitivity",
        current_state=pattern.current_state,
        markers=pattern.markers,
        evidence_density=pattern.evidence_density,
        recurrence_count=pattern.recurrence_count,
        baseline_direction=pattern.baseline_direction,
        baseline_movement=pattern.baseline_movement,
        first_observed_at=pattern.first_observed_at,
        last_observed_at=pattern.last_observed_at,
        evidence_id=pattern.evidence_id,
        source_version=pattern.source_version,
        limitations=pattern.limitations,
    )

    with pytest.raises(ValueError, match="unapproved longitudinal observation key"):
        resolve_longitudinal_personalization_from_context(
            "Qu’est-ce que tu remarques chez moi sur la durée dans mes données ?",
            _context(bad),
            language="fr",
        )


def test_general_multiple_patterns_request_requires_scope():
    resolution = resolve_longitudinal_personalization_from_context(
        "Qu’est-ce que tu remarques chez moi sur la durée dans mes données ?",
        _context(_pattern("context:stress"), _pattern("context:activity")),
        language="fr",
    )

    assert resolution is not None
    assert resolution.decision.rule_id == "diabetes.longitudinal.multiple_patterns"
    assert resolution.decision.allowed_actions == ("request_longitudinal_scope",)
    assert "priorité" in resolution.reply


def test_broad_meal_focus_with_multiple_patterns_requires_exact_meal():
    resolution = resolve_longitudinal_personalization_from_context(
        "Est-ce que les repas se répètent souvent chez moi dans mes données ?",
        _context(_pattern("meal:breakfast"), _pattern("meal:dinner")),
        language="fr",
    )

    assert resolution is not None
    assert resolution.decision.rule_id == "diabetes.longitudinal.multiple_patterns"
    assert "petit-déjeuner" in resolution.reply
    assert "dîner" in resolution.reply


def test_multiple_patterns_latin_darija_stays_latin():
    resolution = resolve_longitudinal_personalization_from_context(
        "Wach kayn chi pattern kayt3awd 3ndi f data dyali?",
        _context(_pattern("context:stress"), _pattern("context:activity")),
        language="ar-MA",
    )

    assert resolution is not None
    assert resolution.decision.rule_id == "diabetes.longitudinal.multiple_patterns"
    assert not any("\u0600" <= ch <= "\u06ff" for ch in resolution.reply)


def test_generic_question_with_multiple_patterns_does_not_infer_priority():
    resolution = resolve_longitudinal_personalization_from_context(
        "Qu’est-ce que tu remarques chez moi sur la durée dans mes données ?",
        _context(_pattern("context:stress"), _pattern("context:activity")),
        language="fr",
    )

    assert resolution is not None
    assert resolution.decision.rule_id == "diabetes.longitudinal.multiple_patterns"
    assert resolution.decision.allowed_actions == ("request_longitudinal_scope",)
    assert "infer_clinical_priority" in resolution.decision.forbidden_actions
    assert "leur ordre ne constitue pas une priorité clinique" in resolution.reply
    assert "activité enregistrée" not in resolution.reply
    assert "stress enregistré" not in resolution.reply


def test_latin_darija_multiple_patterns_reply_keeps_latin_script():
    resolution = resolve_longitudinal_personalization_from_context(
        "Wach kayn chi pattern kayt3awd 3ndi f data dyali?",
        _context(_pattern("context:stress"), _pattern("context:activity")),
        language="ar-MA",
    )

    assert resolution is not None
    assert resolution.decision.rule_id == "diabetes.longitudinal.multiple_patterns"
    assert not any("\u0600" <= ch <= "\u06ff" for ch in resolution.reply)


def test_contradictory_observation_dates_fail_closed():
    pattern = _pattern()
    bad = CompanionPattern(
        observation_key=pattern.observation_key,
        current_state=pattern.current_state,
        markers=pattern.markers,
        evidence_density=pattern.evidence_density,
        recurrence_count=pattern.recurrence_count,
        baseline_direction=pattern.baseline_direction,
        baseline_movement=pattern.baseline_movement,
        first_observed_at="2026-09-21T10:00:00+00:00",
        last_observed_at="2026-08-10T10:00:00+00:00",
        evidence_id=pattern.evidence_id,
        source_version=pattern.source_version,
        limitations=pattern.limitations,
    )

    with pytest.raises(ValueError, match="contradictory observation dates"):
        resolve_longitudinal_personalization_from_context(
            "Qu’est-ce que tu remarques chez moi sur la durée dans mes données ?",
            _context(bad),
            language="fr",
        )


def test_missing_noncausal_safety_limitations_fail_closed():
    pattern = _pattern()
    bad = CompanionPattern(
        observation_key=pattern.observation_key,
        current_state=pattern.current_state,
        markers=pattern.markers,
        evidence_density=pattern.evidence_density,
        recurrence_count=pattern.recurrence_count,
        baseline_direction=pattern.baseline_direction,
        baseline_movement=pattern.baseline_movement,
        first_observed_at=pattern.first_observed_at,
        last_observed_at=pattern.last_observed_at,
        evidence_id=pattern.evidence_id,
        source_version=pattern.source_version,
        limitations=("observational_association_only",),
    )

    with pytest.raises(ValueError, match="missing required safety limitations"):
        resolve_longitudinal_personalization_from_context(
            "Qu’est-ce que tu remarques chez moi sur la durée dans mes données ?",
            _context(bad),
            language="fr",
        )
