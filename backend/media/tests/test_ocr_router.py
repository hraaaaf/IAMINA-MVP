from unittest import TestCase

from media.documents.ocr_router import (
    OcrCapabilities,
    OcrRequest,
    choose_ocr_lane,
)


class OcrRouterContractTest(TestCase):
    def test_digital_pdf_stays_local_without_ocr_provider(self):
        decision = choose_ocr_lane(
            OcrRequest(modality="digital_pdf"),
            OcrCapabilities(),
        )

        self.assertEqual(decision.lane, "local_text_layer")
        self.assertFalse(decision.external_egress)

    def test_latin_document_prefers_qualified_local_lane(self):
        decision = choose_ocr_lane(
            OcrRequest(modality="document_image", script="latin"),
            OcrCapabilities(
                local_latin_qualified=True,
                governed_cloud_allowed=True,
            ),
        )

        self.assertEqual(decision.lane, "local_ocr")
        self.assertEqual(decision.reason, "qualified_local_latin")

    def test_unqualified_latin_uses_cloud_only_when_governed(self):
        governed = choose_ocr_lane(
            OcrRequest(modality="scanned_pdf", script="latin"),
            OcrCapabilities(governed_cloud_allowed=True),
        )
        blocked = choose_ocr_lane(
            OcrRequest(modality="scanned_pdf", script="latin"),
            OcrCapabilities(governed_cloud_allowed=False),
        )

        self.assertEqual(governed.lane, "governed_cloud_ocr")
        self.assertTrue(governed.external_egress)
        self.assertEqual(blocked.lane, "unavailable")
        self.assertFalse(blocked.external_egress)

    def test_full_arabic_does_not_use_bounded_only_local_evidence(self):
        decision = choose_ocr_lane(
            OcrRequest(
                modality="document_image",
                script="arabic",
                bounded_capture=False,
            ),
            OcrCapabilities(
                bounded_arabic_qualified=True,
                governed_cloud_allowed=False,
            ),
        )

        self.assertEqual(decision.lane, "unavailable")
        self.assertEqual(decision.reason, "arabic_local_unqualified_no_qualified_lane")

    def test_bounded_arabic_can_use_separately_qualified_local_lane(self):
        decision = choose_ocr_lane(
            OcrRequest(
                modality="document_image",
                script="arabic",
                bounded_capture=True,
            ),
            OcrCapabilities(bounded_arabic_qualified=True),
        )

        self.assertEqual(decision.lane, "local_ocr")
        self.assertEqual(decision.reason, "qualified_bounded_arabic")

    def test_glucometer_prefers_qualified_on_device_lane(self):
        decision = choose_ocr_lane(
            OcrRequest(modality="glucometer", script="unknown"),
            OcrCapabilities(
                on_device_glucometer_qualified=True,
                governed_cloud_allowed=True,
            ),
        )

        self.assertEqual(decision.lane, "on_device_ocr")
        self.assertFalse(decision.external_egress)

    def test_unknown_script_never_silently_falls_to_unqualified_local_ocr(self):
        decision = choose_ocr_lane(
            OcrRequest(modality="document_image", script="unknown"),
            OcrCapabilities(
                local_latin_qualified=True,
                local_arabic_full_qualified=True,
                governed_cloud_allowed=False,
            ),
        )

        self.assertEqual(decision.lane, "unavailable")
        self.assertEqual(decision.reason, "script_unknown_no_qualified_lane")
