from evaluation.native_voice_shadow_benchmark import (
    CRITICAL_CASE_MIN_SCORE,
    REVIEWER_DISAGREEMENT_THRESHOLD,
    SCENARIOS,
    SUPPORTED_LOCALES,
    TARGET_MEAN_SCORE,
    reviewer_template,
    validate_native_voice_dataset,
)


def test_native_voice_dataset_is_complete_and_balanced():
    summary = validate_native_voice_dataset()

    assert summary == {
        "scenario_count": 7,
        "locale_count": 6,
        "turns_per_scenario": 10,
        "total_turns": 70,
    }


def test_every_supported_locale_has_coverage():
    covered = {scenario.locale for scenario in SCENARIOS}
    assert covered == set(SUPPORTED_LOCALES)


def test_darija_covers_arabic_and_arabizi_separately():
    darija = [scenario for scenario in SCENARIOS if scenario.locale == "ar-MA"]

    assert {scenario.script for scenario in darija} == {"arabic", "latin"}
    assert {scenario.scenario_id for scenario in darija} == {
        "darija_arabic",
        "darija_arabizi",
    }


def test_each_scenario_contains_safety_and_correction_turns():
    for scenario in SCENARIOS:
        ids = {turn.turn_id for turn in scenario.turns}
        assert "safety_boundary" in ids
        assert "correction" in ids
        assert "governed_clinical" in ids
        assert "recap" in ids


def test_human_review_gate_cannot_be_replaced_by_machine_score():
    template = reviewer_template()

    assert template["native_speaker_required"] is True
    assert template["blind_ab_required"] is True
    assert template["reviewers_required"] == 2
    assert template["target_mean_score"] == TARGET_MEAN_SCORE == 9.5
    assert template["critical_case_min_score"] == CRITICAL_CASE_MIN_SCORE == 8.5
    assert (
        template["third_reviewer_if_score_gap_gt"]
        == REVIEWER_DISAGREEMENT_THRESHOLD
        == 1.5
    )


def test_rubric_contains_native_quality_not_only_dialect_markers():
    rubric = set(reviewer_template()["rubric_dimensions"])

    assert "native_naturalness" in rubric
    assert "no_translation_smell" in rubric
    assert "non_caricature" in rubric
    assert "relational_continuity" in rubric
    assert "would_continue_chatting" in rubric
