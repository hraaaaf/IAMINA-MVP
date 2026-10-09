"""V1-01: verified CGM AGP may never inherit manual/unlinked glucose rows."""
import datetime as dt
from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase

from ai.api.v1.ai import SummaryRequest, SummaryResponse, get_summary
from diabetes.models import CGMReadingRecord, CGMSensorSession, LogEntry
from diabetes.services.clinical.cgm_analytics import compute_verified_cgm_agp_profile
from diabetes.services.clinical.sql_analytics import AnalyticalKPIs


class VerifiedCgmAgpTests(TestCase):
    def setUp(self):
        self.patient = User.objects.create_user(username="v1-01-agp-patient")
        self.other = User.objects.create_user(username="v1-01-agp-other")
        now = dt.datetime.now(dt.timezone.utc)
        self.start = now - dt.timedelta(days=14, minutes=5)
        self.end = now - dt.timedelta(minutes=2)
        self.session = CGMSensorSession.objects.create(
            patient=self.patient,
            source="linx",
            session_key="v1-01-agp",
            started_at=self.start,
            ended_at=self.end,
            expected_interval_minutes=60,
            timezone_name="UTC",
            end_reason=CGMSensorSession.EndReason.REPLACED,
        )

    def _reading(self, *, patient=None, session=None, value=100, hour=0, key=None, source="linx", when=None):
        patient = patient or self.patient
        return CGMReadingRecord.objects.create(
            patient=patient,
            session=self.session if session is None else session,
            source=source,
            recorded_at=when or (self.start + dt.timedelta(hours=hour)),
            glucose_mg_dl=value,
            dedupe_key=key or f"agp-{patient.id}-{hour}-{value}-{source}",
        )

    def _profile(self):
        return compute_verified_cgm_agp_profile(
            patient_id=self.patient.id, window_start=self.start, window_end=self.end
        )

    def test_mixed_and_unlinked_rows_never_contaminate_agp_percentiles(self):
        first = self.start + dt.timedelta(hours=1)
        self._reading(value=100, when=first, key="first")
        self._reading(value=120, when=first + dt.timedelta(days=1), key="second")
        self._reading(value=450, when=first, key="duplicate")  # same timestamp
        self._reading(value=500, when=first + dt.timedelta(days=2), key="mismatch", source="libre")
        self._reading(value=470, when=self.end + dt.timedelta(days=1), key="outside")
        CGMReadingRecord.objects.create(
            patient=self.patient, source="linx", session=None,
            recorded_at=first + dt.timedelta(days=3), glucose_mg_dl=480, dedupe_key="unlinked",
        )
        CGMReadingRecord.objects.create(
            patient=self.other, source="linx", session=self.session,
            recorded_at=first + dt.timedelta(days=4), glucose_mg_dl=490, dedupe_key="other-user",
        )
        # Deliberately extreme MANUAL row: not a sensor fact, even with valid CGM.
        LogEntry.objects.create(
            patient=self.patient, blood_sugar=390, source="manual",
            logged_at=first,
        )
        profile = self._profile()
        hour = first.hour
        self.assertEqual(profile, [{
            "hour": hour, "avg": 110.0,
            "p5": 101.0, "p25": 105.0, "p50": 110.0,
            "p75": 115.0, "p95": 119.0,
        }])

    def test_manual_only_without_linked_cgm_has_no_agp(self):
        LogEntry.objects.create(
            patient=self.patient, blood_sugar=350,
            source="manual", logged_at=self.start + dt.timedelta(hours=1),
        )
        self.assertEqual(self._profile(), [])

    def test_unknown_sensor_time_zone_fails_closed(self):
        self.session.timezone_name = "Invalid/TimeZone"
        self.session.save(update_fields=["timezone_name"])
        self._reading(value=110, hour=1)
        self.assertEqual(self._profile(), [])

    def test_verified_summary_serializes_positive_cgm_only_profile(self):
        rows = []
        count = 14 * 24  # hourly for 14 days; >70% coverage
        for index in range(count):
            rows.append(CGMReadingRecord(
                patient=self.patient, session=self.session, source="linx",
                recorded_at=self.start + dt.timedelta(hours=index),
                glucose_mg_dl=100 if index % 2 == 0 else 120,
                dedupe_key=f"full-agp-{index}",
            ))
        CGMReadingRecord.objects.bulk_create(rows)
        raw = AnalyticalKPIs(
            avg_glucose=350.0, std_dev=25.0, cv_pct=50.0,
            tir_pct=0.0, tar_pct=100.0, tbr_pct=0.0, gmi=9.1,
            log_count=60, days_with_data=14, cgm_active_pct=0.0,
        )
        request = SimpleNamespace(user=self.patient)
        with (
            patch("ai.api.v1.ai._get_patient_language", return_value="fr"),
            patch("ai.api.v1.ai.compute_kpis", return_value=raw),
            patch("ai.api.v1.ai.run_clinical_analysis",
                  return_value=SimpleNamespace(patterns=[])),
            patch("ai.api.v1.ai.compress",
                  return_value=SimpleNamespace(full_pivot_text="synthetic")),
            patch("ai.api.v1.ai._call_llm_for_summary", return_value=[]),
            patch("core.medical_safety.sanitize_patient_visible", return_value=[]),
            patch("ai.api.v1.ai.LogEntry.objects.filter") as logs,
            patch("ai.api.v1.ai.compute_daily_averages", return_value=[]),
            patch("ai.api.v1.ai.track"),
            patch("ai.api.v1.ai.get_ai_provider_name", return_value="fallback"),
        ):
            logs.return_value.order_by.return_value = []
            raw_response = get_summary.__wrapped__(request, SummaryRequest(days=14))

        serialized = SummaryResponse.model_validate(raw_response).model_dump()
        self.assertNotEqual(serialized["kpis"]["tir_pct"], 0.0)
        self.assertEqual(serialized["kpis"]["gmi"], None)
        self.assertTrue(serialized["agp_profile"])
        self.assertEqual(len(serialized["agp_profile"]), 24)
        self.assertTrue(all(row["p95"] <= 120 for row in serialized["agp_profile"]))
        self.assertTrue(all(row["p5"] >= 100 for row in serialized["agp_profile"]))
