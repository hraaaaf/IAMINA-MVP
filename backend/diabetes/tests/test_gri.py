"""
GRI (Glycemia Risk Index) + fatigue/illness detector tests.

Covers:
  - _compute_gri: formula correctness, edge cases, cap at 100
  - gri_zone: all five zones A-E plus boundary values
  - gri_label_fr: French label mapping
  - detect_fatigue_correlation: trigger, no-trigger, insufficient data
  - detect_illness_impact: trigger (priority 2), escalation (priority 1),
      no-trigger, insufficient data
  - AnalyticalKPIs.gri / gri_zone / gri_label defaults
  - Empty logs → GRI = None / GRI score 0 → zone A
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

# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def _kpis(**overrides):
    defaults = dict(
        avg_glucose=150.0, std_dev=30.0, cv_pct=20.0,
        tir_pct=65.0, tar_pct=25.0, tbr_pct=5.0,
        gmi=7.0, log_count=10, days_with_data=5,
        gri=None, gri_zone=None, gri_label=None,
    )
    defaults.update(overrides)
    return AnalyticalKPIs(**defaults)


def _entry(
    hour: int,
    day_offset: int,
    blood_sugar: float,
    *,
    fatigue_level: str = "ok",
    is_sick: str = "no",
    base_date: datetime | None = None,
):
    base = base_date or datetime(2026, 4, 1, 0, 0, 0)
    return SimpleNamespace(
        effective_time=base + timedelta(days=day_offset, hours=hour),
        blood_sugar=Decimal(str(blood_sugar)),
        fatigue_level=fatigue_level,
        is_sick=is_sick,
        exercised="no",
        sleep_quality="good",
        stressed="no",
        meal_description="",
        meal_type="",
    )


# ─────────────────────────────────────────────
# 1. _compute_gri — formula correctness
# ─────────────────────────────────────────────

class ComputeGriTests(SimpleTestCase):

    def test_all_zeros_returns_zero(self):
        stats = {"vlow_pct": 0, "low_pct": 0, "vhigh_pct": 0, "high_pct": 0, "log_count": 10}
        result = _compute_gri(stats)
        self.assertEqual(result, 0.0)

    def test_known_values_formula(self):
        # GRI = 3.0×2 + 2.4×3 + 1.6×5 + 0.8×10 = 6 + 7.2 + 8 + 8 = 29.2
        stats = {"vlow_pct": 2, "low_pct": 3, "vhigh_pct": 5, "high_pct": 10, "log_count": 20}
        result = _compute_gri(stats)
        self.assertAlmostEqual(result, 29.2, places=1)

    def test_returns_none_if_fewer_than_5_readings(self):
        stats = {"vlow_pct": 10, "low_pct": 5, "vhigh_pct": 10, "high_pct": 20, "log_count": 4}
        self.assertIsNone(_compute_gri(stats))

    def test_score_capped_at_100(self):
        # Extreme values that would exceed 100
        stats = {"vlow_pct": 20, "low_pct": 10, "vhigh_pct": 20, "high_pct": 10, "log_count": 50}
        result = _compute_gri(stats)
        self.assertLessEqual(result, 100.0)

    def test_only_vlow_component(self):
        # GRI = 3.0 × 10 = 30.0
        stats = {"vlow_pct": 10, "low_pct": 0, "vhigh_pct": 0, "high_pct": 0, "log_count": 10}
        self.assertAlmostEqual(_compute_gri(stats), 30.0, places=1)

    def test_only_high_component(self):
        # GRI = 0.8 × 25 = 20.0
        stats = {"vlow_pct": 0, "low_pct": 0, "vhigh_pct": 0, "high_pct": 25, "log_count": 10}
        self.assertAlmostEqual(_compute_gri(stats), 20.0, places=1)

    def test_missing_keys_treated_as_zero(self):
        # Should not raise; missing keys default to 0
        stats = {"log_count": 10}
        result = _compute_gri(stats)
        self.assertEqual(result, 0.0)


# ─────────────────────────────────────────────
# 2. gri_zone — ADA consensus grid
# ─────────────────────────────────────────────

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


# ─────────────────────────────────────────────
# 3. gri_label_fr — French patient labels
# ─────────────────────────────────────────────

class GriLabelFrTests(SimpleTestCase):

    def test_none_returns_none(self):
        self.assertIsNone(gri_label_fr(None))

    def test_all_zones_have_labels(self):
        for zone in ("A", "B", "C", "D", "E"):
            label = gri_label_fr(zone)
            self.assertIsNotNone(label, f"Zone {zone} has no label")
            self.assertGreater(len(label), 0)

    def test_zone_a_label_positive(self):
        label = gri_label_fr("A")
        self.assertIn("excellent", label.lower())

    def test_unknown_zone_returns_none(self):
        self.assertIsNone(gri_label_fr("Z"))


# ─────────────────────────────────────────────
# 4. AnalyticalKPIs — GRI field defaults
# ─────────────────────────────────────────────

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


# ─────────────────────────────────────────────
# 5. detect_fatigue_correlation
# ─────────────────────────────────────────────

class FatigueCorrelationTests(SimpleTestCase):

    def test_no_entries_returns_none(self):
        self.assertIsNone(detect_fatigue_correlation([]))

    def test_insufficient_fatigue_days_returns_none(self):
        entries = [
            _entry(10, 0, 200, fatigue_level="tired"),   # only 1 fatigue day
            _entry(10, 1, 130, fatigue_level="ok"),
            _entry(10, 2, 140, fatigue_level="ok"),
        ]
        self.assertIsNone(detect_fatigue_correlation(entries))

    def test_insufficient_normal_days_returns_none(self):
        entries = [
            _entry(10, 0, 200, fatigue_level="tired"),
            _entry(10, 1, 210, fatigue_level="tired"),
            _entry(10, 2, 130, fatigue_level="ok"),   # only 1 normal day
        ]
        self.assertIsNone(detect_fatigue_correlation(entries))

    def test_small_delta_not_detected(self):
        # avg fatigue=155, avg normal=140 → delta=15 < 20
        entries = (
            [_entry(10, d, 155, fatigue_level="tired") for d in range(3)]
            + [_entry(10, d + 10, 140, fatigue_level="ok") for d in range(3)]
        )
        self.assertIsNone(detect_fatigue_correlation(entries))

    def test_large_delta_detected(self):
        # avg fatigue=200, avg normal=130 → delta=70 > 20
        entries = (
            [_entry(10, d, 200, fatigue_level="tired") for d in range(3)]
            + [_entry(10, d + 10, 130, fatigue_level="ok") for d in range(3)]
        )
        result = detect_fatigue_correlation(entries)
        self.assertIsNotNone(result)
        self.assertEqual(result.code, "FATIGUE_CORRELATION")
        self.assertEqual(result.priority, 2)

    def test_result_contains_delta_in_evidence(self):
        entries = (
            [_entry(10, d, 210, fatigue_level="exhausted") for d in range(3)]
            + [_entry(10, d + 10, 130, fatigue_level="ok") for d in range(3)]
        )
        result = detect_fatigue_correlation(entries)
        self.assertIsNotNone(result)
        # Evidence must mention the mg/dL values
        self.assertIn("mg/dL", result.evidence)


# ─────────────────────────────────────────────
# 6. detect_illness_impact
# ─────────────────────────────────────────────

class IllnessImpactTests(SimpleTestCase):

    def test_no_entries_returns_none(self):
        self.assertIsNone(detect_illness_impact([]))

    def test_insufficient_sick_days_returns_none(self):
        entries = [
            _entry(10, 0, 280, is_sick="yes"),   # only 1 sick day
            _entry(10, 1, 130, is_sick="no"),
            _entry(10, 2, 140, is_sick="no"),
        ]
        self.assertIsNone(detect_illness_impact(entries))

    def test_insufficient_healthy_days_returns_none(self):
        entries = [
            _entry(10, 0, 280, is_sick="yes"),
            _entry(10, 1, 270, is_sick="yes"),
            _entry(10, 2, 130, is_sick="no"),   # only 1 healthy day
        ]
        self.assertIsNone(detect_illness_impact(entries))

    def test_small_delta_not_detected(self):
        # avg sick=160, avg healthy=130 → delta=30 ≤ 40
        entries = (
            [_entry(10, d, 160, is_sick="yes") for d in range(3)]
            + [_entry(10, d + 10, 130, is_sick="no") for d in range(3)]
        )
        self.assertIsNone(detect_illness_impact(entries))

    def test_moderate_delta_detected_priority_2(self):
        # avg sick=200, avg healthy=130 → delta=70 > 40 but ≤ 80 → priority 2
        entries = (
            [_entry(10, d, 200, is_sick="yes") for d in range(3)]
            + [_entry(10, d + 10, 130, is_sick="no") for d in range(3)]
        )
        result = detect_illness_impact(entries)
        self.assertIsNotNone(result)
        self.assertEqual(result.code, "ILLNESS_IMPACT")
        self.assertEqual(result.priority, 2)

    def test_large_delta_escalates_to_priority_1(self):
        # avg sick=260, avg healthy=130 → delta=130 > 80 → priority 1
        entries = (
            [_entry(10, d, 260, is_sick="yes") for d in range(3)]
            + [_entry(10, d + 10, 130, is_sick="no") for d in range(3)]
        )
        result = detect_illness_impact(entries)
        self.assertIsNotNone(result)
        self.assertEqual(result.code, "ILLNESS_IMPACT")
        self.assertEqual(result.priority, 1)

    def test_evidence_contains_mg_dl(self):
        entries = (
            [_entry(10, d, 250, is_sick="yes") for d in range(3)]
            + [_entry(10, d + 10, 130, is_sick="no") for d in range(3)]
        )
        result = detect_illness_impact(entries)
        self.assertIsNotNone(result)
        self.assertIn("mg/dL", result.evidence)

    def test_darija_fields_present(self):
        entries = (
            [_entry(10, d, 260, is_sick="yes") for d in range(3)]
            + [_entry(10, d + 10, 130, is_sick="no") for d in range(3)]
        )
        result = detect_illness_impact(entries)
        self.assertIsNotNone(result)
        self.assertGreater(len(result.title_darija), 0)
        self.assertGreater(len(result.fallback_action_darija), 0)


# ─────────────────────────────────────────────
# 7. Empty logs / zero GRI edge cases
# ─────────────────────────────────────────────

class GriEdgeCaseTests(SimpleTestCase):

    def test_empty_logs_gri_is_none(self):
        """_compute_gri with log_count=0 returns None (insufficient data)."""
        stats = {"vlow_pct": 0, "low_pct": 0, "vhigh_pct": 0, "high_pct": 0, "log_count": 0}
        self.assertIsNone(_compute_gri(stats))

    def test_gri_zero_maps_to_zone_a(self):
        self.assertEqual(gri_zone(0.0), "A")

    def test_gri_zone_a_label_is_not_none(self):
        self.assertIsNotNone(gri_label_fr("A"))

    def test_gri_score_exactly_5_readings(self):
        """Minimum 5 readings boundary — should compute, not return None."""
        stats = {"vlow_pct": 0, "low_pct": 0, "vhigh_pct": 0, "high_pct": 0, "log_count": 5}
        self.assertIsNotNone(_compute_gri(stats))

    def test_gri_score_4_readings_returns_none(self):
        """4 readings is below threshold — must return None."""
        stats = {"vlow_pct": 0, "low_pct": 0, "vhigh_pct": 0, "high_pct": 0, "log_count": 4}
        self.assertIsNone(_compute_gri(stats))
