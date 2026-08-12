"""Regression tests for evidence-qualified diabetes observations."""

from datetime import datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace

from django.test import SimpleTestCase

from diabetes.services.clinical.engine import (
    detect_dawn_phenomenon,
    detect_food_sensitivity,
    detect_high_variability,
    detect_post_exercise_hypo,
    detect_postmeal_spike,
    detect_sleep_impact,
    detect_somogyi_rebound,
    detect_stress_correlation,
)
from diabetes.services.clinical.sql_analytics import AnalyticalKPIs

_BASE = datetime(2026, 4, 1)


def _e(
    hour,
    day_offset,
    bg,
    *,
    meal_description="",
    exercised="",
    sleep_quality="",
    stressed="",
    fatigue_level="",
    is_sick="",
    meal_type="",
    glycemic_context="",
    source="manual",
):
    return SimpleNamespace(
        effective_time=_BASE + timedelta(days=day_offset, hours=hour),
        blood_sugar=Decimal(str(bg)),
        meal_description=meal_description,
        exercised=exercised,
        sleep_quality=sleep_quality,
        stressed=stressed,
        fatigue_level=fatigue_level,
        is_sick=is_sick,
        meal_type=meal_type,
        glycemic_context=glycemic_context,
        source=source,
    )


def _assert_observation_only(testcase: SimpleTestCase, pattern) -> None:
    text = " ".join(
        [
            pattern.title,
            pattern.evidence,
            pattern.fallback_content,
            pattern.fallback_action,
        ]
    ).lower()
    forbidden = (
        "ajustement de votre dose",
        "insuline basale",
        "insuline rapide",
        "bolus",
        "c'est l'effet somogyi",
        "directement liée",
        "est la cause",
    )
    for phrase in forbidden:
        testcase.assertNotIn(phrase, text)
    testcase.assertIn("ne", pattern.evidence.lower())
    testcase.assertTrue(pattern.source_version)
    testcase.assertTrue(pattern.limitations)


class NeutralTimePatternTests(SimpleTestCase):
    def test_morning_night_pattern_is_not_dawn_diagnosis(self):
        entries = (
            [_e(7, i, 180) for i in range(4)]
            + [_e(23, i, 110) for i in range(3)]
        )
        result = detect_dawn_phenomenon(entries)
        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result.code, "MORNING_NIGHT_GLUCOSE_DIFFERENCE")
        self.assertNotIn("phénomène de l'aube", result.title.lower())
        _assert_observation_only(self, result)

    def test_no_morning_night_pattern_with_insufficient_data(self):
        self.assertIsNone(detect_dawn_phenomenon([_e(7, 0, 190), _e(23, 0, 100)]))


class ActivityObservationTests(SimpleTestCase):
    def test_requires_repeated_low_values_across_two_days(self):
        entries = [
            _e(8, 0, 120, exercised="yes"),
            _e(18, 0, 65),
            _e(20, 0, 60),
            _e(8, 1, 115, exercised="yes"),
            _e(20, 1, 68),
        ]
        result = detect_post_exercise_hypo(entries)
        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result.code, "LOW_GLUCOSE_WITH_RECORDED_ACTIVITY")
        self.assertGreaterEqual(result.evidence_count, 3)
        self.assertGreaterEqual(result.distinct_days, 2)
        _assert_observation_only(self, result)

    def test_two_events_do_not_meet_strengthened_repetition_gate(self):
        entries = [
            _e(8, 0, 120, exercised="yes"),
            _e(20, 0, 65),
            _e(8, 1, 120, exercised="yes"),
            _e(20, 1, 65),
        ]
        self.assertIsNone(detect_post_exercise_hypo(entries))


