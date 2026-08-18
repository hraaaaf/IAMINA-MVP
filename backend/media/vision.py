"""Provider-neutral vision boundary for IAMINA meal and glucometer media.

Clinical interpretation remains outside this module. Deterministic input/output
shields run before/after provider generation. Gemini remains the runtime default;
this refactor only isolates provider invocation so cheaper candidates can later be
benchmarked without changing endpoint or clinical code.
"""
from __future__ import annotations

import base64
import json
import logging
import os
from typing import Optional, Protocol

from core.ai_egress import IMAGE, AIEgressDenied
from core.ai_processor_policy import AIProcessorPolicyDenied
from llm.runtime import execute_external_provider_call

logger = logging.getLogger(__name__)

_ALLOWED_MIME_TYPES = frozenset({"image/jpeg", "image/png", "image/webp"})
_MAX_B64_LEN = 10 * 1_024 * 1_024
_MAX_FOODS = 8

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

_GLUCO_SYSTEM = (
    "You are a medical OCR specialist. Your only task is to read blood glucose values "
    "from glucometer display photos."
)

# Safety-sensitive unit semantics are intentionally preserved unchanged in this
# provider-portability refactor. Any future fail-closed unit-policy change must be
# reviewed separately from cost/provider work.
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


class MealVisionShield:
    """Deterministic input and output validation for vision calls."""

    @staticmethod
    def validate_input(image_b64: str, mime_type: str) -> Optional[str]:
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
        cleaned = []
        for item in raw:
            if not isinstance(item, str):
                continue
            item = item.strip()[:60]
            if len(item) >= 2:
                cleaned.append(item)
        return cleaned[:_MAX_FOODS]


class VisionBackend(Protocol):
    """Minimal provider boundary shared by meal vision and web OCR fallback."""

    name: str

    def generate(
        self,
        image_b64: str,
        mime_type: str,
        *,
        system_prompt: str,
        user_prompt: str,
        purpose: str,
        temperature: float,
    ) -> str: ...


class GeminiVisionBackend:
    """Current runtime-compatible backend; no provider cutover is implied."""

    name = "gemini"
    model = "gemini-2.5-flash"

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
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError("Gemini vision credential is not configured")

        from google import genai
        from google.genai import types as genai_types

        client = genai.Client(
            api_key=api_key,
            http_options={"api_version": "v1alpha"},
        )
        image_bytes = base64.b64decode(image_b64)
        contents = [
            genai_types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
            genai_types.Part.from_text(text=user_prompt),
        ]
        response = execute_external_provider_call(
            "gemini",
            IMAGE,
            purpose,
            lambda: client.models.generate_content(
                model=self.model,
                contents=contents,
                config=genai_types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=temperature,
                ),
            ),
        )
        return response.text.strip() if response.text else ""


_DEFAULT_BACKEND: VisionBackend = GeminiVisionBackend()


def _strip_fences(raw: str) -> str:
    if not raw.startswith("```"):
        return raw
    return "\n".join(
        line for line in raw.splitlines() if not line.strip().startswith("```")
    ).strip()


def analyze_meal_image(
    image_b64: str,
    mime_type: str,
    *,
    backend: VisionBackend | None = None,
) -> dict:
    """Identify visible foods; never performs clinical interpretation."""
    error = MealVisionShield.validate_input(image_b64, mime_type)
    if error:
        logger.warning("meal_vision: input rejected before provider call — %s", error)
        return _fallback()

    selected = backend or _DEFAULT_BACKEND
    raw_text = ""
    try:
        raw_text = selected.generate(
            image_b64,
            mime_type,
            system_prompt=_MEAL_SYSTEM,
            user_prompt=_MEAL_USER,
            purpose="meal_vision",
            temperature=0.1,
        )
        parsed = json.loads(_strip_fences(raw_text))
        foods = MealVisionShield.sanitise_foods(parsed.get("foods", []))
        if not foods:
            return _fallback()
        confidence = "high" if len(foods) >= 3 else "medium"
        return {"foods": foods, "confidence": confidence, "fallback": False}
    except (AIEgressDenied, AIProcessorPolicyDenied):
        raise
    except json.JSONDecodeError:
        logger.warning(
            "meal_vision: backend=%s returned non-JSON — raw: %s",
            selected.name,
            raw_text[:300],
        )
        return _fallback()
    except Exception:
        logger.exception("meal_vision: backend=%s call failed", selected.name)
        return _fallback()


def _fallback() -> dict:
    return {"foods": [], "confidence": "low", "fallback": True}


def analyze_glucometer_image(
    image_b64: str,
    mime_type: str,
    *,
    backend: VisionBackend | None = None,
) -> dict:
    """Extract a glucometer reading for the web fallback path."""
    error = MealVisionShield.validate_input(image_b64, mime_type)
    if error:
        logger.warning("glucometer_vision: input rejected before provider call — %s", error)
        return _gluco_fallback()

    selected = backend or _DEFAULT_BACKEND
    try:
        raw = selected.generate(
            image_b64,
            mime_type,
            system_prompt=_GLUCO_SYSTEM,
            user_prompt=_GLUCO_USER,
            purpose="glucometer_ocr",
            temperature=0.0,
        )
        parsed = json.loads(_strip_fences(raw))
        value = parsed.get("value")
        if value is not None:
            value = float(value)
        unit = parsed.get("unit", "mg/dL")
        confidence = parsed.get("confidence", "low")

        if unit not in ("mg/dL", "mmol/L"):
            unit = "mg/dL"
        if confidence not in ("high", "medium", "low"):
            confidence = "low"

        return {
            "value": value,
            "unit": unit,
            "confidence": confidence,
            "fallback": value is None,
        }
    except (AIEgressDenied, AIProcessorPolicyDenied):
        raise
    except (json.JSONDecodeError, KeyError, ValueError):
        logger.warning(
            "glucometer_vision: backend=%s returned invalid structure",
            selected.name,
        )
        return _gluco_fallback()
    except Exception:
        logger.exception("glucometer_vision: backend=%s call failed", selected.name)
        return _gluco_fallback()


def _gluco_fallback() -> dict:
    return {"value": None, "unit": "mg/dL", "confidence": "low", "fallback": True}
