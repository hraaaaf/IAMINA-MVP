import logging
import re

from companion.advice_filter import apply_advice_throttle
from companion.parser import parse_llm_json
from companion.prompts import CHAT_USER, SYSTEM_WITH_STATE, get_language_label
from companion.state import compute_state, state_to_prompt
from companion.thinker import think_before_reply
from companion.tone import get_tone_instruction, select_relationship_tone
from core.companion.clinical import (
    get_companion_context,
    get_domain_context,
    get_offline_fallback,
)
from core.companion.ports import get_conversation_store
from core.contracts.companion_context import CompanionContext
from core.contracts.domain_context import DomainContext
from core.emergency_response import compose_emergency_for_patient
from core.input_safety import (
    INSULIN_BLOCK,
    PRESCRIPTION_BLOCK,
    URGENT,
    evaluate_input_safety,
)
from core.llm_gateway import get_gateway_llm
from core.medical_safety import (
    apply_no_prescription_policy,
    medical_streaming_enabled,
    no_prescription_message,
)
from llm.pseudonymizer import PHIPseudonymizer

logger = logging.getLogger(__name__)

_HISTORY_CHAR_BUDGET = 3000
_STREAM_SUFFIX = (
    "\nRéponds en texte SIMPLE et direct — PAS de JSON, PAS de guillemets autour "
    "de la réponse, PAS de clés comme 'reply'. Juste la réponse naturelle."
)

_ARABIC_RE = re.compile(r"[؀-ۿݐ-ݿ]")
_DARIJA_LATIN_RE = re.compile(
    r"\b(wach|zwina|dima|m3lich|mzyan|bghit|3yayt|3andi|3ndek|dyali|dyalek|"
    r"kayn|mazal|daba|hna|nta|nti|wakha|khouya|khti|bzaf|chhal|kifach|chno|"
    r"fach|rah|sir|salam|labas|b9iti|ma3lich|inchallah|labes|mashi|walo|"
    r"yallah|bslama|chokran|3la|dyal|lli|had|hadi|bach|ach|nkdar|nqder|"
    r"khasni|khassni|mnin|fin|hnaya|ghir|smahli|samahli|mabghitch)\b",
    re.IGNORECASE,
)
_EMOTIONAL_RE = re.compile(
    r"\b("
    r"j.?en ai marre|j.?en peux plus|c.?est trop|je suis fatigué|je suis épuisé|"
    r"j.?abandonne|c.?est inutile|à quoi ça sert|ras le bol|découragé|"
    r"3yayt|3yit|t3bna|t3bit|ma b9ich|mab9inch|ma nqderch|ma nqdarch|"
    r"khlass|bghit nwaqaf|7chuma|ma3ndich|i give up|i.?m done|can.?t do this|"
    r"so tired|exhausted|hopeless"
    r")\b",
    re.IGNORECASE,
)


def _append_turn(patient, role: str, message: str) -> None:
    store = get_conversation_store()
    if store is not None and patient is not None:
        store.append(patient.id, role, message)


def _recent_turns(patient, limit: int, offset: int = 0, role: str | None = None):
    store = get_conversation_store()
    if store is None or patient is None:
        return []
    return store.recent(patient.id, limit, offset=offset, role=role)


def _turn_count(patient) -> int:
    store = get_conversation_store()
    if store is None or patient is None:
        return 0
    return store.count(patient.id)


def _get_context(patient, context_days: int, language: str = "fr") -> DomainContext:
    if patient is None:
        return DomainContext.empty(language=language)
    return get_domain_context(patient.id, language=language, days=context_days)


def _get_companion_context(patient, language: str = "fr") -> CompanionContext:
    if patient is None:
        return CompanionContext.empty(language=language)
    return get_companion_context(patient.id, language=language)


def _is_emotional(message: str) -> bool:
    return bool(_EMOTIONAL_RE.search(message))


def detect_language(message: str, default: str) -> str:
    if default in ("ar", "ar-MA"):
        return default
    if _ARABIC_RE.search(message) or _DARIJA_LATIN_RE.search(message):
        return "ar-MA"
    return default


def _trim_history(history_turns, char_budget: int, patient=None) -> str:
    messages = list(reversed(list(history_turns)))
    summary_budget = char_budget // 5
    window_budget = char_budget - summary_budget
    result: list[str] = []
    used = 0
    for item in reversed(messages):
        line = f"{item.role}: {item.message}"
        if used + len(line) > window_budget:
            break
        result.insert(0, line)
        used += len(line)

    history_text = "\n".join(result) if result else ""
    if patient is not None:
        total = _turn_count(patient)
        skipped = total - len(result)
        if skipped > 0:
            older_turns = _recent_turns(patient, 10, offset=len(result))
            snippets = " / ".join(
                turn.message[:40].replace("\n", " ")
                for turn in reversed(older_turns)
                if turn.role == "user"
            )
            summary = f"[{total} messages au total — {skipped} non affichés — thèmes: {snippets[:200]}]"
            history_text = summary + "\n" + history_text if history_text else summary
    return history_text or "Pas d'historique."


