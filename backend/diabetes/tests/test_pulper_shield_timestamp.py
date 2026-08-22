"""Regression tests for Pulper glucose timestamp integrity."""
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from diabetes.services.documents.schema import GlucoseReading, LabValues, PulperOutput
from diabetes.services.documents.shield import PulperShield
from diabetes.services.documents.store import _parse_timestamp, persist


class PulperTimestampIntegrityTest(SimpleTestCase):
    @staticmethod
    def _validate_timestamp(timestamp: str) -> PulperOutput:
        output = PulperOutput(
            glucose_readings=[GlucoseReading(value_mgdl=123, timestamp=timestamp)],
            confidence=1.0,
        )
        return PulperShield.validate(output)

    def test_preserves_valid_datetime_time_and_timezone_semantics(self):
        timestamps = [
            "2026-01-15T10:20:30+01:00",
            "2026-01-15T10:20:30-05:00",
            "2026-01-15T10:20:30Z",
            "2026-01-15T10:20:30.123456+01:00",
            "2026-01-15T10:20:30",
        ]

        for timestamp in timestamps:
            with self.subTest(timestamp=timestamp):
                output = self._validate_timestamp(timestamp)
                self.assertEqual(len(output.glucose_readings), 1)
                self.assertEqual(output.glucose_readings[0].timestamp, timestamp)
                self.assertEqual(output.warnings, [])

    def test_date_only_timestamp_is_rejected_without_dropping_glucose_value(self):
        output = self._validate_timestamp("2026-01-15")

        self.assertEqual(len(output.glucose_readings), 1)
        self.assertEqual(output.glucose_readings[0].value_mgdl, 123)
        self.assertIsNone(output.glucose_readings[0].timestamp)
        self.assertTrue(any("heure absente" in warning for warning in output.warnings))

    def test_malformed_timestamp_is_rejected(self):
        output = self._validate_timestamp("2026-01-15Tbroken")

        self.assertIsNone(output.glucose_readings[0].timestamp)
        self.assertTrue(
            any("format datetime non reconnu" in warning for warning in output.warnings)
        )

    def test_future_aware_timestamp_is_rejected(self):
        future = (datetime.now(timezone.utc) + timedelta(days=1)).replace(
            microsecond=0
        ).isoformat()
        output = self._validate_timestamp(future)

        self.assertIsNone(output.glucose_readings[0].timestamp)
        self.assertTrue(any("date future" in warning for warning in output.warnings))

    def test_lab_report_date_contract_remains_date_only(self):
        output = PulperOutput(
            lab_values=LabValues(report_date="2026-01-15"),
            confidence=1.0,
        )

        validated = PulperShield.validate(output)

        self.assertEqual(validated.lab_values.report_date, "2026-01-15")
        self.assertEqual(validated.warnings, [])

    def test_llm_prompt_distinguishes_lab_dates_from_glucose_timestamps(self):
        from diabetes.services.documents.pulper import _PARSE_PROMPT_TEMPLATE

        self.assertIn(
            '- lab_values.report_date: use "YYYY-MM-DD" when present',
            _PARSE_PROMPT_TEMPLATE,
        )
        self.assertIn(
            "glucose_readings.timestamp: preserve an explicit source date+time",
            _PARSE_PROMPT_TEMPLATE,
        )
        self.assertIn(
            "NEVER invent midnight or a timezone",
            _PARSE_PROMPT_TEMPLATE,
        )
        self.assertNotIn(
            '- dates must be "YYYY-MM-DD" format',
            _PARSE_PROMPT_TEMPLATE,
        )

    def test_store_parser_preserves_iso_time_offset_and_fraction(self):
        timestamp = "2026-01-15T10:20:30.123456+01:00"

        parsed = _parse_timestamp(timestamp)

        self.assertIsNotNone(parsed)
        self.assertEqual(parsed.isoformat(), timestamp)

    def test_store_parser_rejects_date_only_instead_of_inventing_midnight(self):
        self.assertIsNone(_parse_timestamp("2026-01-15"))

    def test_persist_does_not_replace_missing_timestamp_with_now(self):
        output = PulperOutput(
            glucose_readings=[GlucoseReading(value_mgdl=123, timestamp=None)],
            confidence=1.0,
        )
        patient = SimpleNamespace(pk=42)
        report = MagicMock(pk=7)

        with (
            patch(
                "diabetes.services.documents.store.LabReport.objects.create",
                return_value=report,
            ),
            patch("diabetes.services.documents.store.LogEntry.objects.create") as create_log,
        ):
            result = persist(output, patient, "batch-1")

        create_log.assert_not_called()
        self.assertEqual(result.glucose_readings_saved, 0)
        self.assertTrue(
            any("sans timestamp explicite" in error for error in result.errors)
        )

    def test_persist_keeps_aware_timestamp_semantics(self):
        timestamp = "2026-01-15T10:20:30+01:00"
        output = PulperOutput(
            glucose_readings=[GlucoseReading(value_mgdl=123, timestamp=timestamp)],
            confidence=1.0,
        )
        patient = SimpleNamespace(pk=42)
        report = MagicMock(pk=7)

        with (
            patch(
                "diabetes.services.documents.store.LabReport.objects.create",
                return_value=report,
            ),
            patch("diabetes.services.documents.store.LogEntry.objects.filter") as filter_log,
            patch("diabetes.services.documents.store.LogEntry.objects.create") as create_log,
        ):
            filter_log.return_value.exists.return_value = False
            result = persist(output, patient, "batch-1")

        self.assertEqual(result.errors, [])
        self.assertEqual(result.glucose_readings_saved, 1)
        logged_at = create_log.call_args.kwargs["logged_at"]
        self.assertEqual(logged_at.isoformat(), timestamp)
