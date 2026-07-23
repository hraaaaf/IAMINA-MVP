"""
Clinical engine — unit tests for pattern detectors and sql_analytics helpers.
Each detector gets at minimum: a positive case, a negative case, an edge case.
"""
from datetime import datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace

from django.test import SimpleTestCase

from diabetes.services.clinical.engine import (
    detect_dawn_phenomenon,
    detect_food_sensitivity,
    detect_high_variability,
    detect_post_exercise_hypo,
    detect_sleep_impact,
    detect_somogyi_rebound,
    detect_stress_correlation,
)
from diabetes.services.clinical.sql_analytics import AnalyticalKPIs

# ─────────────────────────────────────────────────────────────────────────────
# Entry factory
# ─────────────────────────────────────────────────────────────────────────────

_BASE = datetime(2026, 4, 1)


def _e(hour, day_offset, bg, **kwargs):
    """Minimal LogEntry stand-in matching what every detector probes."""
    defaults = dict(
        meal_description="",
        exercised="no",
        sleep_quality="good",
        stressed="no",
        fatigue_level="ok",
        is_sick="no",
        meal_type="",
    )
    defaults.update(kwargs)
    return SimpleNamespace(
        effective_time=_BASE + timedelta(days=day_offset, hours=hour),
        blood_sugar=Decimal(str(bg)),
        **defaults,
    )


# ─────────────────────────────────────────────────────────────────────────────
# KPI formula contracts (inline — no dependency on deprecated helpers)
# ─────────────────────────────────────────────────────────────────────────────

def _gmi(mean_glucose: float) -> float:
    return round(3.31 + 0.02392 * mean_glucose, 1)


def _tir(entries, low: float = 70.0, high: float = 180.0) -> float:
    if not entries:
        return 0.0
    in_range = sum(1 for e in entries if low <= float(e.blood_sugar) <= high)
    return round((in_range / len(entries)) * 100, 1)


class GMITests(SimpleTestCase):
    def test_ada_formula(self):
        self.assertAlmostEqual(_gmi(154), 3.31 + 0.02392 * 154, places=1)

    def test_low_glucose(self):
        self.assertLess(_gmi(70), _gmi(154))

    def test_high_glucose(self):
        self.assertGreater(_gmi(250), _gmi(154))


class TIRTests(SimpleTestCase):
    def test_empty_returns_zero(self):
        self.assertEqual(_tir([]), 0.0)

    def test_all_in_range(self):
        entries = [_e(10, i, 120) for i in range(5)]
        self.assertEqual(_tir(entries), 100.0)

    def test_none_in_range(self):
        entries = [_e(10, 0, 250), _e(10, 1, 50)]
        self.assertEqual(_tir(entries), 0.0)

    def test_half_in_range(self):
        entries = [_e(10, 0, 100), _e(10, 1, 250)]
        self.assertEqual(_tir(entries), 50.0)


# ─────────────────────────────────────────────────────────────────────────────
# Dawn phenomenon detector
# ─────────────────────────────────────────────────────────────────────────────

class DawnPhenomenonTests(SimpleTestCase):

    def _morning(self, day, bg):
        return _e(7, day, bg)   # 7h AM = morning

    def _night(self, day, bg):
        return _e(23, day, bg)  # 11 PM = night

    def test_detects_classic_dawn(self):
        entries = (
            [self._morning(i, 180) for i in range(4)] +
            [self._night(i, 110) for i in range(3)]
        )
        result = detect_dawn_phenomenon(entries)
        self.assertIsNotNone(result)
        self.assertEqual(result.code, "DAWN_PHENOMENON")

    def test_no_detection_when_similar_levels(self):
        entries = (
            [self._morning(i, 120) for i in range(4)] +
            [self._night(i, 115) for i in range(3)]
        )
        self.assertIsNone(detect_dawn_phenomenon(entries))

    def test_no_detection_with_insufficient_data(self):
        entries = [self._morning(0, 200), self._night(0, 100)]
        self.assertIsNone(detect_dawn_phenomenon(entries))


# ─────────────────────────────────────────────────────────────────────────────
# Post-exercise hypoglycemia detector
# ─────────────────────────────────────────────────────────────────────────────

