from unittest import TestCase

from diabetes.api.v1.documents import LabReportOut


class DocumentListStorageContractTest(TestCase):
    def test_list_schema_exposes_structured_metadata_not_retained_or_original_media(self):
        fields = set(LabReportOut.model_fields)

        self.assertIn("document_type", fields)
        self.assertIn("confidence", fields)
        self.assertTrue(
            fields.isdisjoint(
                {
                    "raw_text",
                    "file",
                    "file_bytes",
                    "binary",
                    "original_media",
                    "original_url",
                    "signed_url",
                    "storage_key",
                    "import_batch_id",
                }
            )
        )
