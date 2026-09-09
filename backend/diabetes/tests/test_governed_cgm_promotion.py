import datetime as dt

from django.contrib.auth.models import User
from django.test import TestCase

from diabetes.models import CGMReadingRecord, CGMSensorSession
from diabetes.services.clinical.cgm_analytics import compute_verified_cgm_metrics
from diabetes.services.clinical.cgm_eligibility import assess_cgm_window
from diabetes.services.clinical.evidence_projection import project_public_kpis
from diabetes.services.clinical.sql_analytics import AnalyticalKPIs


class GovernedCgmPromotionTests(TestCase):
    def setUp(self):
        self.patient = User.objects.create_user(username="synthetic-analysis5-cgm")
        self.start = dt.datetime(2026, 1, 1, tzinfo=dt.UTC)
        self.end = self.start + dt.timedelta(days=14)
        self.session = CGMSensorSession.objects.create(
            patient=self.patient,
            source="linx",
            session_key="synthetic-a5-session",
            started_at=self.start,
            ended_at=self.end,
            expected_interval_minutes=60,
            timezone_name="UTC",
            end_reason=CGMSensorSession.EndReason.REPLACED,
        )

    def _raw_kpis(self) -> AnalyticalKPIs:
        return AnalyticalKPIs(
            avg_glucose=250.0,
            std_dev=99.0,
            cv_pct=99.0,
            tir_pct=0.0,
            tar_pct=100.0,
            tbr_pct=0.0,
            gmi=9.3,
            log_count=100,
            days_with_data=14,
            gri=88.0,
            gri_zone="E",
            gri_label="legacy",
            cgm_active_pct=100.0,
        )

    def _insert_complete_hourly_window(self):
        expected = 14 * 24 + 1
        rows = []
        for index in range(expected):
            if index % 10 == 0:
                glucose = 50
            elif index % 10 in (1, 2):
                glucose = 200
            else:
                glucose = 100
            rows.append(
                CGMReadingRecord(
                    patient=self.patient,
                    source="linx",
                    session=self.session,
                    recorded_at=self.start + dt.timedelta(hours=index),
                    glucose_mg_dl=glucose,
                    dedupe_key=f"analysis5:{index}",
                )
            )
        CGMReadingRecord.objects.bulk_create(rows)

    def test_verified_window_promotes_only_cgm_native_metrics(self):
        self._insert_complete_hourly_window()
        window = assess_cgm_window(
            patient_id=self.patient.id,
            window_start=self.start,
            window_end=self.end,
        )
        metrics = compute_verified_cgm_metrics(
            patient_id=self.patient.id,
            window_start=self.start,
            window_end=self.end,
        )
        projection = project_public_kpis(
            self._raw_kpis(),
            cgm_window=window,
            cgm_metrics=metrics,
        )

        self.assertTrue(window.verified)
        self.assertEqual(projection["tir_pct"], metrics.tir_pct)
        self.assertEqual(projection["tar_pct"], metrics.tar_pct)
        self.assertEqual(projection["tbr_pct"], metrics.tbr_pct)
        self.assertEqual(projection["cv_pct"], metrics.cv_pct)
        self.assertNotEqual(projection["tir_pct"], self._raw_kpis().tir_pct)
        self.assertNotEqual(projection["tar_pct"], self._raw_kpis().tar_pct)
        self.assertEqual(projection["cgm_metric_reading_count"], 337)

    def test_verified_cgm_metrics_match_independent_numeric_oracle(self):
        self._insert_complete_hourly_window()
        window = assess_cgm_window(
            patient_id=self.patient.id,
            window_start=self.start,
            window_end=self.end,
        )
        metrics = compute_verified_cgm_metrics(
            patient_id=self.patient.id,
            window_start=self.start,
            window_end=self.end,
        )

        self.assertTrue(window.verified)
        self.assertEqual(metrics.reading_count, 337)
        self.assertEqual(metrics.tir_pct, 69.7)
        self.assertEqual(metrics.tar_pct, 20.2)
        self.assertEqual(metrics.tbr_pct, 10.1)
        self.assertEqual(metrics.cv_pct, 39.3)
        self.assertEqual(
            round(metrics.tir_pct + metrics.tar_pct + metrics.tbr_pct, 1),
            100.0,
        )

    def test_cgm_target_boundaries_are_inclusive(self):
        values = [70, 180, 69, 181]
        for index, glucose in enumerate(values):
            CGMReadingRecord.objects.create(
                patient=self.patient,
                source="linx",
                session=self.session,
                recorded_at=self.start + dt.timedelta(hours=index),
                glucose_mg_dl=glucose,
                dedupe_key=f"analysis5-boundary:{index}",
            )

        metrics = compute_verified_cgm_metrics(
            patient_id=self.patient.id,
            window_start=self.start,
            window_end=self.end,
        )

        self.assertEqual(metrics.reading_count, 4)
        self.assertEqual(metrics.tir_pct, 50.0)
        self.assertEqual(metrics.tar_pct, 25.0)
        self.assertEqual(metrics.tbr_pct, 25.0)

    def test_gmi_and_gri_remain_fail_closed_after_valid_cgm_window(self):
        self._insert_complete_hourly_window()
        window = assess_cgm_window(
            patient_id=self.patient.id,
            window_start=self.start,
            window_end=self.end,
        )
        metrics = compute_verified_cgm_metrics(
            patient_id=self.patient.id,
            window_start=self.start,
            window_end=self.end,
        )
        projection = project_public_kpis(
            self._raw_kpis(),
            cgm_window=window,
            cgm_metrics=metrics,
        )

        self.assertTrue(window.verified)
        self.assertIsNone(projection["gmi"])
        self.assertIsNone(projection["gri"])
        self.assertIsNone(projection["gri_zone"])
        self.assertEqual(projection["gmi_basis"], "règle GMI non promue")

    def test_insufficient_window_keeps_normative_metrics_closed(self):
        for index in range(20):
            CGMReadingRecord.objects.create(
                patient=self.patient,
                source="linx",
                session=self.session,
                recorded_at=self.start + dt.timedelta(hours=index),
                glucose_mg_dl=100,
                dedupe_key=f"analysis5-low:{index}",
            )

        window = assess_cgm_window(
            patient_id=self.patient.id,
            window_start=self.start,
            window_end=self.end,
        )
        metrics = compute_verified_cgm_metrics(
            patient_id=self.patient.id,
            window_start=self.start,
            window_end=self.end,
        )
        projection = project_public_kpis(
            self._raw_kpis(),
            cgm_window=window,
            cgm_metrics=metrics,
        )

        self.assertFalse(window.verified)
        self.assertIsNone(projection["tir_pct"])
        self.assertIsNone(projection["tar_pct"])
        self.assertIsNone(projection["tbr_pct"])
        self.assertIsNone(projection["cv_pct"])

    def test_verified_window_without_cgm_metric_payload_stays_closed(self):
        self._insert_complete_hourly_window()
        window = assess_cgm_window(
            patient_id=self.patient.id,
            window_start=self.start,
            window_end=self.end,
        )
        projection = project_public_kpis(
            self._raw_kpis(),
            cgm_window=window,
            cgm_metrics=None,
        )

        self.assertTrue(window.verified)
        self.assertIsNone(projection["tir_pct"])
        self.assertIsNone(projection["cv_pct"])
