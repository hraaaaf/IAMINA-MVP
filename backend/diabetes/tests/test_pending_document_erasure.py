from unittest.mock import patch

from django.test import SimpleTestCase

from diabetes.api.v1.documents import _pending_key
from diabetes.apps import _purge_pending_documents
from media.documents.pending_cache import pending_extraction_pattern


class PendingDocumentErasureHookTest(SimpleTestCase):
    def test_document_batch_key_is_covered_by_patient_purge_pattern(self):
        prefix = pending_extraction_pattern(7).removesuffix("*")
        self.assertEqual(_pending_key(7, "batch-abc"), f"{prefix}batch-abc")

    def test_account_cleanup_delegates_to_patient_scoped_purge(self):
        with patch(
            "media.documents.pending_cache.purge_patient_pending_extractions"
        ) as purge:
            _purge_pending_documents(7, "firebase-uid-is-not-used")

        purge.assert_called_once_with(7)
