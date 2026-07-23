"""
Phase 11-C: On-device meal photo recognition via Gemini Vision.

Architecture:
  • Input shield (MealVisionShield) validates mime type, size, and base64 encoding
    BEFORE any LLM call — same discipline as GlucoseOcrShield on the Flutter side.
  • Prompt is English Pivot (ADR-0007): image content is not patient data,
    but we keep the analysis layer in English for consistency.
  • Response shield: caps at 8 foods, strips >60-char items, sanitises encoding.
  • analyze_meal_image() NEVER raises — always returns a result dict.
    The endpoint maps fallback=True to a user-friendly "couldn't detect" message.

No clinical decisions are made here — this is purely food identification.
All glucose-related interpretation stays in the clinical engine.
"""
from __future__ import annotations

import base64
import json
import logging
import os
from typing import Optional

from core.ai_egress import IMAGE, assert_ai_egress_allowed
logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────

_ALLOWED_MIME_TYPES = frozenset({"image/jpeg", "image/png", "image/webp"})
_MAX_B64_LEN = 10 * 1_024 * 1_024   # ~7.5 MB decoded — hard reject above this
_MAX_FOODS   = 8

# English Pivot prompt — LLM works in English, output in French for UI matching.
# ADR-0007: no patient glucose data in this prompt; only food identification.
_MEAL_SYSTEM = (
    "You are a food recognition specialist for a diabetes management app. "
    "Your only task is to identify visible foods in meal photos."
)

_MEAL_USER = (
    "Identify the visible foods and ingredients in this meal photograph.\n"
    "Return ONLY valid JSON in this exact format:\n"
    "{\"foods\": [\"food_name_1\", \"food_name_2\"]}\n\n"
    "Rules:\n"
    "- Use simple French food names (e.g. \"pain\", \"poulet rôti\", \"riz\", \"salade\")\n"
    "- List only clearly visible items — never guess or infer\n"
    "- Maximum 8 items\n"
    "- No descriptions, portions, quantities, or adjectives beyond the food name\n"
    "- If no food is visible or the image is unclear, return: {\"foods\": []}\n"
    "- Return ONLY the JSON object, no other text, no markdown fences"
)


# ── Input / Output Shield ─────────────────────────────────────────────────────

class MealVisionShield:
    """
    Deterministic validation layer — runs before and after the LLM call.
    Same philosophy as GlucoseOcrShield: lock all input/output gates.
    """

    @staticmethod
    def validate_input(image_b64: str, mime_type: str) -> Optional[str]:
        """
        Returns an error string if the input is invalid, None if OK.
        Fast checks run first to avoid unnecessary base64 decoding.
        """
        if mime_type not in _ALLOWED_MIME_TYPES:
            return f"Type d'image non supporté : {mime_type} (JPEG, PNG ou WebP requis)"
        if len(image_b64) > _MAX_B64_LEN:
            return "Image trop lourde (maximum ~7.5 Mo)"
        try:
            base64.b64decode(image_b64, validate=True)
        except Exception:
            return "Encodage base64 invalide"
        return None

    @staticmethod
    def sanitise_foods(raw: list) -> list[str]:
        """
        Post-LLM output sanitisation:
          - Each item must be a non-empty string
          - Truncated to 60 chars
          - Max _MAX_FOODS items
        """
        cleaned = []
        for item in raw:
            if not isinstance(item, str):
                continue
            item = item.strip()[:60]
            if len(item) >= 2:
                cleaned.append(item)
        return cleaned[:_MAX_FOODS]


# ── Main entry point ──────────────────────────────────────────────────────────

