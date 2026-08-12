"""GRI plus safe compatibility-observation tests.

The GRI formula tests remain independent of clinical eligibility. Legacy fatigue
and illness tests intentionally assert the current observation-only contract:
explicit positive context may be summarized descriptively, while historical
``ok``/``no`` values are never treated as a synthetic control cohort.
"""

from datetime import datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace

from django.test import SimpleTestCase

from diabetes.services.clinical.engine import (
    detect_fatigue_correlation,
    detect_illness_impact,
)
from diabetes.services.clinical.sql_analytics import (
    AnalyticalKPIs,
    _compute_gri,
    gri_label_fr,
    gri_zone,
)


def _kpis(**overrides):
    defaults = dict(
        avg_glucose=150.0,
        std_dev=30.0,
        cv_pct=20.0,
        tir_pct=65.0,
        tar_pct=25.0,
        tbr_pct=5.0,
        gmi=7.0,
        log_count=10,
        days_with_data=5,
        gri=None,
        gri_zone=None,
        gri_label=None,
    )
    defaults.update(overrides)
    return AnalyticalKPIs(**defaults)


def _entry(
    hour: int,
    day_offset: int,
    blood_sugar: float,
    *,
    fatigue_level: str = "",
    is_sick: str = "",
    base_date: datetime | None = None,
):
    base = base_date or datetime(2026, 4, 1, 0, 0, 0)
    return SimpleNamespace(
        effective_time=base + timedelta(days=day_offset, hours=hour),
        blood_sugar=Decimal(str(blood_sugar)),
        fatigue_level=fatigue_level,
        is_sick=is_sick,
        exercised="",
        sleep_quality="",
        stressed="",
        meal_description="",
        meal_type="",
    )


class ComputeGriTests(SimpleTestCase):
    def test_all_zeros_returns_zero(self):
        stats = {
            "vlow_pct": 0,
            "low_pct": 0,
            "vhigh_pct": 0,
            "high_pct": 0,
            "log_count": 10,
        }
        self.assertEqual(_compute_gri(stats), 0.0)

    def test_known_values_formula(self):
        stats = {
            "vlow_pct": 2,
            "low_pct": 3,
            "vhigh_pct": 5,
            "high_pct": 10,
            "log_count": 20,
        }
        self.assertAlmostEqual(_compute_gri(stats), 29.2, places=1)

    def test_formula_is_independent_of_reading_count(self):
        stats = {
            "vlow_pct": 10,
            "low_pct": 5,
            "vhigh_pct": 10,
            "high_pct": 20,
            "log_count": 4,
        }
        self.assertEqual(_compute_gri(stats), 74.0)

    def test_score_capped_at_100(self):
        stats = {
            "vlow_pct": 20,
            "low_pct": 10,
            "vhigh_pct": 20,
            "high_pct": 10,
            "log_count": 50,
        }
        self.assertLessEqual(_compute_gri(stats), 100.0)

    def test_only_vlow_component(self):
        stats = {
            "vlow_pct": 10,
            "low_pct": 0,
            "vhigh_pct": 0,
            "high_pct": 0,
            "log_count": 10,
        }
        self.assertAlmostEqual(_compute_gri(stats), 30.0, places=1)

    def test_only_high_component(self):
        stats = {
            "vlow_pct": 0,
            "low_pct": 0,
            "vhigh_pct": 0,
            "high_pct": 25,
            "log_count": 10,
        }
        self.assertAlmostEqual(_compute_gri(stats), 20.0, places=1)

    def test_missing_keys_treated_as_zero(self):
        self.assertEqual(_compute_gri({"log_count": 10}), 0.0)


class GriZoneTests(SimpleTestCase):
    def test_none_score_returns_none(self):
        self.assertIsNone(gri_zone(None))

    def test_zone_a_zero(self):
        self.assertEqual(gri_zone(0.0), "A")

    def test_zone_a_boundary(self):
        self.assertEqual(gri_zone(20.0), "A")

    def test_zone_b_lower(self):
        self.assertEqual(gri_zone(20.1), "B")

    def test_zone_b_boundary(self):
        self.assertEqual(gri_zone(40.0), "B")

    def test_zone_c_lower(self):
        self.assertEqual(gri_zone(40.1), "C")

    def test_zone_c_boundary(self):
        self.assertEqual(gri_zone(60.0), "C")

    def test_zone_d_lower(self):
        self.assertEqual(gri_zone(60.1), "D")

    def test_zone_d_boundary(self):
        self.assertEqual(gri_zone(80.0), "D")

    def test_zone_e_lower(self):
        self.assertEqual(gri_zone(80.1), "E")

    def test_zone_e_max(self):
        self.assertEqual(gri_zone(100.0), "E")


class GriLabelFrTests(SimpleTestCase):
    def test_none_returns_none(self):
        self.assertIsNone(gri_label_fr(None))

    def test_all_zones_have_labels(self):
        for zone in ("A", "B", "C", "D", "E"):
            label = gri_label_fr(zone)
            self.assertIsNotNone(label, f"Zone {zone} has no label")
            assert label is not None
            self.assertGreater(len(label), 0)

    def test_zone_a_label_positive(self):
        label = gri_label_fr("A")
        assert label is not None
        self.assertIn("excellent", label.lower())

    def test_unknown_zone_returns_none(self):
        self.assertIsNone(gri_label_fr("Z"))