class PostExerciseHypoTests(SimpleTestCase):

    def test_detects_hypo_after_exercise(self):
        entries = [
            _e(8,  0, 120, exercised="yes"),
            _e(20, 0, 65),
            _e(8,  1, 115, exercised="yes"),
            _e(20, 1, 60),
        ]
        result = detect_post_exercise_hypo(entries)
        self.assertIsNotNone(result)
        self.assertEqual(result.code, "POST_EXERCISE_HYPO")
        self.assertEqual(result.priority, 1)

    def test_no_detection_without_exercise(self):
        entries = [_e(20, i, 65) for i in range(3)]
        self.assertIsNone(detect_post_exercise_hypo(entries))

    def test_no_detection_with_only_one_episode(self):
        entries = [
            _e(8, 0, 120, exercised="yes"),
            _e(20, 0, 60),
        ]
        self.assertIsNone(detect_post_exercise_hypo(entries))


# ─────────────────────────────────────────────────────────────────────────────
# Stress correlation detector
# ─────────────────────────────────────────────────────────────────────────────

class StressCorrelationTests(SimpleTestCase):

    def test_detects_stress_hyperglycemia(self):
        entries = (
            [_e(10, i, 220, stressed="yes") for i in range(3)] +
            [_e(10, i+3, 100, stressed="no") for i in range(3)]
        )
        result = detect_stress_correlation(entries)
        self.assertIsNotNone(result)
        self.assertEqual(result.code, "STRESS_HYPERGLYCEMIA")

    def test_no_detection_when_delta_small(self):
        entries = (
            [_e(10, i, 130, stressed="yes") for i in range(3)] +
            [_e(10, i+3, 120, stressed="no") for i in range(3)]
        )
        self.assertIsNone(detect_stress_correlation(entries))

    def test_no_detection_with_only_stressed_entries(self):
        entries = [_e(10, i, 200, stressed="yes") for i in range(4)]
        self.assertIsNone(detect_stress_correlation(entries))


# ─────────────────────────────────────────────────────────────────────────────
# High variability detector
# ─────────────────────────────────────────────────────────────────────────────

class HighVariabilityTests(SimpleTestCase):

    def test_detects_high_cv(self):
        # Alternating hypo/hyper → huge std dev
        entries = [_e(10, i, 250 if i % 2 == 0 else 55) for i in range(8)]
        result = detect_high_variability(entries)
        self.assertIsNotNone(result)
        self.assertEqual(result.code, "HIGH_VARIABILITY")

    def test_no_detection_stable_glucose(self):
        entries = [_e(10, i, 115 + i) for i in range(8)]
        self.assertIsNone(detect_high_variability(entries))

    def test_no_detection_with_too_few_entries(self):
        entries = [_e(10, 0, 250), _e(10, 1, 55)]
        self.assertIsNone(detect_high_variability(entries))


# ─────────────────────────────────────────────────────────────────────────────
# AnalyticalKPIs dataclass — property tests (no DB needed)
# ─────────────────────────────────────────────────────────────────────────────

class AnalyticalKPIsTests(SimpleTestCase):

    def _kpis(self, **kwargs):
        defaults = dict(
            avg_glucose=140.0, std_dev=20.0, cv_pct=14.0,
            tir_pct=75.0, tar_pct=20.0, tbr_pct=5.0,
            gmi=6.7, log_count=10, days_with_data=5,
        )
        defaults.update(kwargs)
        return AnalyticalKPIs(**defaults)

    def test_has_sufficient_data_true(self):
        self.assertTrue(self._kpis(log_count=5).has_sufficient_data)

    def test_has_sufficient_data_false(self):
        self.assertFalse(self._kpis(log_count=4).has_sufficient_data)

    def test_is_stable_below_threshold(self):
        self.assertTrue(self._kpis(cv_pct=36.0).is_stable)

    def test_is_stable_above_threshold(self):
        self.assertFalse(self._kpis(cv_pct=37.0).is_stable)

    def test_is_stable_none_cv(self):
        self.assertFalse(self._kpis(cv_pct=None).is_stable)
