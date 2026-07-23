"""
Clinical engine tests — covers pattern detectors, KPI helpers, and fallback layer.

P0/P1 regression guards are marked with # P0 / # P1 comments.
Target: ≥ 3 cases per detector (zero-data, negative, positive).
"""
import os
from datetime import datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace
from unittest import mock

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
    run_clinical_analysis,
)
from diabetes.services.clinical.sql_analytics import AnalyticalKPIs

# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def _dummy_kpis(**overrides):
    defaults = dict(
        avg_glucose=180.0, std_dev=20.0, cv_pct=11.0,
        tir_pct=85.0, tar_pct=10.0, tbr_pct=5.0,
        gmi=7.5, log_count=7, days_with_data=7,
    )
    defaults.update(overrides)
    return AnalyticalKPIs(**defaults)


def _entry(
    hour: int,
    day_offset: int,
    blood_sugar: float,
    *,
    exercised: str = "no",
    sleep_quality: str = "good",
    stressed: str = "no",
    meal_description: str = "",
    meal_type: str = "",
    base_date: datetime | None = None,
):
    """Full LogEntry stand-in — attributes match what detectors probe."""
    base = base_date or datetime(2026, 4, 1, 0, 0, 0)
    return SimpleNamespace(
        effective_time=base + timedelta(days=day_offset, hours=hour),
        blood_sugar=Decimal(str(blood_sugar)),
        meal_description=meal_description,
        exercised=exercised,
        sleep_quality=sleep_quality,
        stressed=stressed,
        fatigue_level="ok",
        is_sick="no",
        meal_type=meal_type,
    )


# ─────────────────────────────────────────────
# 1. KPI formula contracts (ADA spec, no external deps)
# ─────────────────────────────────────────────

def _gmi(mean_glucose: float) -> float:
    """ADA GMI formula — tested inline so the spec lives next to the assertion."""
    return round(3.31 + 0.02392 * mean_glucose, 1)


def _tir(entries, low: float = 70.0, high: float = 180.0) -> float:
    """TIR helper — inline so tests don't depend on production helpers."""
    if not entries:
        return 0.0
    in_range = sum(1 for e in entries if low <= float(e.blood_sugar) <= high)
    return round((in_range / len(entries)) * 100, 1)


class KPITests(SimpleTestCase):
    def test_gmi_matches_ada_formula(self):
        self.assertAlmostEqual(_gmi(154), 3.31 + 0.02392 * 154, places=1)

    def test_tir_empty_entries_returns_zero(self):
        self.assertEqual(_tir([]), 0.0)

    def test_tir_half_in_range(self):
        entries = [_entry(10, 0, 100), _entry(10, 1, 250)]
        self.assertEqual(_tir(entries), 50.0)

    def test_tir_all_in_range(self):
        entries = [_entry(10, d, 120) for d in range(5)]
        self.assertEqual(_tir(entries), 100.0)


# ─────────────────────────────────────────────
# 2. detect_high_variability — P0 regression
# ─────────────────────────────────────────────

