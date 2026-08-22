from pathlib import Path
from unittest import TestCase

import diabetes.services.documents.pulper as pulper


class SharedDocumentExtractorCloseoutTest(TestCase):
    def test_pulper_imports_generic_extractors_from_shared_media(self):
        source = Path(pulper.__file__).read_text(encoding="utf-8")
        self.assertIn("from media.documents.extractors.docx import extract_docx", source)
        self.assertIn("from media.documents.extractors.pdf import extract_pdf", source)
        self.assertRegex(
            source,
            r"from media\.documents\.extractors\.image import .*extract_image",
        )
        self.assertNotIn("diabetes.services.documents.extractors.docx", source)
        self.assertNotIn("diabetes.services.documents.extractors.pdf", source)
        self.assertNotIn("diabetes.services.documents.extractors.image", source)

    def test_legacy_generic_extractor_shims_are_removed(self):
        legacy_dir = Path(__file__).resolve().parents[1] / "services" / "documents" / "extractors"
        self.assertFalse((legacy_dir / "docx.py").exists())
        self.assertFalse((legacy_dir / "pdf.py").exists())
        self.assertFalse((legacy_dir / "image.py").exists())

    def test_diabetes_spreadsheet_extractor_remains_condition_owned(self):
        shared_extractors = (
            Path(__file__).resolve().parents[2] / "media" / "documents" / "extractors"
        )
        self.assertFalse((shared_extractors / "spreadsheet.py").exists())
