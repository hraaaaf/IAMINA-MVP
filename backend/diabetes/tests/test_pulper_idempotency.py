import uuid
from datetime import datetime

from django.contrib.auth.models import User
from django.test import TestCase

from diabetes.api.v1.imports import _make_client_uuid
from diabetes.models import LabReport, LogEntry
from diabetes.services.documents.schema import GlucoseReading, PulperOutput
from diabetes.services.documents.store import _make_uuid, persist
from diabetes.services.import_identity import make_import_client_uuid


class PulperIdempotencyTest(TestCase):
    def setUp(self):
        self.patient = User.objects.create_user(username="pulper-idem-patient")

    def _output(self, source_sha256: str = "a" * 64) -> PulperOutput:
        return PulperOutput(
            document_type="glucose_log",
            source_format="csv",
            confidence=0.95,
            source_sha256=source_sha256,
            glucose_readings=[
                GlucoseReading(
                    value_mgdl=126.0,
                    timestamp="2026-08-20T08:15:00+02:00",
                )
            ],
        )

    def test_same_document_different_batches_reuses_report_and_reading(self):
        first = persist(self._output(), self.patient, "batch-a")
        second = persist(self._output(), self.patient, "batch-b")

        self.assertTrue(first.ok, first.errors)
        self.assertTrue(second.ok, second.errors)
        self.assertEqual(first.lab_report_id, second.lab_report_id)
        self.assertEqual(first.glucose_readings_saved, 1)
        self.assertEqual(second.glucose_readings_saved, 0)
        self.assertEqual(second.glucose_duplicates, 1)
        self.assertEqual(LabReport.objects.filter(patient=self.patient).count(), 1)
        self.assertEqual(LogEntry.objects.filter(patient=self.patient).count(), 1)

        report = LabReport.objects.get(pk=first.lab_report_id)
        self.assertEqual(report.source_sha256, "a" * 64)
        self.assertEqual(report.glucose_readings_imported, 1)

    def test_same_source_hash_is_scoped_to_patient(self):
        other_patient = User.objects.create_user(username="pulper-idem-other")
        first = persist(self._output(), self.patient, "batch-a")
        second = persist(self._output(), other_patient, "batch-b")

        self.assertTrue(first.ok, first.errors)
        self.assertTrue(second.ok, second.errors)
        self.assertNotEqual(first.lab_report_id, second.lab_report_id)
        self.assertEqual(LabReport.objects.filter(source_sha256="a" * 64).count(), 2)
        self.assertEqual(LogEntry.objects.filter(source="import").count(), 2)

    def test_legacy_import_uuid_is_detected_by_clinical_identity(self):
        timestamp = datetime.fromisoformat("2026-08-20T08:15:00+02:00")
        LogEntry.objects.create(
            patient=self.patient,
            logged_at=timestamp,
            blood_sugar=126.0,
            client_uuid=uuid.uuid4(),
            source="import",
            meal_type="",
        )

        result = persist(self._output("b" * 64), self.patient, "batch-new")

        self.assertTrue(result.ok, result.errors)
        self.assertEqual(result.glucose_readings_saved, 0)
        self.assertEqual(result.glucose_duplicates, 1)
        self.assertEqual(LogEntry.objects.filter(patient=self.patient).count(), 1)

    def test_pulper_and_librelink_helpers_share_one_canonical_identity(self):
        local_time = datetime.fromisoformat("2026-08-20T08:15:00+02:00")
        utc_time = datetime.fromisoformat("2026-08-20T06:15:00+00:00")

        canonical = make_import_client_uuid(self.patient.pk, local_time, 126.0)
        self.assertEqual(
            canonical,
            _make_client_uuid(self.patient.pk, utc_time, 126.00),
        )
        self.assertEqual(
            canonical,
            _make_uuid(self.patient.pk, local_time, 126.0, "ignored-batch"),
        )

    def test_invalid_source_hash_fails_closed(self):
        result = persist(self._output("not-a-sha256"), self.patient, "batch-bad")

        self.assertFalse(result.ok)
        self.assertIsNone(result.lab_report_id)
        self.assertTrue(any("source_sha256" in error for error in result.errors))
        self.assertFalse(LabReport.objects.filter(patient=self.patient).exists())