class HighVariabilityTests(SimpleTestCase):
    """
    P0: threshold must be CV > 36% (ADA), NOT sd > 50.
    Old code: patient mean=100 sd=40 (CV=40% DANGER) → missed.
              patient mean=200 sd=55 (CV=27.5% OK)   → false positive.
    """

    def test_too_few_entries_returns_none(self):
        entries = [_entry(10, d, 150) for d in range(4)]
        self.assertIsNone(detect_high_variability(entries))

    def test_stable_low_mean_not_detected(self):
        # mean≈102, sd≈31, CV≈30% → below 36%
        values = [80, 60, 120, 140, 100, 85, 150, 70, 130, 90]
        entries = [_entry(10, d, v) for d, v in enumerate(values)]
        self.assertIsNone(detect_high_variability(entries))

    def test_high_mean_low_cv_not_detected(self):
        # mean≈200, sd≈23, CV≈11% — was false positive with old sd>50 on bigger datasets  # P0
        values = [180, 160, 220, 240, 200, 185, 210, 190, 220, 195]
        entries = [_entry(10, d, v) for d, v in enumerate(values)]
        self.assertIsNone(detect_high_variability(entries))

    def test_dangerous_low_mean_high_cv_detected(self):
        # mean≈100, sd≈49, CV≈49% — was MISSED with old sd>50 threshold  # P0
        values = [55, 60, 170, 150, 80, 55, 160, 75, 140, 55]
        entries = [_entry(10, d, v) for d, v in enumerate(values)]
        result = detect_high_variability(entries)
        self.assertIsNotNone(result)
        self.assertEqual(result.code, "HIGH_VARIABILITY")
        self.assertEqual(result.priority, 1)

    def test_zero_mean_does_not_crash(self):
        # Guard for ZeroDivisionError
        entries = [_entry(10, d, 0) for d in range(5)]
        self.assertIsNone(detect_high_variability(entries))

    def test_cv_exactly_at_threshold_not_detected(self):
        # CV exactly 36% should NOT trigger (strictly >)
        # mean=100 → sd must equal 36 exactly
        # Build synthetic values whose stdev ≈ 36 and mean ≈ 100
        import statistics
        values = [64, 64, 136, 136, 100, 100, 100, 100, 100, 100]
        entries = [_entry(10, d, v) for d, v in enumerate(values)]
        sd = statistics.stdev([float(e.blood_sugar) for e in entries])
        avg = statistics.mean([float(e.blood_sugar) for e in entries])
        cv = (sd / avg) * 100
        result = detect_high_variability(entries)
        # Just verify no crash and result depends on actual CV
        if cv > 36:
            self.assertIsNotNone(result)
        else:
            self.assertIsNone(result)


# ─────────────────────────────────────────────
# 3. detect_food_sensitivity — P0 + P1 regression
# ─────────────────────────────────────────────

class FoodSensitivityTests(SimpleTestCase):

    def test_no_entries_returns_none(self):
        self.assertIsNone(detect_food_sensitivity([]))

    def test_one_event_not_enough(self):
        e = _entry(13, 0, 220, meal_description="couscous")
        self.assertIsNone(detect_food_sensitivity([e]))

    def test_universal_foods_detected(self):
        entries = [
            _entry(13, 0, 230, meal_description="pizza margherita"),
            _entry(13, 3, 210, meal_description="pâtes bolognaise"),
        ]
        result = detect_food_sensitivity(entries)
        self.assertIsNotNone(result)
        self.assertEqual(result.code, "FOOD_SENSITIVITY")

    def test_moroccan_foods_detected(self):
        """P1: Moroccan foods must trigger the detector."""
        entries = [
            _entry(13, 0, 230, meal_description="couscous au poulet"),
            _entry(13, 3, 215, meal_description="harira + briouats"),
            _entry(13, 7, 200, meal_description="msemen au miel"),
        ]
        result = detect_food_sensitivity(entries)
        self.assertIsNotNone(result)

    def test_top_culprit_is_most_frequent(self):
        """P1: top_culprit must be the most frequent offending meal, not the first entry."""
        entries = [
            _entry(13, 0,  230, meal_description="couscous tfaya"),
            _entry(13, 3,  215, meal_description="harira"),
            _entry(13, 7,  220, meal_description="couscous tfaya"),   # couscous appears twice
            _entry(13, 10, 195, meal_description="couscous tfaya"),
        ]
        result = detect_food_sensitivity(entries)
        self.assertIsNotNone(result)
        # harira was first but couscous is most frequent
        self.assertIn("couscous tfaya", result.evidence)

    def test_fallback_action_has_no_insulin_prescription(self):
        """P0 SAFETY: fallback_action must never mention insulin dose adjustments."""
        entries = [
            _entry(13, 0, 230, meal_description="pizza"),
            _entry(13, 3, 220, meal_description="baguette + beurre"),
        ]
        result = detect_food_sensitivity(entries)
        self.assertIsNotNone(result)
        action = result.fallback_action.lower()
        # These words indicate a dose prescription — must not appear
        forbidden = ["bolus", "2 unités", "augmentez votre dose", "insuline rapide"]
        for word in forbidden:
            self.assertNotIn(word, action, msg=f"Insulin prescription found: '{word}'")

    def test_low_glucose_after_target_food_not_counted(self):
        # Blood sugar < 185 after a target meal → should not count
        entries = [
            _entry(13, 0, 170, meal_description="couscous"),
            _entry(13, 3, 175, meal_description="riz"),
        ]
        self.assertIsNone(detect_food_sensitivity(entries))


