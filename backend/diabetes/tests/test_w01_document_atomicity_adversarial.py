"""W01 adversarial regression: one clinical import never partially commits."""
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase

from diabetes.models import LabReport, LogEntry
from diabetes.services.documents.schema import GlucoseReading, PulperOutput
from diabetes.services.documents.store import persist


class W01DocumentAtomicityTest(TestCase):
    def setUp(self):
        self.patient = User.objects.create_user(username="w01-atomic-synthetic")

    def _output(self, second_timestamp="2026-08-20T09:15:00+02:00"):
        return PulperOutput(
            source_sha256="e" * 64,
            document_type="glucose_log",
            source_format="csv",
            confidence=0.95,
            glucose_readings=[
                GlucoseReading(value_mgdl=121.0, timestamp="2026-08-20T08:15:00+02:00"),
                GlucoseReading(value_mgdl=124.0, timestamp=second_timestamp),
            ],
        )

    def _assert_rolled_back(self, result):
        self.assertFalse(result.ok)
        self.assertIsNone(result.lab_report_id)
        self.assertEqual(result.glucose_readings_saved, 0)
        self.assertFalse(LabReport.objects.filter(patient=self.patient).exists())
        self.assertFalse(LogEntry.objects.filter(patient=self.patient).exists())

    def test_second_write_failure_rolls_back_earlier_writes(self):
        create = LogEntry.objects.create
        counter = 0

        def interrupt(**kwargs):
            nonlocal counter
            counter += 1
            if counter == 2:
                raise RuntimeError("synthetic-write-interruption")
            return create(**kwargs)

        with patch.object(LogEntry.objects, "create", side_effect=interrupt):
            result = persist(self._output(), self.patient, "synthetic-failure")

        self.assertEqual(counter, 2)
        self._assert_rolled_back(result)
        self.assertTrue(result.errors)
        self.assertNotIn("synthetic-write-interruption", " ".join(result.errors))

    def test_missing_timestamp_cannot_commit_remaining_readings(self):
        result = persist(self._output(second_timestamp=None), self.patient, "bad-timestamp")
        self._assert_rolled_back(result)
        self.assertTrue(any("timestamp" in error for error in result.errors))

    def test_failure_after_first_insert_before_second_check_rolls_back(self):
        with patch(
            "diabetes.services.documents.store.imported_reading_exists",
            side_effect=[False, RuntimeError("synthetic-post-write-failure")],
        ):
            result = persist(self._output(), self.patient, "synthetic-late-failure")
        self._assert_rolled_back(result)
