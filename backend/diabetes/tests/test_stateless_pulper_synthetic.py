"""W01-C1 AEAD synthetic preview: isolation, replay, expiry and rollback."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4

from django.contrib.auth.models import User
from django.db import close_old_connections, connection, connections
from django.test import TestCase, TransactionTestCase, override_settings

from core.models import BasePatientProfile
from diabetes.api.v1.documents import (
    PulperConfirmRequest,
    confirm_import,
    ingest_document,
)
from diabetes.models import DocumentConfirmationNonce, LabReport
from diabetes.services.documents.schema import LabValues, PulperOutput
from diabetes.services.documents.stateless_preview import (
    PreviewEnvelopeError,
    issue_preview_envelope,
    synthetic_mode_enabled,
    verify_preview_envelope,
)


class _SyntheticUpload:
    name = "synthetic.csv"
    content_type = "text/csv"
    size = 9

    def read(self, size=-1):
        return b"synthetic"


@override_settings(
    IAMINA_NO_REDIS=True,
    IAMINA_PULPER_STATELESS_SYNTHETIC=True,
    DEBUG=True, VERCEL=False, VERCEL_ENV="",
)
class StatelessPulperSyntheticTest(TestCase):
    def setUp(self):
        self.a = User.objects.create_user("pulper-a", email="a@example.invalid")
        self.b = User.objects.create_user("pulper-b", email="b@example.invalid")
        BasePatientProfile.objects.create(patient=self.a)
        BasePatientProfile.objects.create(patient=self.b)
        self.output = PulperOutput(
            source_sha256="a" * 64,
            document_type="lab_report",
            source_format="csv",
            lab_values=LabValues(hba1c_pct=5.9),
            confidence=0.95,
            clinical_notes="Synthetic-only-marker",
            raw_text="DO_NOT_INCLUDE_UNTRUSTED_RAW_OCR_TEXT",
        )
        self.batch_id = str(uuid4())

    def _issue(self, now=1000):
        return issue_preview_envelope(
            self.output, patient_id=self.a.pk, batch_id=self.batch_id,
            auth_version=0, now=now,
        )

    def test_envelope_is_encrypted_and_strips_raw_ocr_text(self):
        token = self._issue()
        self.assertNotIn("Synthetic-only-marker", token)
        self.assertNotIn("DO_NOT_INCLUDE_UNTRUSTED_RAW_OCR_TEXT", token)
        restored = verify_preview_envelope(
            token, patient_id=self.a.pk, batch_id=self.batch_id,
            auth_version=0, now=1001,
        )
        self.assertEqual(restored.lab_values.hba1c_pct, 5.9)
        self.assertEqual(restored.raw_text, "")

    def test_cross_patient_batch_revocation_expiration_and_tamper(self):
        token = self._issue()
        for opts in (
            {"patient_id": self.b.pk, "batch_id": self.batch_id, "auth_version": 0, "now": 1001},
            {"patient_id": self.a.pk, "batch_id": str(uuid4()), "auth_version": 0, "now": 1001},
            {"patient_id": self.a.pk, "batch_id": self.batch_id, "auth_version": 1, "now": 1001},
            {"patient_id": self.a.pk, "batch_id": self.batch_id, "auth_version": 0, "now": 4600},
            {"patient_id": self.a.pk, "batch_id": self.batch_id, "auth_version": 0, "now": 965},
        ):
            with self.subTest(opts=opts), self.assertRaises(PreviewEnvelopeError):
                verify_preview_envelope(token, **opts)
        with self.assertRaises(PreviewEnvelopeError):
            verify_preview_envelope(
                token[:-2] + ("AA" if token[-2:] != "AA" else "BB"),
                patient_id=self.a.pk, batch_id=self.batch_id,
                auth_version=0, now=1001,
            )

    def test_feature_refuses_vercel_and_non_debug(self):
        with override_settings(VERCEL=True):
            self.assertFalse(synthetic_mode_enabled())
            with self.assertRaises(PreviewEnvelopeError):
                self._issue()
        with override_settings(DEBUG=False):
            self.assertFalse(synthetic_mode_enabled())

    def test_synthetic_ingest_confirm_persists_once_not_twice(self):
        request = SimpleNamespace(auth=self.a)
        with patch("diabetes.api.v1.documents.ingest", return_value=self.output):
            status, preview = ingest_document.__wrapped__(
                request, _SyntheticUpload(), confirm=False,
            )
        self.assertEqual(status, 200)
        self.assertTrue(preview.preview_token)
        self.assertEqual(DocumentConfirmationNonce.objects.count(), 0)
        self.assertEqual(LabReport.objects.count(), 0)
        data = PulperConfirmRequest(preview_token=preview.preview_token)
        first = confirm_import(request, preview.batch_id, data)
        self.assertTrue(first.ok, first.errors)
        self.assertEqual(DocumentConfirmationNonce.objects.count(), 1)
        self.assertEqual(LabReport.objects.filter(patient=self.a).count(), 1)
        replay = confirm_import(request, preview.batch_id, data)
        self.assertFalse(replay.ok)
        self.assertEqual(DocumentConfirmationNonce.objects.count(), 1)
        self.assertEqual(LabReport.objects.count(), 1)

    def test_persistence_error_rolls_back_nonce(self):
        request = SimpleNamespace(auth=self.a)
        token = issue_preview_envelope(
            self.output, patient_id=self.a.pk,
            batch_id=self.batch_id, auth_version=0,
        )
        with patch("diabetes.api.v1.documents._do_persist") as persist_mock:
            persist_mock.return_value = SimpleNamespace(ok=False)
            result = confirm_import(
                request, self.batch_id,
                PulperConfirmRequest(preview_token=token),
            )
        self.assertFalse(result.ok)
        self.assertEqual(DocumentConfirmationNonce.objects.count(), 0)
        self.assertEqual(LabReport.objects.count(), 0)

    def test_other_patient_cannot_confirm(self):
        token = issue_preview_envelope(
            self.output, patient_id=self.a.pk,
            batch_id=self.batch_id, auth_version=0,
        )
        result = confirm_import(
            SimpleNamespace(auth=self.b), self.batch_id,
            PulperConfirmRequest(preview_token=token),
        )
        self.assertFalse(result.ok)
        self.assertEqual(DocumentConfirmationNonce.objects.count(), 0)
        self.assertEqual(LabReport.objects.count(), 0)


@override_settings(
    IAMINA_NO_REDIS=True,
    IAMINA_PULPER_STATELESS_SYNTHETIC=True,
    DEBUG=True, VERCEL=False, VERCEL_ENV="",
)
class StatelessPulperPostgresRaceTest(TransactionTestCase):
    """Two real PostgreSQL sessions must not confirm one AEAD batch twice."""

    def test_parallel_confirm_is_single_use_across_postgres_connections(self):
        if connection.vendor != "postgresql":
            self.skipTest("Concurrent SQL uniqueness needs PostgreSQL")

        patient = User.objects.create_user(
            "pulper-race", email="race@example.invalid"
        )
        BasePatientProfile.objects.create(patient=patient)
        batch_id = str(uuid4())
        output = PulperOutput(
            source_sha256="b" * 64,
            document_type="lab_report", source_format="csv",
            lab_values=LabValues(hba1c_pct=5.9), confidence=0.95,
            clinical_notes="Synthetic concurrency marker",
        )
        token = issue_preview_envelope(
            output, patient_id=patient.pk, batch_id=batch_id,
            auth_version=0,
        )
        barrier = Barrier(2)

        def confirm_on_new_connection():
            close_old_connections()
            try:
                with connections["default"].cursor() as cursor:
                    cursor.execute("SELECT pg_backend_pid()")
                    backend_pid = cursor.fetchone()[0]
                barrier.wait(timeout=15)
                result = confirm_import(
                    SimpleNamespace(auth=patient), batch_id,
                    PulperConfirmRequest(preview_token=token),
                )
                return backend_pid, result.ok
            finally:
                connections["default"].close()

        with ThreadPoolExecutor(max_workers=2) as executor:
            future_a = executor.submit(confirm_on_new_connection)
            future_b = executor.submit(confirm_on_new_connection)
            outcomes = [future_a.result(timeout=30), future_b.result(timeout=30)]

        self.assertEqual(len({pid for pid, _ in outcomes}), 2)
        self.assertCountEqual([True, False], [ok for _, ok in outcomes])
        self.assertEqual(DocumentConfirmationNonce.objects.count(), 1)
        self.assertEqual(LabReport.objects.filter(patient=patient).count(), 1)