class ContextObservationTests(SimpleTestCase):
    def test_stress_uses_positive_context_without_negative_control(self):
        entries = [
            _e(10, 0, 210, stressed="yes"),
            _e(10, 1, 205, stressed="yes"),
            _e(10, 2, 200, stressed="yes"),
        ]
        result = detect_stress_correlation(entries)
        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result.code, "GLUCOSE_WITH_RECORDED_STRESS")
        self.assertNotIn("jours calmes", result.evidence.lower())
        _assert_observation_only(self, result)

    def test_sleep_uses_explicit_bad_sleep_only(self):
        entries = [
            _e(8, 0, 160, sleep_quality="bad"),
            _e(8, 1, 155, sleep_quality="bad"),
            _e(8, 2, 150, sleep_quality="bad"),
        ]
        result = detect_sleep_impact(entries)
        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result.code, "GLUCOSE_WITH_RECORDED_POOR_SLEEP")
        _assert_observation_only(self, result)


class SQLFirstVariabilityTests(SimpleTestCase):
    def test_raw_entry_cv_detector_is_retired(self):
        entries = [_e(10, i, 250 if i % 2 == 0 else 55) for i in range(20)]
        self.assertIsNone(detect_high_variability(entries))

    def test_kpi_dataclass_stability_property_unchanged(self):
        kpis = AnalyticalKPIs(
            avg_glucose=140.0,
            std_dev=20.0,
            cv_pct=36.0,
            tir_pct=75.0,
            tar_pct=20.0,
            tbr_pct=5.0,
            gmi=6.7,
            log_count=1000,
            days_with_data=14,
            cgm_active_pct=90.0,
        )
        self.assertTrue(kpis.is_stable)


class MealObservationTests(SimpleTestCase):
    def test_food_text_does_not_claim_sensitivity(self):
        entries = [
            _e(13, 0, 230, meal_description="couscous tfaya"),
            _e(13, 2, 215, meal_description="harira"),
            _e(13, 3, 220, meal_description="couscous tfaya"),
        ]
        result = detect_food_sensitivity(entries)
        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result.code, "HIGH_GLUCOSE_WITH_RECORDED_MEAL_TEXT")
        self.assertNotIn("sensibilité", result.title.lower())
        _assert_observation_only(self, result)

    def test_postmeal_rise_requires_explicit_pre_and_post_context(self):
        entries = [
            _e(12, 0, 100, meal_type="lunch", glycemic_context="pre_meal"),
            _e(14, 0, 170, meal_type="lunch", glycemic_context="post_meal"),
            _e(12, 1, 110, meal_type="lunch", glycemic_context="pre_meal"),
            _e(14, 1, 180, meal_type="lunch", glycemic_context="post_meal"),
        ]
        result = detect_postmeal_spike(entries)
        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result.code, "REPEATED_PRE_POST_MEAL_RISE")
        _assert_observation_only(self, result)

    def test_meal_tag_without_explicit_measurement_context_fails_closed(self):
        entries = [
            _e(12, 0, 100, meal_type="lunch"),
            _e(14, 0, 180, meal_type="lunch"),
            _e(12, 1, 100, meal_type="lunch"),
            _e(14, 1, 180, meal_type="lunch"),
        ]
        self.assertIsNone(detect_postmeal_spike(entries))


class NightLowMorningHighTests(SimpleTestCase):
    def _pair(self, day):
        return [
            _e(23, day, 65, source="cgm"),
            _e(7, day + 1, 190, source="cgm"),
        ]

    def test_neutral_cgm_sequence_detected_without_somogyi_label(self):
        result = detect_somogyi_rebound(self._pair(0) + self._pair(5))
        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result.code, "NIGHT_LOW_THEN_MORNING_HIGH")
        self.assertNotIn("somogyi", result.title.lower())
        self.assertNotIn("somogyi", result.fallback_content.lower())
        _assert_observation_only(self, result)

    def test_manual_sparse_pairs_do_not_create_named_mechanism(self):
        entries = [
            _e(23, 0, 65, source="manual"),
            _e(7, 1, 190, source="manual"),
            _e(23, 5, 65, source="manual"),
            _e(7, 6, 190, source="manual"),
        ]
        self.assertIsNone(detect_somogyi_rebound(entries))