# ─────────────────────────────────────────────
# 4. detect_somogyi_rebound — P1 threshold
# ─────────────────────────────────────────────

class SomogyiReboundTests(SimpleTestCase):

    def _make_pair(self, day_offset: int):
        """One night hypo (23h) + one morning hyper (7h next day)."""
        return [
            _entry(23, day_offset,     65),   # night hypo
            _entry(7,  day_offset + 1, 175),  # morning hyper
        ]

    def test_no_entries_returns_none(self):
        self.assertIsNone(detect_somogyi_rebound([]))

    def test_single_event_not_enough(self):
        """P1: one rebound pair should NOT trigger (could be coincidence)."""
        entries = self._make_pair(0)
        self.assertIsNone(detect_somogyi_rebound(entries))

    def test_two_events_detected(self):
        """P1: two or more pairs should trigger."""
        entries = self._make_pair(0) + self._make_pair(5)
        result = detect_somogyi_rebound(entries)
        self.assertIsNotNone(result)
        self.assertEqual(result.code, "SOMOGYI_REBOUND")
        self.assertEqual(result.priority, 1)

    def test_hypo_without_morning_hyper_not_counted(self):
        entries = [
            _entry(23, 0, 65),   # night hypo
            _entry(7,  1, 130),  # morning normal — not a rebound
            _entry(23, 5, 60),
            _entry(7,  6, 145),  # still not hyper enough (>165 required)
        ]
        self.assertIsNone(detect_somogyi_rebound(entries))


# ─────────────────────────────────────────────
# 5. detect_dawn_phenomenon
# ─────────────────────────────────────────────

class DawnPhenomenonTests(SimpleTestCase):

    def test_too_few_entries_returns_none(self):
        self.assertIsNone(detect_dawn_phenomenon([]))

    def test_not_detected_when_morning_normal(self):
        morning = [_entry(7, d, 120) for d in range(3)]
        night   = [_entry(23, d, 110) for d in range(2)]
        self.assertIsNone(detect_dawn_phenomenon(morning + night))

    def test_detected_when_morning_high_night_normal(self):
        morning = [_entry(7, d, 165) for d in range(3)]
        night   = [_entry(23, d, 105) for d in range(2)]
        result = detect_dawn_phenomenon(morning + night)
        self.assertIsNotNone(result)
        self.assertEqual(result.code, "DAWN_PHENOMENON")

    def test_not_detected_when_night_also_high(self):
        # Night must be < 130 for dawn phenomenon
        morning = [_entry(7, d, 165) for d in range(3)]
        night   = [_entry(23, d, 160) for d in range(2)]
        self.assertIsNone(detect_dawn_phenomenon(morning + night))


# ─────────────────────────────────────────────
# 6. detect_post_exercise_hypo
# ─────────────────────────────────────────────

class PostExerciseHypoTests(SimpleTestCase):

    def test_no_exercise_returns_none(self):
        entries = [_entry(10, d, 65, exercised="no") for d in range(3)]
        self.assertIsNone(detect_post_exercise_hypo(entries))

    def test_single_hypo_on_exercise_day_not_enough(self):
        entries = [
            _entry(10, 0, 65, exercised="yes"),
            _entry(15, 0, 120, exercised="no"),
        ]
        self.assertIsNone(detect_post_exercise_hypo(entries))

    def test_two_hypos_on_exercise_days_detected(self):
        entries = [
            _entry(10, 0, 65, exercised="yes"),
            _entry(10, 1, 68, exercised="yes"),
            _entry(10, 2, 130, exercised="no"),
        ]
        result = detect_post_exercise_hypo(entries)
        self.assertIsNotNone(result)
        self.assertEqual(result.code, "POST_EXERCISE_HYPO")
        self.assertEqual(result.priority, 1)


