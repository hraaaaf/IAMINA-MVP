"""
Speech-to-Text via Gemini Audio API.
=====================================
Gemini 2.5 Flash handles audio inline (base64, ≤ 20 MB).
Pricing: 25 tokens/sec at $0.075/1M ≈ $0.000032 per 10-sec clip.

Language support:
  fr    → French
  ar-MA → Moroccan Darija (dialect + French code-switching)
  ar    → Modern Standard Arabic (Fusha)

D2 extension: accepts language_hints: dict | None = None.
  - When provided, language_hints overrides the built-in hint lookup.
  - The ar-MA vocabulary dict has been extracted to
    diabetes.config.stt_vocabulary.AR_MA_STT_HINTS so that diabetes-domain
    callers can inject it explicitly without coupling to this module.
"""
from __future__ import annotations

import base64
import logging
import os

from core.ai_egress import AUDIO, AIEgressDenied
from core.ai_processor_policy import AIProcessorPolicyDenied
from llm.errors import LLMProviderError
from llm.runtime import execute_external_provider_call

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────

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

MAX_AUDIO_BYTES: int = 10 * 1024 * 1024  # 10 MB — conservative (Gemini limit is 20 MB)

# Built-in language hints for fr and ar (ar-MA removed — lives in stt_vocabulary.py)
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


# ── Exceptions ────────────────────────────────────────────────────────────────

class TranscriptionError(Exception):
    """Raised when the Gemini Audio API call fails."""


# ── Public API ────────────────────────────────────────────────────────────────

def transcribe(
    audio_bytes: bytes,
    mime_type: str,
    language: str = "fr",
    language_hints: dict | None = None,
) -> str:
    """
    Transcribe audio_bytes via Gemini Audio (inline base64).

    Args:
        audio_bytes:    Raw audio content (mp4 / webm / wav / ogg / m4a / flac).
        mime_type:      MIME type of the audio (e.g. "audio/mp4").
        language:       Patient preferred_language code — drives the language hint
                        injected into the STT prompt for better Darija accuracy.
        language_hints: Optional override dict {lang_code: hint_str}.
                        When provided, this dict is used instead of the built-in
                        _LANGUAGE_HINTS table for the hint lookup.
                        Callers such as diabetes.api.v1.voice pass
                        AR_MA_STT_HINTS from diabetes.config.stt_vocabulary so
                        the full Darija medical vocabulary is applied.

    Returns:
        Transcription string. May be empty if audio is silent / inaudible.

    Raises:
        ValueError:          Unsupported MIME type or file exceeds MAX_AUDIO_BYTES.
        TranscriptionError:  Gemini API call failed.
    """
    if len(audio_bytes) > MAX_AUDIO_BYTES:
        raise ValueError(
            f"Audio too large: {len(audio_bytes):,} bytes (max {MAX_AUDIO_BYTES:,})"
        )
    if mime_type not in SUPPORTED_MIME_TYPES:
        raise ValueError(f"Unsupported audio format: {mime_type!r}")

    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise TranscriptionError("GEMINI_API_KEY not set — STT unavailable.")

    # Resolve language hint — caller-supplied dict takes precedence
    hints_table = language_hints if language_hints is not None else _LANGUAGE_HINTS
    language_hint = hints_table.get(language, "French or Arabic")
    user_prompt   = _STT_USER_TEMPLATE.format(language_hint=language_hint)
    audio_b64     = base64.b64encode(audio_bytes).decode("utf-8")

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
                model="gemini-2.5-flash",
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

        transcript = (response.text or "").strip()
        logger.info(
            "STT: %d bytes (%s, lang=%s) → %d chars transcript",
            len(audio_bytes), mime_type, language, len(transcript),
        )
        return transcript

    except (AIEgressDenied, AIProcessorPolicyDenied, LLMProviderError):
        raise
    except Exception:
        logger.exception("STT: transcription failed (lang=%s)", language)
        raise TranscriptionError("STT request could not be completed safely.") from None
