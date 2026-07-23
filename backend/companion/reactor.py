import logging

from companion.advice_filter import apply_advice_throttle
from companion.parser import parse_llm_json
from companion.prompts import REACTION_USER, SYSTEM_BASE, get_language_label
from core.llm_gateway import get_gateway_llm
from core.medical_safety import apply_no_prescription_policy

logger = logging.getLogger(__name__)

# Static fallback messages — safe, non-prescriptive
_FALLBACKS = {
    "encouraging": "Bien noté ! Continue comme ça, chaque mesure compte.",
    "gentle": "C'est enregistré. On continue à surveiller ensemble.",
    "challenge": "Noté. Regardons ça de plus près lors de ta prochaine saisie.",
}


def react(entry, memory, llm=None, language: str = "fr", deep=None, patient=None) -> str:
    """Mode 2: Post-log reaction — short empathetic response after a glucose entry."""
    if llm is None:
        llm = get_gateway_llm()

    glucose = getattr(entry, "blood_sugar", None)
    meal = getattr(entry, "meal_type", "") or "non précisé"
    notes = getattr(entry, "notes", "") or ""

    # PHI: mask patient name in free-text notes before LLM — no unmask needed (notes not echoed)
    first_name = ""
    if patient is not None:
        first_name = getattr(patient, "first_name", "") or ""
    if first_name and notes:
        from llm.pseudonymizer import PHIPseudonymizer  # lazy import — avoids circular imports
        notes = PHIPseudonymizer().mask_patient_identity(first_name, notes)[1]

    system = SYSTEM_BASE.format(language=get_language_label(language), tone=memory.current_tone or "encouraging")
    user_prompt = REACTION_USER.format(
        glucose=f"{glucose:.2f}" if glucose else "?",
        meal=meal,
        context=notes or "aucun contexte",
    )

    try:
        result = llm.complete(system, user_prompt)
        parsed = parse_llm_json(result.content, ["message", "tone_detected"])

        # Persist detected tone override in memory
        tone_detected = parsed.get("tone_detected", "").strip()
        if tone_detected in ("encouraging", "gentle", "challenge"):
            memory.current_tone = tone_detected

        reply = parsed["message"] or _fallback(memory.current_tone)

    except Exception:
        logger.exception("IAmina reactor.react failed for entry=%s", getattr(entry, "id", "?"))
        reply = _fallback(memory.current_tone)

    if deep is not None:
        reply = apply_advice_throttle(reply, deep)
        reply = apply_no_prescription_policy(reply, language)
        deep.save()

    return reply


def _fallback(tone: str) -> str:
    return _FALLBACKS.get(tone, _FALLBACKS["gentle"])