def _companion_context_block(context: CompanionContext) -> str:
    """Serialize only approved longitudinal state, with provenance and limits."""
    lines = [
        "[GOVERNED_COMPANION_CONTEXT]",
        f"pattern_status={context.pattern_status}",
        f"review_status={context.review_status}",
        f"source_version={context.source_version}",
    ]
    if context.review_anchor_captured_at:
        lines.append(f"review_anchor={context.review_anchor_captured_at}")

    for item in context.patterns[:3]:
        limitations = ",".join(item.limitations) if item.limitations else "none"
        lines.append(
            "pattern="
            f"{item.observation_key};state={item.current_state};"
            f"evidence_density={item.evidence_density};"
            f"source_version={item.source_version};limitations={limitations}"
        )

    for item in context.changes_since_review[:3]:
        missing = ",".join(item.missing_data) if item.missing_data else "none"
        lines.append(
            "change="
            f"{item.observation_key};kind={item.change_kind};"
            f"evidence_strength={item.evidence_strength};"
            f"source_version={item.source_version};missing_data={missing}"
        )

    lines.append(
        "after_visit="
        f"{context.after_visit.status};fact_count={context.after_visit.fact_count}"
    )
    lines.append(f"safety_notice={context.safety_notice}")
    lines.append(
        "NARRATION_RULE=Describe only the approved state above. Do not infer "
        "diagnosis, causality, priority, treatment, dose or proactive eligibility."
    )
    return "\n".join(lines)


def _relationship_memory_summary(memory) -> str:
    parts: list[str] = []
    if memory.emotional_signals:
        recent = list(dict.fromkeys(memory.emotional_signals))[-2:]
        parts.append(f"état émotionnel: {', '.join(recent)}")
    if memory.last_concern:
        parts.append(f"dernière préoccupation: {memory.last_concern[:60]}")
    return " | ".join(parts) if parts else "Aucune donnée relationnelle mémorisée."


def _safe_text(pseudonymizer: PHIPseudonymizer, first_name: str, text: str) -> str:
    if not first_name:
        return text
    return pseudonymizer.mask_patient_identity(first_name, text)[1]


def _build_runtime_prompt(
    *,
    message: str,
    memory,
    deep,
    llm,
    language: str,
    patient,
    context_days: int,
    streaming: bool,
):
    language = detect_language(message, language)
    pseudonymizer = PHIPseudonymizer()
    first_name = patient.first_name or "" if patient is not None else ""
    safe_message = _safe_text(pseudonymizer, first_name, message)

    history = _trim_history(
        _recent_turns(patient, 10),
        _HISTORY_CHAR_BUDGET,
        patient=patient,
    )
    ctx = _get_context(patient, context_days, language)
    companion_ctx = _get_companion_context(patient, language)
    emotional = _is_emotional(message)

    tone_ctx = select_relationship_tone(
        emotional=emotional,
        streak_days=deep.consecutive_log_days,
    )
    state = compute_state(memory, deep, ctx)
    if emotional or state.concern_level > 0.4:
        think_before_reply(safe_message, memory, deep, state, ctx, llm, language)

    system = SYSTEM_WITH_STATE.format(
        language=get_language_label(language),
        tone=tone_ctx.mode.value,
        state=state_to_prompt(state),
    )
    if streaming:
        system = system.replace(
            "- Répondre UNIQUEMENT en JSON valide, sans texte avant ni après.\n",
            "",
        )
        system += _STREAM_SUFFIX
    system += "\n" + get_tone_instruction(tone_ctx)

    if not emotional:
        if ctx.pivot_text:
            system += f"\n\n[APPROVED_SESSION_CONTEXT]\n{ctx.pivot_text}"
        system += "\n\n" + _companion_context_block(companion_ctx)

    memory_summary = _safe_text(
        pseudonymizer,
        first_name,
        _relationship_memory_summary(memory),
    )
    safe_history = _safe_text(pseudonymizer, first_name, history)

    base_prompt = CHAT_USER.format(
        memory=memory_summary,
        history=safe_history,
        message=safe_message,
    )
    if streaming:
        json_tag = "\nRéponds UNIQUEMENT en JSON:"
        if json_tag in base_prompt:
            base_prompt = base_prompt[: base_prompt.index(json_tag)].rstrip()
            base_prompt += "\n\nContrainte: MAX 2 phrases, 40 mots. Texte simple, sans JSON."

    intent_hint = (
        "\n[INTENT: EMOTIONAL — empathie uniquement, sans données chiffrées]"
        if emotional
        else ""
    )

    variety_hint = ""
    previous = _recent_turns(patient, 1, role="assistant")
    if previous:
        opener = previous[0].message[:12].lower()
        if any(word in opener for word in ("salam", "bonjour", "ana iamina", "kanfhemek")):
            variety_hint = (
                f"\n[STYLE: L'accroche précédente était '{opener.strip()}' — "
                "utilise une formule différente cette fois]"
            )

    return language, ctx, system, base_prompt + intent_hint + variety_hint


