"""Provider-neutral speech-to-text boundary for IAMINA voice input.

The governed public function remains ``transcribe(...)``. Gemini is still the
runtime default, so this refactor does not switch provider or change clinical
behaviour. The provider-specific network call is isolated behind ``STTBackend``
so low-cost candidates can be benchmarked and swapped without touching triage or
conversation logic.

No static price is embedded here. Pricing is versioned separately because model
prices and identifiers are operational data, not durable source-code facts.
"""
from __future__ import annotations

import base64
import logging
import os
from typing import Protocol

from core.ai_egress import AUDIO, AIEgressDenied
from core.ai_processor_policy import AIProcessorPolicyDenied
from llm.errors import LLMProviderError
from llm.runtime import execute_external_provider_call

logger = logging.getLogger(__name__)

SUPPORTED_MIME_TYPES: frozenset[str] = frozenset([
    "audio/mp4",
    "audio/mpeg",
    "audio/webm",
    "audio/wav",
    "audio/ogg",
    "audio/x-m4a",
    "audio/m4a",
    "audio/flac",
])

MAX_AUDIO_BYTES: int = 10 * 1024 * 1024

_LANGUAGE_HINTS: dict[str, str] = {
    "fr": "French",
    "ar": "Modern Standard Arabic (Fusha / MSA)",
}

_STT_SYSTEM = (
    "You are a specialist medical transcription assistant for a diabetes care app. "
    "Transcribe the audio EXACTLY as spoken, preserving the original language and dialect. "
    "Never translate, summarise, paraphrase, or add any commentary. "
    "Numeric values (blood glucose, HbA1c, insulin doses) are medically critical — "
    "transcribe them with maximum accuracy."
)

_STT_USER_TEMPLATE = (
    "Transcribe this audio. The speaker uses {language_hint}. "
    "Return ONLY the verbatim transcription — no timestamps, no labels, no explanation. "
    "If the audio is silent or inaudible, return an empty string."
)


class TranscriptionError(Exception):
    """Raised when the selected STT backend cannot complete safely."""


class STTBackend(Protocol):
    """Minimal interchangeable boundary for speech transcription providers."""

    name: str

    def transcribe(
        self,
        audio_bytes: bytes,
        mime_type: str,
        *,
        language: str,
        language_hint: str,
    ) -> str: ...


class GeminiSTTBackend:
    """Current production-compatible STT backend. Behaviour matches the old path."""

    name = "gemini"
    model = "gemini-2.5-flash"

    def transcribe(
        self,
        audio_bytes: bytes,
        mime_type: str,
        *,
        language: str,
        language_hint: str,
    ) -> str:
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise TranscriptionError("GEMINI_API_KEY not set — STT unavailable.")

        user_prompt = _STT_USER_TEMPLATE.format(language_hint=language_hint)
        audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")

        try:
            from google import genai

            client = genai.Client(
                api_key=api_key,
                http_options={"api_version": "v1alpha"},
            )
            response = execute_external_provider_call(
                "gemini",
                AUDIO,
                "transcribe",
                lambda: client.models.generate_content(
                    model=self.model,
                    contents=[
                        {
                            "parts": [
                                {
                                    "inline_data": {
                                        "mime_type": mime_type,
                                        "data": audio_b64,
                                    }
                                },
                                {"text": user_prompt},
                            ]
                        }
                    ],
                    config={
                        "system_instruction": _STT_SYSTEM,
                        "temperature": 0.0,
                    },
                ),
            )
            return (response.text or "").strip()
        except (AIEgressDenied, AIProcessorPolicyDenied, LLMProviderError):
            raise
        except Exception:
            logger.exception("STT: Gemini transcription failed (lang=%s)", language)
            raise TranscriptionError(
                "STT request could not be completed safely."
            ) from None


_DEFAULT_BACKEND: STTBackend = GeminiSTTBackend()


def transcribe(
    audio_bytes: bytes,
    mime_type: str,
    language: str = "fr",
    language_hints: dict | None = None,
    *,
    backend: STTBackend | None = None,
) -> str:
    """Transcribe validated audio through an interchangeable STT backend.

    ``backend`` is injectable for benchmark/testing lanes. Runtime callers omit it
    and therefore preserve the existing Gemini behaviour until a separately
    benchmarked and authorized provider cutover occurs.
    """
    if len(audio_bytes) > MAX_AUDIO_BYTES:
        raise ValueError(
            f"Audio too large: {len(audio_bytes):,} bytes (max {MAX_AUDIO_BYTES:,})"
        )
    if mime_type not in SUPPORTED_MIME_TYPES:
        raise ValueError(f"Unsupported audio format: {mime_type!r}")

    hints_table = language_hints if language_hints is not None else _LANGUAGE_HINTS
    language_hint = hints_table.get(language, "French or Arabic")
    selected = backend or _DEFAULT_BACKEND
    transcript = selected.transcribe(
        audio_bytes,
        mime_type,
        language=language,
        language_hint=language_hint,
    ).strip()

    logger.info(
        "STT: backend=%s bytes=%d mime=%s lang=%s transcript_chars=%d",
        selected.name,
        len(audio_bytes),
        mime_type,
        language,
        len(transcript),
    )
    return transcript
