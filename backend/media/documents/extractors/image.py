"""
Image extractor — Phase 12 Document Pulper.

Accepts raw image bytes (JPEG, PNG, WEBP, HEIC) and returns the raw text
extracted by Gemini Vision.

Unlike the meal-photo flow (which identifies food names), this extractor asks
Gemini to read ALL text visible in the image — acting as a smarter OCR.
The pulper.py then sends that text to the LLM parsing prompt.
"""
from __future__ import annotations

import base64
import logging

from core.ai_egress import IMAGE, AIEgressDenied
from core.ai_processor_policy import AIProcessorPolicyDenied
from llm.runtime import execute_external_provider_call

logger = logging.getLogger(__name__)

_ALLOWED_MIME = frozenset({"image/jpeg", "image/png", "image/webp", "image/heic"})
_MAX_BYTES = 15 * 1_024 * 1_024   # 15 MB — Gemini limit
OCR_MODEL = "gemini-2.0-flash"


def extract_image(file_bytes: bytes, mime_type: str) -> str:
    """
    Use Gemini Vision to transcribe all visible text in the image.

    Returns extracted text, or '' on failure (caller adds error to output).
    """
    if mime_type not in _ALLOWED_MIME:
        logger.warning("image_extractor: unsupported MIME %s", mime_type)
        return ''

    if len(file_bytes) > _MAX_BYTES:
        logger.warning("image_extractor: file too large (%d bytes)", len(file_bytes))
        return ''

    b64 = base64.b64encode(file_bytes).decode('ascii')

    try:
        import os

        import google.generativeai as genai

        genai.configure(api_key=os.environ['GEMINI_API_KEY'])
        model = genai.GenerativeModel(OCR_MODEL)

        response = execute_external_provider_call(
            "gemini",
            IMAGE,
            "document_image_ocr",
            lambda: model.generate_content(
                contents=[
                    {
                        "parts": [
                            {
                                "inline_data": {
                                    "mime_type": mime_type,
                                    "data": b64,
                                }
                            },
                            {
                                "text": (
                                    "Transcribe ALL visible text from this image exactly as written. "
                                    "Include numbers, dates, units, labels, and table content. "
                                    "Preserve the structure with newlines. "
                                    "Do NOT interpret or summarise — only transcribe. "
                                    "Return plain text only."
                                )
                            },
                        ]
                    }
                ]
            ),
        )
        return response.text or ''

    except (AIEgressDenied, AIProcessorPolicyDenied):
        raise

    except KeyError:
        logger.error("image_extractor: GEMINI_API_KEY not set.")
        return ''
    except Exception as exc:
        logger.warning("image_extractor: Gemini Vision failed: %s", exc)
        return ''
