"""
Smoke test — diabetes.services.documents.pulper importability.

Verifies that the diabetes capsule owns the Pulper orchestrator and that the
ingest entry point is callable. No file I/O or LLM calls are made.
"""
from django.test import SimpleTestCase


class PulperImportSmokeTest(SimpleTestCase):
    def test_pulper_importable(self):
        from diabetes.services.documents.pulper import ingest
        assert callable(ingest)

    def test_pulper_output_class_importable(self):
        from diabetes.services.documents.schema import PulperOutput
        assert callable(PulperOutput)
