"""Bounded external model narration for the public IAMINA demo.

This path is intentionally separate from patient egress. It accepts no patient
identity/context, persists no turns, rejects common identifiers before network
egress, and fails closed to the deterministic demo responder.
"""
from __future__ import annotations

import json
import os

from companion.output_guard import contains_unapproved_behavior_action
from core.ai_egress import _detect_sensitive_text
from core.input_safety import INSULIN_BLOCK, PRESCRIPTION_BLOCK, URGENT, evaluate_input_safety
from core.medical_safety import no_prescription_message
from llm.provider_registry import build_openai_compatible_provider

_SYSTEM = """You are IAmina in PUBLIC DEMO mode.
You have NO patient record, NO memory, NO clinical measurements and NO identity.
Reply naturally and briefly in the user's language. Understand Moroccan Darija,
including Latin-script Darija such as "fia doukha" (I feel dizzy).
For symptoms, acknowledge what the user said and ask at most one useful,
non-diagnostic follow-up question. Never diagnose, prescribe, calculate doses,
change treatment, or invent patient facts. Never claim access to a dossier.
Do not give medication doses or treatment changes. Keep answers under 80 words.
Return only the reply text."""
_ENABLED = "IAMINA_DEMO_EXTERNAL_AI_ENABLED"
_PROVIDER = "IAMINA_DEMO_LLM_PROVIDER"


class DemoModelUnavailable(RuntimeError):
    pass


class DemoPayloadDenied(ValueError):
    pass


def demo_model_enabled() -> bool:
    return os.environ.get(_ENABLED, "").strip().lower() in {"1", "true", "yes"}


def _provider_id() -> str:
    provider = os.environ.get(_PROVIDER, "groq").strip().lower()
    if provider not in {"groq"}:
        raise DemoModelUnavailable("unsupported demo provider")
    return provider


def _extract_reply(content: str) -> str:
    text = (content or "").strip()
    if not text:
        raise DemoModelUnavailable("empty demo model response")
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return text
    if isinstance(parsed, dict) and isinstance(parsed.get("reply"), str):
        return parsed["reply"].strip()
    return text


def generate_demo_reply(message: str, language: str) -> str:
    """Generate one bounded public-demo reply or fail closed.

    No patient/user object, conversation history or database state enters this call.
    """
    if not demo_model_enabled():
        raise DemoModelUnavailable("demo external model disabled")

    text = (message or "").strip()
    if not text:
        raise DemoPayloadDenied("empty demo message")
    if _detect_sensitive_text(text):
        raise DemoPayloadDenied("identifying data is not allowed in public demo")

    decision = evaluate_input_safety(text, language)
    if decision.action == URGENT:
        raise DemoPayloadDenied("urgent content remains deterministic")
    if decision.action in (INSULIN_BLOCK, PRESCRIPTION_BLOCK):
        return no_prescription_message("ar" if language == "ar-MA" else language)

    provider = build_openai_compatible_provider(_provider_id())
    response = provider.complete(_SYSTEM, text)
    reply = _extract_reply(response.content)
    if not reply or len(reply) > 1200 or contains_unapproved_behavior_action(reply):
        raise DemoModelUnavailable("demo model output rejected by safety guard")
    return reply
