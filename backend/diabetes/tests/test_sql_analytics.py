"""
Phase 8 — sql_analytics.compute_kpis unit tests
=================================================
5 canonical cases from the roadmap + bonus edge-cases.
All LLM calls are bypassed — pure SQL/Python logic only.

Cases covered:
  1. Empty DB             → all KPIs None, log_count=0
  2. Single entry         → avg set, gmi=None (< 5 entries required)
  3. All-in-range data    → TIR=100%, TAR=TBR=0%
  4. Spike data           → TAR > 0 (glucose > 180)
  5. Hypo data            → TBR > 0 (glucose < 70)
  + GMI computed at ≥ 5 entries
  + CV stability flag
  + gmi_confidence tiers
  + gmi_basis string
  + out-of-window entries excluded
  + custom target range respected
"""
from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone


class ComputeKpisTest(TestCase):
    """Core KPI computation via raw SQL (SQLite in test env)."""

    def setUp(self):
        # Unique username to avoid inter-test cache collisions (MISTAKES #13)
        self.user = User.objects.create_user(
            username=f"kpis_{self._testMethodName}", password="x"
        )

    def _add_entries(self, values: list[float], days_ago: int = 2):
        """Create LogEntry rows within the default 21-day window."""
        from diabetes.models import LogEntry

        ts = timezone.now() - timedelta(days=days_ago)
        for val in values:
            LogEntry.objects.create(patient=self.user, blood_sugar=val, logged_at=ts)

    # ── Case 1: empty DB ──────────────────────────────────────────────────────

    def test_empty_db_returns_zero_count(self):
        from diabetes.services.clinical.sql_analytics import compute_kpis

        kpis = compute_kpis(self.user.id)
        self.assertEqual(kpis.log_count, 0)
        self.assertIsNone(kpis.avg_glucose)
        self.assertIsNone(kpis.tir_pct)
        self.assertIsNone(kpis.gmi)
        self.assertFalse(kpis.has_sufficient_data)
        self.assertIsNone(kpis.gmi_confidence)

    def test_empty_db_gmi_basis(self):
        from diabetes.services.clinical.sql_analytics import compute_kpis

        kpis = compute_kpis(self.user.id)
        self.assertEqual(kpis.gmi_basis, "données insuffisantes")

    # ── Case 2: single entry ──────────────────────────────────────────────────

    def test_single_entry_avg_set_gmi_none(self):
        from diabetes.services.clinical.sql_analytics import compute_kpis

        self._add_entries([120.0])
        kpis = compute_kpis(self.user.id)
        self.assertEqual(kpis.log_count, 1)
        self.assertIsNotNone(kpis.avg_glucose)
        self.assertAlmostEqual(kpis.avg_glucose, 120.0, delta=1.0)
        # GMI requires ≥ 5 entries
        self.assertIsNone(kpis.gmi)
        self.assertIsNone(kpis.gmi_confidence)
        self.assertFalse(kpis.has_sufficient_data)

    def test_four_entries_still_no_gmi(self):
        from diabetes.services.clinical.sql_analytics import compute_kpis

        self._add_entries([100.0, 110.0, 120.0, 130.0])  # 4 < 5
        kpis = compute_kpis(self.user.id)
        self.assertEqual(kpis.log_count, 4)
        self.assertIsNone(kpis.gmi)

    # ── Case 3: all in range → TIR = 100% ────────────────────────────────────

    def test_all_in_range_tir_100(self):
        from diabetes.services.clinical.sql_analytics import compute_kpis

        self._add_entries([80.0, 100.0, 120.0, 140.0, 160.0, 175.0])
        kpis = compute_kpis(self.user.id)
        self.assertEqual(kpis.tir_pct, 100.0)
        self.assertEqual(kpis.tar_pct, 0.0)
        self.assertEqual(kpis.tbr_pct, 0.0)

    # ── Case 4: spike data → TAR > 0 ─────────────────────────────────────────

    def test_spike_entries_tar_nonzero(self):
        from diabetes.services.clinical.sql_analytics import compute_kpis

        # 4 in-range + 2 above 180
        self._add_entries([120.0, 130.0, 140.0, 150.0, 250.0, 310.0])
        kpis = compute_kpis(self.user.id)
        self.assertIsNotNone(kpis.tar_pct)
        self.assertGreater(kpis.tar_pct, 0.0)
        # ≈ 2/6 = 33.3%
        self.assertAlmostEqual(kpis.tar_pct, 33.3, delta=1.0)
        # No values below 70
        self.assertEqual(kpis.tbr_pct, 0.0)

    # ── Case 5: hypo data → TBR > 0 ──────────────────────────────────────────

    def test_hypo_entries_tbr_nonzero(self):
        from diabetes.services.clinical.sql_analytics import compute_kpis

        # 3 in-range + 2 below 70
        self._add_entries([120.0, 140.0, 150.0, 60.0, 55.0])
        kpis = compute_kpis(self.user.id)
        self.assertIsNotNone(kpis.tbr_pct)
        self.assertGreater(kpis.tbr_pct, 0.0)
        # ≈ 2/5 = 40%
        self.assertAlmostEqual(kpis.tbr_pct, 40.0, delta=1.0)
        # No values above 180
        self.assertEqual(kpis.tar_pct, 0.0)

    # ── GMI computed at ≥ 5 entries ───────────────────────────────────────────

    def test_gmi_computed_at_exactly_5_entries(self):
        from diabetes.services.clinical.sql_analytics import compute_kpis

        self._add_entries([120.0, 130.0, 140.0, 120.0, 130.0])  # avg = 128
        kpis = compute_kpis(self.user.id)
        self.assertEqual(kpis.log_count, 5)
        self.assertIsNotNone(kpis.gmi)
        self.assertTrue(kpis.has_sufficient_data)
        # ADA formula: 3.31 + 0.02392 * 128 ≈ 6.37
        expected_gmi = 3.31 + 0.02392 * 128.0
        self.assertAlmostEqual(kpis.gmi, expected_gmi, delta=0.3)

    # ── gmi_confidence tiers ──────────────────────────────────────────────────

    def test_gmi_confidence_low_with_5_entries(self):
        """5 entries → 'low' confidence (< 7 days and < 25 entries)."""
        from diabetes.services.clinical.sql_analytics import compute_kpis

        self._add_entries([120.0, 130.0, 140.0, 120.0, 130.0])
        kpis = compute_kpis(self.user.id)
        self.assertEqual(kpis.gmi_confidence, "low")

    def test_gmi_confidence_medium_with_25_entries(self):
        """25+ entries on same day → 'medium' (log_count ≥ 25, days < 14)."""
        from diabetes.services.clinical.sql_analytics import compute_kpis

        self._add_entries([120.0] * 25, days_ago=1)
        kpis = compute_kpis(self.user.id)
        self.assertEqual(kpis.log_count, 25)
        self.assertEqual(kpis.gmi_confidence, "medium")

    def test_gmi_confidence_none_below_5(self):
        from diabetes.services.clinical.sql_analytics import compute_kpis

        self._add_entries([120.0, 130.0])
        kpis = compute_kpis(self.user.id)
        self.assertIsNone(kpis.gmi_confidence)

    # ── CV stability ──────────────────────────────────────────────────────────

    def test_is_stable_for_low_variability_values(self):
        """Very narrow range → CV well below 36%."""
        from diabetes.services.clinical.sql_analytics import compute_kpis

        self._add_entries([120.0, 121.0, 119.0, 120.0, 122.0, 118.0, 120.0])
        kpis = compute_kpis(self.user.id)
        self.assertTrue(kpis.is_stable)

    def test_is_not_stable_for_high_variability(self):
        """Wide range → CV above 36%."""
        from diabetes.services.clinical.sql_analytics import compute_kpis

        self._add_entries([50.0, 300.0, 50.0, 300.0, 50.0, 300.0])
        kpis = compute_kpis(self.user.id)
        self.assertFalse(kpis.is_stable)

    # ── Out-of-window exclusion ───────────────────────────────────────────────

    def test_entries_outside_window_excluded(self):
        """Entries older than `days` must be ignored."""
        from diabetes.models import LogEntry
        from diabetes.services.clinical.sql_analytics import compute_kpis

        LogEntry.objects.create(
            patient=self.user,
            blood_sugar=250.0,
            logged_at=timezone.now() - timedelta(days=30),
        )
        kpis = compute_kpis(self.user.id, days=21)
        self.assertEqual(kpis.log_count, 0)
        self.assertIsNone(kpis.avg_glucose)

    def test_entries_just_inside_window_included(self):
        """Entry exactly 20 days ago must appear in a 21-day window."""
        from diabetes.models import LogEntry
        from diabetes.services.clinical.sql_analytics import compute_kpis

        LogEntry.objects.create(
            patient=self.user,
            blood_sugar=130.0,
            logged_at=timezone.now() - timedelta(days=20),
        )
        kpis = compute_kpis(self.user.id, days=21)
        self.assertEqual(kpis.log_count, 1)

    # ── Custom target range ───────────────────────────────────────────────────

    def test_custom_target_range_affects_tir(self):
        """With a narrow target (80–120), values at 140 are above range."""
        from diabetes.services.clinical.sql_analytics import compute_kpis

        self._add_entries([90.0, 100.0, 110.0, 90.0, 140.0, 150.0])
        kpis_default = compute_kpis(self.user.id, target_low=70.0, target_high=180.0)
        kpis_narrow  = compute_kpis(self.user.id, target_low=80.0, target_high=120.0)
        # With default range, all in [70–180] → TIR = 100%
        self.assertEqual(kpis_default.tir_pct, 100.0)
        # With narrow range, 140 and 150 are above → TIR < 100%
        self.assertLess(kpis_narrow.tir_pct, 100.0)

    # ── gmi_basis string ──────────────────────────────────────────────────────

    def test_gmi_basis_contains_count(self):
        from diabetes.services.clinical.sql_analytics import compute_kpis

        self._add_entries([120.0] * 8)
        kpis = compute_kpis(self.user.id)
        basis = kpis.gmi_basis
        self.assertIn("8", basis)          # count present
        self.assertIn("mesures", basis)    # unit label present

    # ── Isolation between patients ────────────────────────────────────────────

    def test_other_patient_entries_not_counted(self):
        """KPIs for user A must not include entries from user B."""
        from diabetes.models import LogEntry
        from diabetes.services.clinical.sql_analytics import compute_kpis

        other = User.objects.create_user(username="other_kpis", password="x")
        LogEntry.objects.create(
            patient=other,
            blood_sugar=250.0,
            logged_at=timezone.now() - timedelta(days=1),
        )
        kpis = compute_kpis(self.user.id)
        self.assertEqual(kpis.log_count, 0)
