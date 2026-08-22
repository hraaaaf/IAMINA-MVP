from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase

from media.documents.extractors.image import extract_image
from media.documents.ocr_router import OcrCapabilities, OcrRequest
from media.documents.security import DocumentSecurityError


class _FakeVisionBackend:
    name = "fake-vision"

    def generate(
        self,
        image_b64,
        mime_type,
        *,
        system_prompt,
        user_prompt,
        purpose,
        temperature,
    ):
        return "HbA1c 6.7 %"


class OcrRouteRuntimeTelemetryTest(SimpleTestCase):
    def test_image_route_decision_is_metered_before_cloud_execution(self):
        request = OcrRequest(
            modality="document_image",
            script="arabic",
            bounded_capture=False,
        )

        with (
            patch(
                "media.documents.extractors.image.inspect_document",
                return_value=SimpleNamespace(kind="jpeg", mime_type="image/jpeg"),
            ),
            patch(
                "media.documents.extractors.image._runtime_ocr_capabilities",
                return_value=OcrCapabilities(governed_cloud_allowed=True),
            ),
            patch(
                "media.documents.extractors.image.record_ocr_route",
            ) as record,
        ):
            text = extract_image(
                b"synthetic",
                "image/jpeg",
                backend=_FakeVisionBackend(),
                request=request,
            )

        self.assertEqual(text, "HbA1c 6.7 %")
        record.assert_called_once_with(
            modality="document_image",
            script="arabic",
            bounded_capture=False,
            lane="governed_cloud_ocr",
        )

    def test_unavailable_route_is_metered_before_fail_closed(self):
        request = OcrRequest(
            modality="document_image",
            script="unknown",
            bounded_capture=False,
        )

        with (
            patch(
                "media.documents.extractors.image.inspect_document",
                return_value=SimpleNamespace(kind="jpeg", mime_type="image/jpeg"),
            ),
            patch(
                "media.documents.extractors.image._runtime_ocr_capabilities",
                return_value=OcrCapabilities(),
            ),
            patch(
                "media.documents.extractors.image.record_ocr_route",
            ) as record,
        ):
            with self.assertRaisesRegex(DocumentSecurityError, "image_ocr_unavailable"):
                extract_image(
                    b"synthetic",
                    "image/jpeg",
                    backend=_FakeVisionBackend(),
                    request=request,
                )

        record.assert_called_once_with(
            modality="document_image",
            script="unknown",
            bounded_capture=False,
            lane="unavailable",
        )
