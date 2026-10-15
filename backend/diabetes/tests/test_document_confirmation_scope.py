from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase as DjangoTestCase

from diabetes.api.v1.documents import (
    PulperConfirmResponse,
    _pending_key,
    confirm_import,
    ingest_document,
)
from diabetes.models import LabReport
from diabetes.services.documents.schema import LabValues, PulperOutput


class _FakeCache:
    def __init__(self):
        self.values = {}

    def set(self, key, value, timeout=None):
        self.values[key] = value

    def get(self, key):
        return self.values.get(key)

    def delete(self, key):
        self.values.pop(key, None)


class _Upload:
    name = "synthetic.pdf"
    content_type = "application/pdf"
    size = 4

    def read(self, size=-1):
        return b"test"


class DocumentConfirmationScopeTest(TestCase):
    def test_pending_keys_are_patient_scoped(self):
        self.assertNotEqual(_pending_key(101, "batch"), _pending_key(202, "batch"))

    @patch("diabetes.api.v1.documents._do_persist")
    @patch("diabetes.api.v1.documents.ingest", return_value=PulperOutput())
    def test_preview_does_not_persist_before_confirmation(self, _ingest, do_persist):
        fake_cache = _FakeCache()
        patient = SimpleNamespace(id=101)
        request = SimpleNamespace(auth=patient)

        with patch("diabetes.api.v1.documents.cache", fake_cache):
            status, preview = ingest_document.__wrapped__(request, _Upload(), confirm=False)

        self.assertEqual(status, 200)
        do_persist.assert_not_called()
        self.assertIsNotNone(fake_cache.get(_pending_key(patient.id, preview.batch_id)))

    @patch("diabetes.api.v1.documents._do_persist")
    def test_other_patient_cannot_confirm_staged_batch(self, do_persist):
        fake_cache = _FakeCache()
        owner = SimpleNamespace(id=101)
        other = SimpleNamespace(id=202)
        batch_id = "synthetic-batch"
        output = PulperOutput()
        fake_cache.set(_pending_key(owner.id, batch_id), output)

        with patch("diabetes.api.v1.documents.cache", fake_cache):
            response = confirm_import(SimpleNamespace(auth=other), batch_id)

        self.assertFalse(response.ok)
        do_persist.assert_not_called()
        self.assertIs(fake_cache.get(_pending_key(owner.id, batch_id)), output)

    @patch("diabetes.api.v1.documents._do_persist")
    def test_owner_confirmation_consumes_batch_once(self, do_persist):
        fake_cache = _FakeCache()
        owner = SimpleNamespace(id=101)
        batch_id = "synthetic-batch"
        output = PulperOutput()
        expected = PulperConfirmResponse(
            ok=True,
            lab_report_id=1,
            glucose_readings_saved=0,
            glucose_duplicates=0,
            errors=[],
        )
        do_persist.return_value = expected
        fake_cache.set(_pending_key(owner.id, batch_id), output)

        with patch("diabetes.api.v1.documents.cache", fake_cache):
            response = confirm_import(SimpleNamespace(auth=owner), batch_id)

        self.assertIs(response, expected)
        do_persist.assert_called_once_with(output, owner, batch_id)
        self.assertIsNone(fake_cache.get(_pending_key(owner.id, batch_id)))

    def test_patient_preview_excludes_uncited_medication_fields(self):
        from diabetes.services.documents.pulper import (
            _enforce_model_evidence_coverage,
        )
        from diabetes.services.documents.schema import FieldEvidence, MedicationEntry

        extracted = PulperOutput(
            parser_model="synthetic",
            confidence=0.95,
            medications=[MedicationEntry(
                name="metformin",
                dose="1000 mg",
                frequency="twice daily",
                drug_type="oral",
                evidence={"name": FieldEvidence(
                    raw_value="metformin",
                    source_ref="text:L0001",
                    verified=True,
                )},
            )],
        )
        _enforce_model_evidence_coverage(extracted)
        cache = _FakeCache()
        with (
            patch("diabetes.api.v1.documents.cache", cache),
            patch("diabetes.api.v1.documents.ingest", return_value=extracted),
        ):
            status, preview = ingest_document.__wrapped__(
                SimpleNamespace(auth=SimpleNamespace(id=101)),
                _Upload(),
                confirm=False,
            )
        self.assertEqual(status, 200)
        self.assertEqual(len(preview.medications), 1)
        self.assertEqual(preview.medications[0].name, "metformin")
        self.assertIsNone(preview.medications[0].dose)
        self.assertIsNone(preview.medications[0].frequency)
        self.assertIsNone(preview.medications[0].drug_type)

    @patch("diabetes.api.v1.documents._do_persist")
    @patch("diabetes.api.v1.documents.ingest", return_value=PulperOutput())
    def test_immediate_confirmation_is_rejected_before_upload_or_persistence(self, _ingest, do_persist):
        fake_cache = _FakeCache()
        patient = SimpleNamespace(id=101)
        request = SimpleNamespace(auth=patient)
        upload = _Upload()
        with patch("diabetes.api.v1.documents.cache", fake_cache):
            status, payload = ingest_document.__wrapped__(request, upload, confirm=True)

        self.assertEqual(status, 422)
        self.assertIn("Prévisualisation", payload["detail"])
        _ingest.assert_not_called()
        do_persist.assert_not_called()
        self.assertEqual(fake_cache.values, {})

