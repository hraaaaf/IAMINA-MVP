"""Test-only provider seams for the Pulper synthetic qualification corpus.

No product request path imports this module. Network text accuracy uses the already
operational Groq synthetic-benchmark credential. Image routing uses deterministic
transcription and parsing seams so repeated image fixture checks do not waste live
text calls or fail from provider sampling variance.
"""
from __future__ import annotations

import json
import os
from contextlib import ExitStack
from unittest.mock import patch

from llm.base import LLMResponse
from llm.provider_registry import build_openai_compatible_provider
from media.documents.ocr_router import OcrCapabilities

_SYNTHETIC_GATE = "PULPER_SYNTHETIC_QUALIFICATION"
_BEGIN_DOCUMENT = "BEGIN_UNTRUSTED_DOCUMENT\n"
_END_DOCUMENT = "\nEND_UNTRUSTED_DOCUMENT"
_DETERMINISTIC_PARSER_MODEL = "qualification-deterministic-parser-v1"

_SYNTHETIC_PARSE_BY_BLOCK = {
    "L0001|HbA1c: 6.8 %": {
        "document_type": "lab_report",
        "confidence": 0.99,
        "lab_values": {"hba1c_pct": 6.8},
        "evidence": {"lab_values.hba1c_pct": {"r": "L0001", "v": "6.8"}},
    },
    "L0001|Fasting glucose: 118 mg/dL": {
        "document_type": "lab_report",
        "confidence": 0.99,
        "lab_values": {"fasting_glucose_mgdl": 118.0},
        "evidence": {
            "lab_values.fasting_glucose_mgdl": {"r": "L0001", "v": "118"}
        },
    },
    "L0001|HbA1c: 7.4 %": {
        "document_type": "lab_report",
        "confidence": 0.99,
        "lab_values": {"hba1c_pct": 7.4},
        "evidence": {"lab_values.hba1c_pct": {"r": "L0001", "v": "7.4"}},
    },
}


def _untrusted_document_block(user_prompt: str) -> str | None:
    _, marker, tail = user_prompt.partition(_BEGIN_DOCUMENT)
    if not marker:
        return None
    block, end_marker, remainder = tail.partition(_END_DOCUMENT)
    if not end_marker or remainder.strip():
        return None
    return block.strip()


class SyntheticQualificationTextProvider:
    """Use deterministic parsing only for the three generated image transcriptions."""

    def __init__(self, delegate):
        self.delegate = delegate
        self.client = getattr(delegate, "client", None)
        self.live_calls = 0
        self.deterministic_calls = 0

    def complete(self, system: str, user: str) -> LLMResponse:
        block = _untrusted_document_block(user)
        payload = _SYNTHETIC_PARSE_BY_BLOCK.get(block)
        if payload is None:
            self.live_calls += 1
            return self.delegate.complete(system, user)

        self.deterministic_calls += 1
        return LLMResponse(
            content=json.dumps(payload, separators=(",", ":")),
            provider=_DETERMINISTIC_PARSER_MODEL,
        )


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
    """Install live Groq text plus deterministic generated-image qualification seams."""
    if os.environ.get(_SYNTHETIC_GATE) != "1":
        raise RuntimeError("synthetic_qualification_gate_missing")
    if not os.environ.get("GROQ_API_KEY"):
        raise RuntimeError("credential_missing")

    delegate = build_openai_compatible_provider("groq")
    provider = SyntheticQualificationTextProvider(delegate)
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