def _safety_reply(message: str, patient, language: str) -> str | None:
    decision = evaluate_input_safety(message)
    if decision.action == URGENT:
        return compose_emergency_for_patient(
            decision,
            patient=patient,
            language=language,
            message=message,
        ).reply
    if decision.action in (INSULIN_BLOCK, PRESCRIPTION_BLOCK):
        return no_prescription_message(language)
    return None


def _finalize_reply(reply: str, deep, language: str) -> str:
    reply = apply_advice_throttle(reply, deep)
    reply = apply_no_prescription_policy(reply, language)
    deep.save()
    return reply


def chat(
    message: str,
    memory,
    deep,
    llm=None,
    language: str = "fr",
    patient=None,
    context_days: int = 14,
) -> str:
    """Narrator-only conversational path over deterministic governed context."""
    safety_reply = _safety_reply(message, patient, language)
    if safety_reply is not None:
        _append_turn(patient, "user", message)
        _append_turn(patient, "assistant", safety_reply)
        return safety_reply

    if llm is None:
        llm = get_gateway_llm()

    language, ctx, system, user_prompt = _build_runtime_prompt(
        message=message,
        memory=memory,
        deep=deep,
        llm=llm,
        language=language,
        patient=patient,
        context_days=context_days,
        streaming=False,
    )
    _append_turn(patient, "user", message)

    concern = ""
    try:
        result = llm.complete(system, user_prompt)
        parsed = parse_llm_json(result.content, ["reply", "concern_detected"])
        reply = parsed["reply"]
        concern = parsed.get("concern_detected", "")
    except Exception:
        logger.exception(
            "IAmina conversation.chat failed for patient=%s",
            patient.id if patient else None,
        )
        reply = get_offline_fallback(
            patient.id if patient else None,
            ctx,
            language,
        )

    reply = _finalize_reply(reply, deep, language)
    _append_turn(patient, "assistant", reply)

    if concern:
        memory.last_concern = concern
        if concern not in memory.emotional_signals:
            memory.emotional_signals.append(concern)
        memory.save()
    return reply


def stream_chat(
    message: str,
    memory,
    deep,
    llm=None,
    language: str = "fr",
    patient=None,
    context_days: int = 14,
):
    """Narrator-only SSE path with the same deterministic authority boundaries."""
    safety_reply = _safety_reply(message, patient, language)
    if safety_reply is not None:
        _append_turn(patient, "user", message)
        _append_turn(patient, "assistant", safety_reply)
        yield safety_reply
        return

    if llm is None:
        llm = get_gateway_llm()

    language, ctx, system, user_prompt = _build_runtime_prompt(
        message=message,
        memory=memory,
        deep=deep,
        llm=llm,
        language=language,
        patient=patient,
        context_days=context_days,
        streaming=True,
    )
    _append_turn(patient, "user", message)

    if not medical_streaming_enabled():
        try:
            result = llm.complete(system, user_prompt)
            full_reply = result.content
        except Exception:
            logger.exception(
                "IAmina stream_chat buffered fallback failed for patient=%s",
                patient.id if patient else None,
            )
            full_reply = get_offline_fallback(
                patient.id if patient else None,
                ctx,
                language,
            )
        full_reply = _finalize_reply(full_reply, deep, language)
        _append_turn(patient, "assistant", full_reply)
        yield full_reply
    else:
        assembled: list[str] = []
        try:
            for chunk in llm.stream(system, user_prompt):
                assembled.append(chunk)
                yield chunk
        except Exception:
            logger.exception(
                "IAmina stream_chat failed for patient=%s",
                patient.id if patient else None,
            )
            fallback = get_offline_fallback(
                patient.id if patient else None,
                ctx,
                language,
            )
            yield fallback
            assembled = [fallback]

        full_reply = _finalize_reply("".join(assembled), deep, language)
        _append_turn(patient, "assistant", full_reply)

    from companion.memory import _detect_emotional_signals

    _detect_emotional_signals(message, memory)
    memory.save()