class AnalyticalKPIsGriFieldsTests(SimpleTestCase):
    def test_gri_fields_default_to_none(self):
        kpis = _kpis()
        self.assertIsNone(kpis.gri)
        self.assertIsNone(kpis.gri_zone)
        self.assertIsNone(kpis.gri_label)

    def test_gri_fields_accept_values(self):
        kpis = _kpis(gri=29.2, gri_zone="B", gri_label="Bon contrôle glycémique")
        self.assertAlmostEqual(kpis.gri, 29.2, places=1)
        self.assertEqual(kpis.gri_zone, "B")
        self.assertEqual(kpis.gri_label, "Bon contrôle glycémique")


class FatigueObservationCompatibilityTests(SimpleTestCase):
    def test_no_entries_returns_none(self):
        self.assertIsNone(detect_fatigue_correlation([]))

    def test_requires_three_explicit_positive_observations(self):
        entries = [
            _entry(10, 0, 200, fatigue_level="tired"),
            _entry(10, 1, 210, fatigue_level="tired"),
            _entry(10, 2, 130, fatigue_level="ok"),
        ]
        self.assertIsNone(detect_fatigue_correlation(entries))

    def test_repeated_explicit_fatigue_is_descriptive_only(self):
        entries = [
            _entry(10, 0, 200, fatigue_level="tired"),
            _entry(10, 1, 205, fatigue_level="tired"),
            _entry(10, 2, 210, fatigue_level="tired"),
            _entry(10, 10, 130, fatigue_level="ok"),
            _entry(10, 11, 135, fatigue_level="ok"),
            _entry(10, 12, 140, fatigue_level="ok"),
        ]
        result = detect_fatigue_correlation(entries)
        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result.code, "GLUCOSE_WITH_RECORDED_FATIGUE")
        self.assertEqual(result.priority, 3)
        self.assertIn("médiane de la fenêtre", result.evidence)
        self.assertNotIn("jours normaux", result.evidence.lower())
        self.assertIn("ne démontre pas une cause", result.evidence)
        self.assertNotIn("insuline", result.fallback_action.lower())

    def test_historical_ok_values_do_not_create_a_required_control_group(self):
        entries = [
            _entry(10, 0, 180, fatigue_level="tired"),
            _entry(10, 1, 175, fatigue_level="tired"),
            _entry(10, 2, 170, fatigue_level="tired"),
        ]
        self.assertIsNotNone(detect_fatigue_correlation(entries))


class IllnessObservationCompatibilityTests(SimpleTestCase):
    def test_no_entries_returns_none(self):
        self.assertIsNone(detect_illness_impact([]))

    def test_requires_three_explicit_positive_observations(self):
        entries = [
            _entry(10, 0, 250, is_sick="yes"),
            _entry(10, 1, 240, is_sick="yes"),
            _entry(10, 2, 130, is_sick="no"),
        ]
        self.assertIsNone(detect_illness_impact(entries))

    def test_repeated_explicit_illness_is_descriptive_only(self):
        entries = [
            _entry(10, 0, 250, is_sick="yes"),
            _entry(10, 1, 245, is_sick="yes"),
            _entry(10, 2, 255, is_sick="yes"),
            _entry(10, 10, 130, is_sick="no"),
            _entry(10, 11, 135, is_sick="no"),
            _entry(10, 12, 140, is_sick="no"),
        ]
        result = detect_illness_impact(entries)
        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result.code, "GLUCOSE_WITH_RECORDED_ILLNESS")
        self.assertEqual(result.priority, 3)
        self.assertIn("médiane de la fenêtre", result.evidence)
        self.assertNotIn("jours sains", result.evidence.lower())
        self.assertIn("ne démontre pas une cause", result.evidence)
        self.assertGreater(len(result.title_darija), 0)

    def test_historical_no_values_do_not_create_a_required_control_group(self):
        entries = [
            _entry(10, 0, 220, is_sick="yes"),
            _entry(10, 1, 225, is_sick="yes"),
            _entry(10, 2, 230, is_sick="yes"),
        ]
        self.assertIsNotNone(detect_illness_impact(entries))


class GriEdgeCaseTests(SimpleTestCase):
    def test_zero_percentages_return_zero(self):
        stats = {
            "vlow_pct": 0,
            "low_pct": 0,
            "vhigh_pct": 0,
            "high_pct": 0,
            "log_count": 0,
        }
        self.assertEqual(_compute_gri(stats), 0.0)

    def test_gri_zero_maps_to_zone_a(self):
        self.assertEqual(gri_zone(0.0), "A")

    def test_gri_zone_a_label_is_not_none(self):
        self.assertIsNotNone(gri_label_fr("A"))

    def test_log_count_does_not_change_formula_result(self):
        base = {"vlow_pct": 1, "low_pct": 2, "vhigh_pct": 3, "high_pct": 4}
        self.assertEqual(
            _compute_gri({**base, "log_count": 4}),
            _compute_gri({**base, "log_count": 5}),
        )