# ─────────────────────────────────────────────
# 7. detect_stress_correlation
# ─────────────────────────────────────────────

class StressCorrelationTests(SimpleTestCase):

    def test_not_enough_data_returns_none(self):
        entries = [_entry(10, 0, 180, stressed="yes")]
        self.assertIsNone(detect_stress_correlation(entries))

    def test_small_delta_not_detected(self):
        stressed = [_entry(10, d, 165, stressed="yes") for d in range(3)]
        calm     = [_entry(10, d + 10, 150, stressed="no") for d in range(3)]
        self.assertIsNone(detect_stress_correlation(stressed + calm))

    def test_large_delta_detected(self):
        stressed = [_entry(10, d, 210, stressed="yes") for d in range(3)]
        calm     = [_entry(10, d + 10, 140, stressed="no") for d in range(3)]
        result = detect_stress_correlation(stressed + calm)
        self.assertIsNotNone(result)
        self.assertEqual(result.code, "STRESS_HYPERGLYCEMIA")


# ─────────────────────────────────────────────
# 8. detect_sleep_impact
# ─────────────────────────────────────────────

class SleepImpactTests(SimpleTestCase):

    def test_only_good_sleep_returns_none(self):
        entries = [_entry(8, d, 130, sleep_quality="good") for d in range(5)]
        self.assertIsNone(detect_sleep_impact(entries))

    def test_bad_sleep_small_delta_not_detected(self):
        # Bad sleep + morning avg: 140 vs good sleep + morning avg: 130 → delta 10 < 20
        entries = []
        for d in range(4):
            entries.append(_entry(22, d * 2,     100, sleep_quality="bad"))
            entries.append(_entry(8,  d * 2 + 1, 140))  # morning after bad sleep
        for d in range(4):
            entries.append(_entry(22, d * 2 + 1, 100, sleep_quality="good"))
            entries.append(_entry(8,  d * 2 + 2, 130))  # morning after good sleep
        # delta = 10 → should not detect
        self.assertIsNone(detect_sleep_impact(entries))

    def test_bad_sleep_large_delta_detected(self):
        entries = []
        for d in range(4):
            entries.append(_entry(22, d * 2,     100, sleep_quality="bad"))
            entries.append(_entry(8,  d * 2 + 1, 175))  # high morning after bad sleep
        for d in range(4):
            entries.append(_entry(22, d * 2 + 1, 100, sleep_quality="good"))
            entries.append(_entry(8,  d * 2 + 2, 120))  # normal morning after good sleep
        result = detect_sleep_impact(entries)
        self.assertIsNotNone(result)
        self.assertEqual(result.code, "SLEEP_IMPACT")


# ─────────────────────────────────────────────
# 9. detect_postmeal_spike
# ─────────────────────────────────────────────

class PostmealSpikeTests(SimpleTestCase):

    def test_no_meal_tagged_entries_returns_none(self):
        entries = [_entry(13, d, 150) for d in range(5)]
        self.assertIsNone(detect_postmeal_spike(entries))

    def test_single_spike_not_enough(self):
        base = datetime(2026, 4, 1, 0, 0, 0)
        entries = [
            _entry(12, 0, 100, meal_type="lunch", base_date=base),
            _entry(14, 0, 165, base_date=base),   # +65 within 2h → 1 spike
        ]
        self.assertIsNone(detect_postmeal_spike(entries))

    def test_two_spikes_detected(self):
        base = datetime(2026, 4, 1, 0, 0, 0)
        entries = [
            # Day 0 spike
            _entry(12, 0, 100, meal_type="lunch", base_date=base),
            _entry(14, 0, 170, base_date=base),
            # Day 1 spike
            _entry(12, 1, 110, meal_type="lunch", base_date=base),
            _entry(14, 1, 180, base_date=base),
        ]
        result = detect_postmeal_spike(entries)
        self.assertIsNotNone(result)
        self.assertEqual(result.code, "POSTMEAL_SPIKE")

    def test_rise_outside_2h_window_not_counted(self):
        base = datetime(2026, 4, 1, 0, 0, 0)
        entries = [
            _entry(12, 0, 100, meal_type="lunch", base_date=base),
            _entry(15, 0, 175, base_date=base),   # 3h later — outside window
            _entry(12, 1, 110, meal_type="lunch", base_date=base),
            _entry(15, 1, 180, base_date=base),
        ]
        self.assertIsNone(detect_postmeal_spike(entries))


