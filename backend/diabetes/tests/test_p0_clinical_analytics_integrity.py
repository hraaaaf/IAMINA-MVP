"""P0 regression tests for clinically sensitive analytics invariants."""

from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone


class GriIntegrityTests(TestCase):
    def test_original_paper_example_equals_79(self):
        """Klonoff et al. example: 5/10/15/20 in disjoint zones => GRI 79."""
        from diabetes.services.clinical.sql_analytics import _compute_gri

        score = _compute_gri(
            {
                "vlow_pct": 5.0,
                "low_pct": 10.0,
                "vhigh_pct": 15.0,
                "high_pct": 20.0,
            }
        )
        self.assertEqual(score, 79.0)

    def test_extreme_zones_are_not_double_counted(self):
        """Level-2 percentages must not be included again inside Level-1 inputs."""
        from diabetes.services.clinical.sql_analytics import _compute_gri

        score = _compute_gri(
            {
                "vlow_pct": 10.0,
                "low_pct": 0.0,
                "vhigh_pct": 10.0,
                "high_pct": 0.0,
            }
        )
        self.assertEqual(score, 46.0)

    def test_compute_kpis_does_not_publish_unvalidated_gri(self):
        """Sparse/manual readings cannot be presented as a validated CGM GRI."""
        from diabetes.models import LogEntry
        from diabetes.services.clinical.sql_analytics import compute_kpis

        user = User.objects.create_user(username="p0-gri-manual")
        ts = timezone.now() - timedelta(days=1)
        for value in (45, 60, 100, 220, 300):
            LogEntry.objects.create(
                patient=user,
                blood_sugar=value,
                logged_at=ts,
                source="manual",
            )

        kpis = compute_kpis(user.id)
        self.assertIsNone(kpis.gri)
        self.assertIsNone(kpis.gri_zone)
        self.assertIsNone(kpis.gri_label)


class DailyAverageSqlIntegrityTests(TestCase):
    def test_created_at_fallback_is_grouped_consistently(self):
        """Rows without logged_at must group by the same COALESCE expression selected."""
        from diabetes.models import LogEntry
        from diabetes.services.clinical.sql_analytics import compute_daily_averages

        user = User.objects.create_user(username="p0-daily-avg")
        LogEntry.objects.create(patient=user, blood_sugar=100, logged_at=None)
        LogEntry.objects.create(patient=user, blood_sugar=200, logged_at=None)

        rows = compute_daily_averages(user.id, days=1)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["entries"], 2)
        self.assertAlmostEqual(rows[0]["avg_glucose"], 150.0, places=1)