class DocumentConfirmationDatabaseContractTest(DjangoTestCase):
    @patch("diabetes.api.v1.documents.ingest")
    def test_immediate_confirm_true_never_creates_report(self, mocked_ingest):
        patient = User.objects.create_user(username="pulper-preview-required")
        request = SimpleNamespace(auth=patient)
        with patch("diabetes.api.v1.documents.cache", _FakeCache()):
            status, _body = ingest_document.__wrapped__(
                request, _Upload(), confirm=True,
            )
        self.assertEqual(status, 422)
        mocked_ingest.assert_not_called()
        self.assertFalse(LabReport.objects.filter(patient=patient).exists())

    def test_preview_then_patient_bound_confirm_persists_once(self):
        patient = User.objects.create_user(username="pulper-two-step")
        other = User.objects.create_user(username="pulper-other")
        cache = _FakeCache()
        output = PulperOutput(
            source_format="docx", document_type="lab_report",
            confidence=0.91, lab_values=LabValues(hba1c_pct=7.2),
        )
        with (
            patch("diabetes.api.v1.documents.cache", cache),
            patch("diabetes.api.v1.documents.ingest", return_value=output),
            patch("diabetes.api.v1.documents._read_upload_with_limit",
                  return_value=(b"fake", None)),
        ):
            status, preview = ingest_document.__wrapped__(
                SimpleNamespace(auth=patient), _Upload(), confirm=False,
            )
            self.assertEqual(status, 200)
            self.assertFalse(LabReport.objects.filter(patient=patient).exists())
            unauthorized = confirm_import(
                SimpleNamespace(auth=other), preview.batch_id,
            )
            self.assertFalse(unauthorized.ok)
            self.assertFalse(LabReport.objects.exists())
            confirmed = confirm_import(
                SimpleNamespace(auth=patient), preview.batch_id,
            )
            self.assertTrue(confirmed.ok, confirmed.errors)
            self.assertEqual(
                LabReport.objects.filter(patient=patient).count(), 1,
            )
            replay = confirm_import(
                SimpleNamespace(auth=patient), preview.batch_id,
            )
            self.assertFalse(replay.ok)
            self.assertEqual(LabReport.objects.count(), 1)

    def test_llm_notes_are_absent_from_preview_and_database(self):
        from diabetes.services.documents.pulper import _map_json_to_output

        patient = User.objects.create_user(username="pulper-no-model-notes")
        output = PulperOutput(source_format="docx", document_type="lab_report")
        _map_json_to_output(output, {
            "document_type": "lab_report",
            "confidence": 0.91,
            "lab_values": {"hba1c_pct": 7.2},
            "clinical_notes": "Increase insulin dose now",
        })
        # The model text was eliminated by the mapper before either boundary.
        self.assertEqual(output.clinical_notes, "")
        cache = _FakeCache()
        with (
            patch("diabetes.api.v1.documents.cache", cache),
            patch("diabetes.api.v1.documents.ingest", return_value=output),
        ):
            status, preview = ingest_document.__wrapped__(
                SimpleNamespace(auth=patient), _Upload(), confirm=False,
            )
            self.assertEqual(status, 200)
            self.assertEqual(preview.clinical_notes, "")
            self.assertFalse(LabReport.objects.filter(patient=patient).exists())
            result = confirm_import(
                SimpleNamespace(auth=patient), preview.batch_id,
            )
        self.assertTrue(result.ok, result.errors)
        report = LabReport.objects.get(pk=result.lab_report_id)
        self.assertEqual(report.clinical_notes, "")

    def test_invalid_extraction_cannot_persist_after_preview(self):
        patient = User.objects.create_user(username="pulper-invalid-review")
        cache = _FakeCache()
        output = PulperOutput(
            source_format="docx", confidence=0.1,
            lab_values=LabValues(hba1c_pct=7.2),
            errors=["Synthetic provider refusal"],
        )
        cache.set(_pending_key(patient.id, "invalid"), output)
        with patch("diabetes.api.v1.documents.cache", cache):
            result = confirm_import(SimpleNamespace(auth=patient), "invalid")
        self.assertFalse(result.ok)
        self.assertFalse(LabReport.objects.filter(patient=patient).exists())
