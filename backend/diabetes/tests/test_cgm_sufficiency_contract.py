from datetime import datetime, timedelta, timezone as dt_timezone

from django.contrib.auth.models import User
from django.test import TestCase

from diabetes.models import CGMReadingRecord, CGMSensorSession
from diabetes.services.clinical.cgm_eligibility import assess_cgm_window


class RealCgmSufficiencyContractTests(TestCase):
    interval_minutes = 15

    def setUp(self):
        self.patient = User.objects.create_user(username="synthetic-cgm-patient")
        self.start = datetime(2026, 1, 1, tzinfo=dt_timezone.utc)
        self.end = self.start + timedelta(days=14)

    def _session(self, *, key, start=None, end=None, source="linx"):
        return CGMSensorSession.objects.create(
            patient=self.patient,
            source=source,
            session_key=key,
            started_at=start or self.start,
            ended_at=end or self.end,
            expected_interval_minutes=self.interval_minutes,
            timezone_name="UTC",
            end_reason=CGMSensorSession.EndReason.REPLACED,
        )

    def _readings(self, session, *, start, count, duplicate_first=False):
        rows = []
        for index in range(count):
            recorded_at = start + timedelta(minutes=self.interval_minutes * index)
            rows.append(
                CGMReadingRecord(
                    patient=self.patient,
                    source=session.source,
                    session=session,
                    recorded_at=recorded_at,
                    glucose_mg_dl=110,
                    dedupe_key=f"{session.session_key}:{index}",
                )
            )
        if duplicate_first and rows:
            rows.append(
                CGMReadingRecord(
                    patient=self.patient,
                    source=session.source,
                    session=session,
                    recorded_at=rows[0].recorded_at,
                    glucose_mg_dl=111,
                    dedupe_key=f"{session.session_key}:duplicate",
                )
            )
        CGMReadingRecord.objects.bulk_create(rows)

    def _expected_full_window(self):
        seconds = int((self.end - self.start).total_seconds())
        return seconds // (self.interval_minutes * 60) + 1

    def test_fourteen_day_window_at_or_above_seventy_percent_is_verified(self):
        session = self._session(key="sensor-a")
        expected = self._expected_full_window()
        count = (expected * 70 + 99) // 100
        self._readings(session, start=self.start, count=count)

        result = assess_cgm_window(
            patient_id=self.patient.id,
            window_start=self.start,
            window_end=self.end,
        )

        self.assertTrue(result.verified)
        self.assertEqual(result.reason, "verified")
        self.assertGreaterEqual(result.coverage_pct, 70.0)
        self.assertEqual(result.expected_readings, expected)

    def test_below_seventy_percent_fails_closed(self):
        session = self._session(key="sensor-b")
        expected = self._expected_full_window()
        count = expected * 69 // 100
        self._readings(session, start=self.start, count=count)

        result = assess_cgm_window(
            patient_id=self.patient.id,
            window_start=self.start,
            window_end=self.end,
        )

        self.assertFalse(result.verified)
        self.assertEqual(result.reason, "insufficient_coverage")
        self.assertLess(result.coverage_pct, 70.0)

    def test_duplicate_timestamps_do_not_inflate_received_coverage(self):
        session = self._session(key="sensor-c")
        self._readings(session, start=self.start, count=10, duplicate_first=True)

        result = assess_cgm_window(
            patient_id=self.patient.id,
            window_start=self.start,
            window_end=self.end,
        )

        self.assertEqual(result.received_readings, 10)
        self.assertFalse(result.verified)

    def test_sequential_multi_sensor_window_can_be_verified(self):
        midpoint = self.start + timedelta(days=7)
        first = self._session(key="sensor-d1", end=midpoint)
        second = self._session(key="sensor-d2", start=midpoint, end=self.end)

        first_seconds = int((midpoint - self.start).total_seconds())
        second_seconds = int((self.end - midpoint).total_seconds())
        first_expected = first_seconds // (self.interval_minutes * 60) + 1
        second_expected = second_seconds // (self.interval_minutes * 60) + 1
        self._readings(first, start=self.start, count=first_expected)
        self._readings(second, start=midpoint, count=second_expected)

        result = assess_cgm_window(
            patient_id=self.patient.id,
            window_start=self.start,
            window_end=self.end,
        )

        self.assertTrue(result.verified)
        self.assertEqual(result.session_count, 2)
        self.assertEqual(result.active_window_pct, 100.0)

    def test_overlapping_sensor_sessions_fail_closed(self):
        self._session(key="sensor-e1", end=self.start + timedelta(days=8))
        self._session(
            key="sensor-e2",
            start=self.start + timedelta(days=7),
            end=self.end,
        )

        result = assess_cgm_window(
            patient_id=self.patient.id,
            window_start=self.start,
            window_end=self.end,
        )

        self.assertFalse(result.verified)
        self.assertEqual(result.reason, "overlapping_sensor_sessions")

    def test_naive_timezone_window_fails_closed(self):
        result = assess_cgm_window(
            patient_id=self.patient.id,
            window_start=datetime(2026, 1, 1),
            window_end=datetime(2026, 1, 15),
        )

        self.assertFalse(result.verified)
        self.assertEqual(result.reason, "timezone_required")

    def test_short_window_fails_even_with_complete_sensor_data(self):
        short_end = self.start + timedelta(days=13, hours=23)
        session = self._session(key="sensor-f", end=short_end)
        seconds = int((short_end - self.start).total_seconds())
        count = seconds // (self.interval_minutes * 60) + 1
        self._readings(session, start=self.start, count=count)

        result = assess_cgm_window(
            patient_id=self.patient.id,
            window_start=self.start,
            window_end=short_end,
        )

        self.assertFalse(result.verified)
        self.assertEqual(result.reason, "insufficient_window_duration")