def analyze_meal_image(image_b64: str, mime_type: str) -> dict:
    """
    Call Gemini Vision to identify foods in a meal photo.

    Returns:
        {
            "foods":      list[str],   # French food names, max 8
            "confidence": "high" | "medium" | "low",
            "fallback":   bool,        # True if LLM failed or returned empty
        }

    Never raises — all exceptions produce fallback=True with an empty food list.
    The caller should show a user-facing "couldn't detect" message when fallback=True.
    """
    raw_text = ""

    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        logger.warning("meal_vision: No Gemini API key — returning empty fallback")
        return _fallback()

    try:
        assert_ai_egress_allowed(IMAGE)
        from google import genai
        from google.genai import types as genai_types

        client = genai.Client(
            api_key=api_key,
            http_options={"api_version": "v1alpha"},
        )

        # Decode base64 → raw bytes, then use SDK Part.from_bytes so the SDK
        # handles the exact wire-format for the current genai SDK version.
        image_bytes = base64.b64decode(image_b64)
        contents = [
            genai_types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
            genai_types.Part.from_text(text=_MEAL_USER),
        ]

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=contents,
            config=genai_types.GenerateContentConfig(
                system_instruction=_MEAL_SYSTEM,
                temperature=0.1,
            ),
        )

        raw_text = response.text.strip() if response.text else ""

        # Strip markdown code fences if Gemini added them despite the prompt
        if raw_text.startswith("```"):
            lines = raw_text.splitlines()
            raw_text = "\n".join(
                ln for ln in lines if not ln.strip().startswith("```")
            ).strip()

        parsed = json.loads(raw_text)
        foods  = MealVisionShield.sanitise_foods(parsed.get("foods", []))

        if not foods:
            return _fallback()

        confidence = (
            "high"   if len(foods) >= 3 else
            "medium" if len(foods) >= 1 else
            "low"
        )
        return {"foods": foods, "confidence": confidence, "fallback": False}

    except json.JSONDecodeError:
        logger.warning("meal_vision: LLM returned non-JSON — raw: %s", raw_text[:300])
        return _fallback()

    except Exception:
        logger.exception("meal_vision: Gemini Vision call failed")
        return _fallback()


def _fallback() -> dict:
    return {"foods": [], "confidence": "low", "fallback": True}


# ── Glucometer OCR (Phase 11-D web) ──────────────────────────────────────────

_GLUCO_SYSTEM = (
    "You are a medical OCR specialist. Your only task is to read blood glucose values "
    "from glucometer display photos."
)

_GLUCO_USER = (
    "Read the blood glucose value from this glucometer photo.\n"
    "Return ONLY valid JSON:\n"
    "{\"value\": <number or null>, \"unit\": \"<mg/dL or mmol/L>\", \"confidence\": \"<high/medium/low>\"}\n\n"
    "Rules:\n"
    "- value: the numeric reading (integer or one decimal). null if not visible.\n"
    "- unit: exactly \"mg/dL\" or \"mmol/L\" based on what is shown on the display.\n"
    "  If unit is not visible: guess from value magnitude (>30 → mg/dL, ≤30 → mmol/L).\n"
    "- confidence: \"high\" if display is clear, \"medium\" if partially visible, \"low\" if unclear.\n"
    "- Return ONLY the JSON, no markdown fences, no extra text."
)


def analyze_glucometer_image(image_b64: str, mime_type: str) -> dict:
    """
    Extract glucose reading from a glucometer photo via Gemini Vision.
    Used as web fallback when ML Kit (mobile-only) is unavailable.

    Returns:
        {"value": float|None, "unit": "mg/dL"|"mmol/L", "confidence": str, "fallback": bool}
    Never raises.
    """
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        logger.warning("glucometer_vision: No Gemini API key — returning fallback")
        return _gluco_fallback()

    try:
        assert_ai_egress_allowed(IMAGE)
        from google import genai
        from google.genai import types as genai_types

        client = genai.Client(
            api_key=api_key,
            http_options={"api_version": "v1alpha"},
        )
        image_bytes = base64.b64decode(image_b64)
        contents = [
            genai_types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
            genai_types.Part.from_text(text=_GLUCO_USER),
        ]
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=contents,
            config=genai_types.GenerateContentConfig(
                system_instruction=_GLUCO_SYSTEM,
                temperature=0.0,
            ),
        )
        raw = response.text.strip() if response.text else ""
        if raw.startswith("```"):
            raw = "\n".join(ln for ln in raw.splitlines() if not ln.strip().startswith("```")).strip()

        parsed = json.loads(raw)
        value = parsed.get("value")
        if value is not None:
            value = float(value)
        unit       = parsed.get("unit", "mg/dL")
        confidence = parsed.get("confidence", "low")

        if unit not in ("mg/dL", "mmol/L"):
            unit = "mg/dL"
        if confidence not in ("high", "medium", "low"):
            confidence = "low"

        return {"value": value, "unit": unit, "confidence": confidence, "fallback": value is None}

    except (json.JSONDecodeError, KeyError, ValueError):
        logger.warning("glucometer_vision: non-JSON or bad structure from LLM")
        return _gluco_fallback()
    except Exception:
        logger.exception("glucometer_vision: Gemini Vision call failed")
        return _gluco_fallback()


def _gluco_fallback() -> dict:
    return {"value": None, "unit": "mg/dL", "confidence": "low", "fallback": True}
