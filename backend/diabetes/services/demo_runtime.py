"""Public-demo adapter onto the production IAmina runtime."""

from __future__ import annotations

import os

from django.utils import timezone

import companion.demo_runtime as companion_demo_runtime
from companion.conversation import detect_language
from companion.demo import reply_to_demo_message
from companion.intent_envelope import RouteKind
from companion.intent_pipeline import analyze_unresolved_turn
from core.ai_egress import TEXT, ai_egress_scope
from core.emergency_response import compose_emergency_for_patient
from core.input_safety import INSULIN_BLOCK, PRESCRIPTION_BLOCK, URGENT, evaluate_input_safety
from core.medical_safety import no_prescription_message
from diabetes.services.demo_patient import get_or_create_synthetic_demo_patient
from llm.provider_registry import build_openai_compatible_provider



_INTENT_PREVIEW_ENABLED = "IAMINA_DEMO_INTENT_ROUTER_ENABLED"
_INTENT_PREVIEW_MODEL = "IAMINA_INTENT_ROUTER_LLM_MODEL"


def _intent_preview_enabled() -> bool:
    return os.environ.get(_INTENT_PREVIEW_ENABLED, "").strip().lower() in {"1", "true", "yes"}


def _clarify_reply(language: str) -> str:
    if language == "en":
        return "I’m not fully sure what you want yet. Do you want me to retrieve a recorded item, explain something generally, or just chat?"
    if language == "ar-MA":
        return "Mazal ma fhemtch bddabt chno bghiti. Bghiti n9elleb 3la data msjla, nchra7 lik chi haja b sifa 3amma, wela ghir nhdro?"
    if language == "ar":
        return "لست متأكدًا تمامًا مما تريده. هل تريد استرجاع معلومة مسجلة، شرحًا عامًا، أم مجرد محادثة؟"
    return "Je ne suis pas encore certain de ce que tu veux. Tu veux que je retrouve une donnée enregistrée, que je t’explique quelque chose en général, ou simplement discuter ?"


def _preview_route_reply(message: str, language: str) -> tuple[RouteKind, str] | None:
    if not _intent_preview_enabled():
        return None
    provider = build_openai_compatible_provider(
        "groq",
        model=os.environ.get(_INTENT_PREVIEW_MODEL, "").strip() or "openai/gpt-oss-120b",
    )
    outcome = analyze_unresolved_turn(message, language, provider=provider)
    if outcome.decision.route is RouteKind.CLARIFY:
        return outcome.decision.route, _clarify_reply(language)
    if outcome.decision.route in {RouteKind.DETERMINISTIC_LOCAL, RouteKind.CONVERSATIONAL}:
        demo = reply_to_demo_message(message, language, history=[])
        return outcome.decision.route, demo["reply"]
    return outcome.decision.route, ""

def reply_with_synthetic_patient(
    message: str,
    *,
    language: str,
    subject_key: str,
) -> dict:
    patient = get_or_create_synthetic_demo_patient(subject_key)
    reply_language = detect_language(message, language)
    decision = evaluate_input_safety(message, reply_language)

    if decision.action == URGENT:
        emergency = compose_emergency_for_patient(
            decision,
            patient=None,
            language=reply_language,
            message=message,
        )
        return {
            "reply": emergency.reply,
            "conversation_id": emergency.conversation_id,
            "timestamp": timezone.now().isoformat(),
            "is_emergency": True,
            "reply_language": emergency.reply_language,
        }

    if decision.action in (INSULIN_BLOCK, PRESCRIPTION_BLOCK):
        return {
            "reply": no_prescription_message(reply_language),
            "conversation_id": f"conv-demo-{subject_key[:12]}",
            "timestamp": timezone.now().isoformat(),
            "is_emergency": False,
            "reply_language": reply_language,
        }

    try:
        preview = _preview_route_reply(message, reply_language)
    except Exception:
        preview = (RouteKind.CLARIFY, _clarify_reply(reply_language))
    if preview is not None:
        route, preview_reply = preview
        if route in {RouteKind.DETERMINISTIC_LOCAL, RouteKind.CONVERSATIONAL, RouteKind.CLARIFY}:
            return {
                "reply": preview_reply,
                "conversation_id": f"conv-demo-{subject_key[:12]}",
                "timestamp": timezone.now().isoformat(),
                "is_emergency": False,
                "reply_language": reply_language,
            }

    try:
        with ai_egress_scope(patient.id, "companion_chat", TEXT):
            reply = companion_demo_runtime.IAmina(patient, reply_language).chat(
                message,
                context_days=14,
            )
    except Exception:
        reply = "Désolé, une erreur inattendue s'est produite. Réessaie dans quelques instants."

    return {
        "reply": reply,
        "conversation_id": f"conv-demo-{subject_key[:12]}",
        "timestamp": timezone.now().isoformat(),
        "is_emergency": False,
        "reply_language": reply_language,
    }
