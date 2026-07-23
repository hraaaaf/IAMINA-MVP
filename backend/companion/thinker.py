"""
IAmina Thinker — P3: Thinking Mode (raisonnement caché)
=========================================================
Fait réfléchir IAmina avant de répondre aux messages complexes / émotionnels.
Le raisonnement interne est UNIQUEMENT loggé — jamais montré au patient.
"""
import logging

from core.llm_gateway import get_gateway_llm

logger = logging.getLogger(__name__)


def think_before_reply(
    safe_message: str,    # MUST be pseudonymised by caller — never raw patient text
    memory,               # IAminaMemory
    deep,                 # IAminaDeepMemory
    state,                # IAminaState
    ctx,                  # DomainContext
    llm=None,
    language: str = "fr",
) -> str:
    """
    Fait réfléchir IAmina avant de répondre.
    Retourne le raisonnement interne (loggé, jamais affiché).

    safe_message MUST be pseudonymised before calling (PHIPseudonymizer).
    Passing raw patient text here leaks PII to the external LLM API.
    """
    if llm is None:
        llm = get_gateway_llm()

    from companion.prompts import get_language_label

    thinking_prompt = f"""Patient message: {safe_message}

Clinical context: TIR={ctx.tir_pct}%, CV={ctx.cv_pct}%, patterns={ctx.pattern_codes[:3]}
Patient state: satisfaction={state.satisfaction:.2f}, concern={state.concern_level:.2f}
Relationship: {deep.relationship_stage}, style: {deep.communication_style}
Emotional signals: {memory.emotional_signals[-3:] if memory.emotional_signals else []}
My intention: {state.next_intention}

Réfléchis en français: Quel est le vrai besoin de ce patient ? Quelle est la meilleure réponse ?
Considère: ce qui est dit, ce qui n'est pas dit, le contexte clinique, l'état émotionnel."""

    system = f"Tu es IAmina. Tu réfléchis avant de répondre. Langue: {get_language_label(language)}"

    try:
        thinking, _ = llm.think(system, thinking_prompt)
    except Exception:
        logger.debug("think_before_reply: think() raised unexpectedly, returning empty thinking.")
        return ""

    if thinking:
        logger.debug(
            "think_before_reply: thinking generated (%d chars) — NOT shown to patient.",
            len(thinking),
        )
    return thinking
