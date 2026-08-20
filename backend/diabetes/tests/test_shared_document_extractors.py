from pathlib import Path
from unittest import TestCase


class SharedDocumentExtractorCompatibilityTest(TestCase):
    def test_docx_legacy_import_reexports_shared_function(self):
        from diabetes.services.documents.extractors.docx import extract_docx as legacy
        from media.documents.extractors.docx import extract_docx as shared

        self.assertIs(legacy, shared)

    def test_pdf_legacy_import_reexports_shared_function(self):
        from diabetes.services.documents.extractors.pdf import extract_pdf as legacy
        from media.documents.extractors.pdf import extract_pdf as shared

        self.assertIs(legacy, shared)

    def test_image_legacy_import_reexports_shared_function(self):
        from diabetes.services.documents.extractors.image import extract_image as legacy
        from media.documents.extractors.image import extract_image as shared

        self.assertIs(legacy, shared)

    def test_diabetes_spreadsheet_extractor_does_not_move_to_shared_layer(self):
        shared_extractors = (
            Path(__file__).resolve().parents[2] / "media" / "documents" / "extractors"
        )
        self.assertFalse((shared_extractors / "spreadsheet.py").exists())
