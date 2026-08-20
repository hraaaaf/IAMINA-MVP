from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from diabetes.api.v1.documents import (
    PulperConfirmResponse,
    _pending_key,
    confirm_import,
    ingest_document,
)
from diabetes.services.documents.schema import PulperOutput


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

    @patch("diabetes.api.v1.documents._do_persist")
    @patch("diabetes.api.v1.documents.ingest", return_value=PulperOutput())
    def test_immediate_confirmation_leaves_no_replayable_batch(self, _ingest, do_persist):
        fake_cache = _FakeCache()
        patient = SimpleNamespace(id=101)
        request = SimpleNamespace(auth=patient)
        do_persist.return_value = PulperConfirmResponse(
            ok=True,
            lab_report_id=1,
            glucose_readings_saved=0,
            glucose_duplicates=0,
            errors=[],
        )

        with patch("diabetes.api.v1.documents.cache", fake_cache):
            ingest_document.__wrapped__(request, _Upload(), confirm=True)

        batch_id = do_persist.call_args.args[2]
        self.assertIsNone(fake_cache.get(_pending_key(patient.id, batch_id)))
