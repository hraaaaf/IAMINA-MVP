"""Test-only provider seams for the Pulper synthetic qualification corpus.

No product request path imports this module. Network text accuracy uses the already
operational Groq synthetic-benchmark credential. Image routing uses a deterministic
transcription seam so the benchmark does not pretend to measure live Gemini OCR.
"""
from __future__ import annotations

import os
from contextlib import ExitStack
from unittest.mock import patch

from llm.provider_registry import build_openai_compatible_provider
from media.documents.ocr_router import OcrCapabilities

_SYNTHETIC_GATE = "PULPER_SYNTHETIC_QUALIFICATION"


class SyntheticQualificationVisionBackend:
    """Deterministic transcription for generated image fixtures only."""

    name = "qualification-synthetic-vision"
    model = "qualification-synthetic-vision-v1"
    _TEXT_BY_MIME = {
        "image/jpeg": "HbA1c: 6.8 %",
        "image/png": "Fasting glucose: 118 mg/dL",
        "image/webp": "HbA1c: 7.4 %",
    }

    def generate(
        self,
        image_b64: str,
        mime_type: str,
        *,
        system_prompt: str,
        user_prompt: str,
        purpose: str,
        temperature: float,
    ) -> str:
        del image_b64, system_prompt, user_prompt, purpose, temperature
        try:
            return self._TEXT_BY_MIME[mime_type]
        except KeyError as exc:
            raise RuntimeError("synthetic_vision_fixture_unmapped") from exc


def install_synthetic_groq(stack: ExitStack):
    """Install raw Groq text + deterministic vision only for synthetic qualification."""
    if os.environ.get(_SYNTHETIC_GATE) != "1":
        raise RuntimeError("synthetic_qualification_gate_missing")
    if not os.environ.get("GROQ_API_KEY"):
        raise RuntimeError("credential_missing")

    provider = build_openai_compatible_provider("groq")
    vision = SyntheticQualificationVisionBackend()

    stack.enter_context(patch("llm.factory.get_llm", return_value=provider))
    stack.enter_context(
        patch("diabetes.services.documents.pulper.assert_ai_egress_allowed")
    )
    # FRUG-2 keeps product OCR fail-closed. Only this synthetic, env-gated
    # qualification seam marks the deterministic fixture lane as executable.
    stack.enter_context(
        patch(
            "media.documents.extractors.image._runtime_ocr_capabilities",
            return_value=OcrCapabilities(governed_cloud_allowed=True),
        )
    )
    stack.enter_context(
        patch(
            "media.documents.extractors.image.GeminiVisionBackend",
            return_value=vision,
        )
    )
    stack.enter_context(
        patch("diabetes.services.documents.pulper.OCR_MODEL", vision.model)
    )
    return provider