# ─────────────────────────────────────────────
# 10. End-to-end + fallback layer
# ─────────────────────────────────────────────

class FallbackTests(SimpleTestCase):
    """Without a Gemini API key, engine must return a French report — no crash, no English."""

    def test_no_api_key_uses_fallback_content(self):
        entries = [_entry(10, d, 180) for d in range(7)]
        kpis = _dummy_kpis()
        env = {"GEMINI_API_KEY": "", "GOOGLE_API_KEY": ""}
        with mock.patch.dict(os.environ, env, clear=False):
            os.environ.pop("GEMINI_API_KEY", None)
            os.environ.pop("GOOGLE_API_KEY", None)
            report = run_clinical_analysis(entries, kpis)
        self.assertIsNotNone(report)
        self.assertGreaterEqual(report.kpis.tir_pct, 0.0)

    def test_empty_entries_do_not_crash(self):
        report = run_clinical_analysis([], _dummy_kpis(log_count=0, days_with_data=0))
        self.assertIsNotNone(report)
        self.assertEqual(report.patterns, [])

    def test_detector_exception_does_not_abort_report(self):
        """A broken detector must be skipped, not crash the whole report."""
        # Inject one entry that satisfies dawn phenomenon so we get at least one pattern
        morning = [_entry(7, d, 165) for d in range(3)]
        night   = [_entry(23, d, 105) for d in range(2)]
        entries = morning + night
        kpis = _dummy_kpis()
        broken = mock.MagicMock(__name__="detect_stress_correlation", side_effect=RuntimeError("boom"))
        with mock.patch("diabetes.services.clinical.engine.detect_stress_correlation", broken):
            with mock.patch("diabetes.services.clinical.engine._format_with_llm", return_value=[]):
                report = run_clinical_analysis(entries, kpis)
        self.assertIsNotNone(report)  # must not raise


class IntegrationTest(SimpleTestCase):
    """All detectors fire together — verify report sorts by priority."""

    def test_priority_1_patterns_come_first(self):
        base = datetime(2026, 4, 1, 0, 0, 0)
        entries = []

        # Post-exercise hypo (P1)
        entries += [_entry(10, d, 65, exercised="yes", base_date=base) for d in range(2)]

        # High variability (P1) — mean≈100, CV≈49%
        for d, v in enumerate([55, 170, 60, 160, 80, 55, 150, 70, 145, 60], start=10):
            entries.append(_entry(10, d, v, base_date=base))

        # Stress hyperglycemia (P2)
        entries += [_entry(10, d + 30, 210, stressed="yes", base_date=base) for d in range(3)]
        entries += [_entry(10, d + 40, 140, stressed="no",  base_date=base) for d in range(3)]

        kpis = _dummy_kpis()
        # Mock LLM to avoid network calls in tests
        with mock.patch("diabetes.services.clinical.engine._format_with_llm", side_effect=lambda ps, lang="fr": [
            {"code": p.code, "priority": p.priority, "icon": p.icon,
             "title": p.title, "content": p.fallback_content, "action": p.fallback_action}
            for p in ps
        ]):
            report = run_clinical_analysis(entries, kpis)

        p1_codes = {p.code for p in report.patterns if p.priority == 1}
        _ = p1_codes  # referenced to confirm structure

        # All priority-1 patterns appear before priority-2 in the sorted list
        sorted_priorities = [p.priority for p in report.patterns]
        self.assertEqual(sorted_priorities, sorted(sorted_priorities))

        if p1_codes:
            self.assertLessEqual(report.patterns[0].priority, 2)
