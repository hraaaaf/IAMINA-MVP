"""Public-demo adapter onto the production IAmina runtime."""

from __future__ import annotations

from django.utils import timezone

import companion.demo_runtime as companion_demo_runtime
from companion.conversation import detect_language
from core.ai_egress import TEXT, ai_egress_scope
from core.emergency_response import compose_emergency_for_patient
from core.input_safety import INSULIN_BLOCK, PRESCRIPTION_BLOCK, URGENT, evaluate_input_safety
from core.medical_safety import no_prescription_message
from diabetes.services.demo_patient import get_or_create_synthetic_demo_patient


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
            patient=patient,
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
