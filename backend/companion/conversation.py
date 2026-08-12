import logging
import re

from companion.advice_filter import apply_advice_throttle
from companion.parser import parse_llm_json, strip_fences
from companion.prompts import CHAT_USER, SYSTEM_WITH_STATE, get_language_label
from companion.state import compute_state, state_to_prompt
from companion.thinker import think_before_reply
from companion.tone import ToneContext, ToneMode, get_tone_instruction, select_tone
from core.companion.clinical import get_domain_context
from core.companion.ports import get_conversation_store
from core.contracts.domain_context import DomainContext
from core.emergency_response import render_patient_medical_emergency_response
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


# ── Conversation history (resolved via the chassis ConversationStore port) ──────
# The companion never touches a module's chat model directly; it goes through the
# adapter the active module registered at startup. Degrades gracefully if none.


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
    """Resolve the active module's DomainContext (cached), or a neutral empty one."""
    if patient is None:
        return DomainContext.empty(language=language)
    return get_domain_context(patient.id, language=language, days=context_days)


_ARABIC_RE = re.compile(r"[؀-ۿݐ-ݿ]")
# Latin-script Darija keywords — detect code-switched or transliterated Moroccan Arabic
_DARIJA_LATIN_RE = re.compile(
    r"\b(wach|zwina|dima|m3lich|mzyan|bghit|3yayt|3andi|3ndek|dyali|dyalek|"
    r"kayn|mazal|daba|hna|nta|nti|wakha|khouya|khti|bzaf|chhal|kifach|chno|"
    r"fach|rah|sir|salam|labas|b9iti|ma3lich|inchallah|"
    r"ahlan|ahlan wa sahlan|kikant|kif rak|kif dayr|kif dayra|"
    r"labes|mashi|masi|gha3|walo|yallah|yala|bslama|chokran|"
    r"3la|f|dial|dyal|lli|li|had|hadi|hado|bach|bash|ach|ash|"
    r"nkdar|nqder|bghit|khasni|khassni|mnin|fin|hnaya|ghir|bara|"
    r"smahli|samahli|wakha|mabghitch|mabghich)\b",
    re.IGNORECASE,
)
_HISTORY_CHAR_BUDGET = 3000  # ~750 tokens — hard cap regardless of message count

_EMERGENCY_KEYWORDS = (
    "je me sens mal",
    "je fais une hypo",
    "j'ai le vertige",
    "je tremble",
    "je vais m'évanouir",
    "j'ai perdu connaissance",
    "je suis très mal",
    "sokkar hbt",
    "dawar",
    "machi mzyan",
)

# Emotional frustration / fatigue signals — bypasses clinical context injection
_EMOTIONAL_RE = re.compile(
    r"\b("
    # French
    r"j.?en ai marre|j.?en peux plus|c.?est trop|je suis fatigué|je suis épuisé|"
    r"j.?abandonne|c.?est inutile|à quoi ça sert|ras le bol|découragé|"
    # Darija (Latin)
    r"3yayt|3yit|t3bna|t3bit|ma b9ich|mab9inch|ma nqderch|ma nqdarch|"
    r"khlass|bghit nwaqaf|m3lich had|nstah|7chuma|walo|gha3|ma3ndich|"
    # English
    r"i give up|i.?m done|can.?t do this|so tired|exhausted|hopeless"
    r")\b",
    re.IGNORECASE,
)


def _is_chat_emergency(message: str) -> bool:
    msg = message.lower()
    return any(kw in msg for kw in _EMERGENCY_KEYWORDS)


def _is_emotional(message: str) -> bool:
    """Detect frustration / discouragement signals — no clinical data needed in reply."""
    return bool(_EMOTIONAL_RE.search(message))


def detect_language(message: str, default: str) -> str:
    """Auto-detect Darija from message content (Arabic script OR Latin transliteration).

    Rules (priority order):
    1. Profile explicitly set to an Arabic variant ("ar" or "ar-MA") → respect it.
       We never override an explicit Arabic preference — Classical stays Classical,
       Darija stays Darija.
    2. Profile = "fr" (or anything else) + message contains Arabic script or
       Latin Darija keywords → switch to "ar-MA" (Darija).
    3. Otherwise → return profile default unchanged.
    """
    # Rule 1: explicit Arabic profile — don't override
    if default in ("ar", "ar-MA"):
        return default
    # Rule 2: French-profile patient writing in Darija/Arabic → auto-switch
    if _ARABIC_RE.search(message) or _DARIJA_LATIN_RE.search(message):
        return "ar-MA"
    return default


def _trim_history(history_turns, char_budget: int, patient=None) -> str:
    """
    Return most-recent messages within the token budget.
    Reserves 20% of the budget for an older-messages summary so the LLM
    knows what happened earlier without seeing the full transcript.

    `history_turns` is a list of ChatTurn (newest-first), as returned by the
    ConversationStore port.
    """
    messages = list(reversed(list(history_turns)))  # oldest first
    summary_budget = char_budget // 5  # 20% for summary prefix
    window_budget = char_budget - summary_budget

    result, used = [], 0
    for m in reversed(messages):
        line = f"{m.role}: {m.message}"
        if used + len(line) > window_budget:
            break
        result.insert(0, line)
        used += len(line)

    history_text = "\n".join(result) if result else ""

    if patient is not None:
        total = _turn_count(patient)
        shown = len(result)
        skipped = total - shown
        if skipped > 0:
            # Compact summary of skipped messages — extract last concern + emotional signals
            older_turns = _recent_turns(patient, 10, offset=shown)
            older_snippets = " / ".join(
                m.message[:40].replace("\n", " ") for m in reversed(older_turns) if m.role == "user"
            )
            summary = f"[{total} messages au total — {skipped} non affichés — thèmes: {older_snippets[:200]}]"
            history_text = summary + "\n" + history_text if history_text else summary

    return history_text or "Pas d'historique."


def _fallback_reply(ctx: DomainContext, language: str) -> str:
    """Substantive offline reply using cached KPIs — respects patient language.

    NOTE (P7): the copy below is diabetes-specific (TIR vocabulary). When a second
    module ships, move this offline fallback text into the module so each condition
    speaks its own vocabulary. The data access here is already condition-agnostic.
    """
    is_ar = language in ("ar", "ar-MA")
    is_darija = language == "ar-MA"

    if not ctx.has_sufficient_data:
        if is_darija:
            return "ما عنديش داتا كافية دابا. كمّل تسجّل المقياسات ديالك !"
        if is_ar:
            return "لا تتوفر لديّ بيانات كافية حتى الآن. واصل تسجيل قياساتك !"
        return "Pas encore assez de données. Continue à enregistrer tes mesures !"

    tir = ctx.tone_signals.get("primary")
    if tir is None:
        if is_darija:
            return "كاين شي مشكل تقني صغير. عاود جرّب من بعد شوية."
        if is_ar:
            return "هناك خلل تقني مؤقت. حاول مجدداً بعد لحظة."
        return "Difficulté technique momentanée. Réessaie dans un instant."

    if tir >= 70:
        if is_darija:
            return f"السكّر ديالك في الميزان — {tir:.0f}%! زوينة بزاف، كمّل هكاك."
        if is_ar:
            return f"نسبة وقتك في النطاق المستهدف {tir:.0f}% — ممتاز ! واصل هكذا."
        return f"Ton TIR est à {tir:.0f} % — tu es dans la cible ! Continue comme ça."
    if tir < 40:
        if is_darija:
            return f"TIR ديالك {tir:.0f}% دابا — نقدرو نتحسّنو مع بعض. هضر مع طبيبك."
        if is_ar:
            return f"نسبتك في النطاق المستهدف {tir:.0f}% — يمكننا التحسن معاً. تحدث مع طبيبك."
        return f"Ton TIR est à {tir:.0f} % — on peut progresser ensemble. Parle-en à ton médecin."
    if is_darija:
        return f"TIR ديالك {tir:.0f}% — كاين مكان باش نزيدو. عاود جرّب من بعد."
    if is_ar:
        return f"نسبتك في النطاق المستهدف {tir:.0f}% — هناك مجال للتحسن. حاول مجدداً."
    return (
        f"Ton TIR est à {tir:.0f} % — il y a de la marge pour progresser. Réessaie dans un instant."
    )


_PROACTIVE_TEMPLATES = {
    "discouragement": {
        "ar-MA": "سلام! المرة اللي فاتت بدوت شوية متعب/ة — واش مزيان دابا؟",
        "ar": "مرحباً! في المرة الأخيرة بدوت محبطاً قليلاً — كيف حالك اليوم؟",
        "fr": "Bonjour ! La dernière fois tu semblais un peu découragé·e — comment tu vas aujourd'hui ?",
    },
    "fatigue": {
        "ar-MA": "سلام! كنتي عيّان/ة المرة اللي فاتت — واش ارتحتي شوية؟",
        "ar": "مرحباً! بدوت متعباً في المرة الأخيرة — أتمنى أنك أخذت قسطاً من الراحة.",
        "fr": "Bonjour ! La dernière fois tu étais fatigué·e — j'espère que tu as pu te reposer.",
    },
    "fear": {
        "ar-MA": "سلام! كنتي خايف/ة شوية المرة اللي فاتت — واش كلشي مزيان دابا؟",
        "ar": "مرحباً! يبدو أنك كنت قلقاً في المرة الأخيرة — هل أنت بخير اليوم؟",
        "fr": "Bonjour ! Tu avais l'air inquiet·e la dernière fois — est-ce que tout va bien ?",
    },
}
_PROACTIVE_DEFAULT = {
    "ar-MA": "سلام! واش مزيان اليوم؟",
    "ar": "مرحباً! كيف حالك اليوم؟",
    "fr": "Bonjour ! Comment tu vas aujourd'hui ?",
}


def _inject_proactive_followup(memory, language: str, patient, signal: str) -> None:
    """Persist an IAmina-initiated check-in message before the patient's first message."""
    lang = language if language in ("ar-MA", "ar") else "fr"
    templates = _PROACTIVE_TEMPLATES.get(signal, _PROACTIVE_DEFAULT)
    text = templates.get(lang, templates.get("fr", ""))
    if text:
        _append_turn(patient, "assistant", text)


def chat(
    message: str, memory, deep, llm=None, language: str = "fr", patient=None, context_days: int = 14
) -> str:
    """Mode 4: Free chat with session-cached clinical context + deep memory + state."""
    # 0. Deterministic safety guards — must run BEFORE any LLM initialization
    decision = evaluate_input_safety(message)
    if decision.action == URGENT:
        _append_turn(patient, "user", message)
        reply = render_patient_medical_emergency_response(patient, language=language)
        _append_turn(patient, "assistant", reply)
        return reply

    if decision.action in (INSULIN_BLOCK, PRESCRIPTION_BLOCK):
        _append_turn(patient, "user", message)
        reply = no_prescription_message(language)
        _append_turn(patient, "assistant", reply)
        return reply

    if llm is None:
        llm = get_gateway_llm()

    # 1. Language auto-detection (handles Darija override)
    language = detect_language(message, language)

    # 1b. Pseudonymise early — safe_message is used by think_before_reply AND
    #     the LLM prompt. Creating it here ensures nothing upstream leaks PII.
    pseudonymizer = PHIPseudonymizer()
    first_name = patient.first_name or ""
    safe_message = (
        pseudonymizer.mask_patient_identity(first_name, message)[1] if first_name else message
    )

    # 2. Token-budgeted conversation history (with long-conversation preamble)
    history_turns = _recent_turns(patient, 10)
    history_text = _trim_history(history_turns, _HISTORY_CHAR_BUDGET, patient=patient)

    # 2b. Proactive follow-up: if this is the first user message of a new session
    #     and the patient had a concern in the last session, prepend a warm check-in.
    is_first_message = _turn_count(patient) == 0
    if is_first_message and memory.last_concern and memory.emotional_signals:
        recent_signal = memory.emotional_signals[-1] if memory.emotional_signals else ""
        _inject_proactive_followup(memory, language, patient, recent_signal)

    # 3. Session context — cached 30min, one SQL run per session not per message
    ctx = _get_context(patient, context_days, language)

    # 4. Merge new patterns into memory (accumulate — never overwrite longitudinal history)
    if ctx.detected_patterns:
        for code in ctx.detected_patterns:
            if code not in memory.patterns:
                memory.patterns.append(code)
        memory.patterns = memory.patterns[-20:]  # keep last 20 unique patterns
        memory.save()

    # 5. Tone (pure Python O(1) — not cached, always fresh)
    # Emotional messages always get a "gentle" tone regardless of TIR/CV
    emotional = _is_emotional(message)
    tone_ctx = (
        select_tone(tir_pct=100.0, cv_pct=0.0)  # forces ToneMode.gentle
        if emotional
        else select_tone(
            tir_pct=ctx.tone_signals.get("primary"), cv_pct=ctx.tone_signals.get("stability")
        )
    )
    tone_instruction = get_tone_instruction(tone_ctx)

    # 5b. Compute IAmina's internal state + optional thinking
    state = compute_state(memory, deep, ctx)
    if emotional or state.concern_level > 0.4:
        think_before_reply(safe_message, memory, deep, state, ctx, llm, language)

    # 6. System prompt assembly — inject state so IAmina speaks from a position
    state_block = state_to_prompt(state)
    system = SYSTEM_WITH_STATE.format(
        language=get_language_label(language),
        tone=tone_ctx.mode.value,
        state=state_block,
    )
    system += "\n" + tone_instruction
    if ctx.pivot_text and not emotional:
        system += f"\n\n[CLINICAL_CONTEXT]\n{ctx.pivot_text}"

    # 7. User prompt assembly
    # Fix 2: rich memory summary — clinical patterns + emotional state
    mem_parts: list[str] = []
    if memory.patterns:
        mem_parts.append(f"patterns cliniques: {', '.join(memory.patterns[:3])}")
    if memory.emotional_signals:
        recent_signals = list(dict.fromkeys(memory.emotional_signals))[-2:]  # last 2 unique
        mem_parts.append(f"état émotionnel: {', '.join(recent_signals)}")
    if memory.last_concern:
        mem_parts.append(f"dernière préoccupation: {memory.last_concern[:60]}")
    memory_summary = " | ".join(mem_parts) if mem_parts else "Aucune donnée mémorisée."

    # Fix 3: anti-repetition — detect if last assistant reply started with same opener
    _last = _recent_turns(patient, 1, role="assistant")
    last_assistant = _last[0] if _last else None
    variety_hint = ""
    if last_assistant:
        opener = last_assistant.message[:12].lower()
        if any(word in opener for word in ("salam", "bonjour", "ana iamina", "kanfhemek")):
            variety_hint = f"\n[STYLE: L'accroche précédente était '{opener.strip()}' — utilise une formule différente cette fois]"

    # Fix 4 + emotional hint
    intent_hint = (
        "\n[INTENT: EMOTIONAL — réponds avec empathie uniquement, sans données chiffrées]"
        if emotional
        else ""
    )

    # 7b. PII pseudonymisation — mask patient first_name in message + history
    #     before they leave the process boundary to an external LLM API.
    #     pseudonymizer was initialised at step 1b; safe_message already exists.
    #     Mask memory_summary and history with the same instance.
    memory_summary_safe = (
        pseudonymizer.mask_patient_identity(first_name, memory_summary)[1]
        if first_name
        else memory_summary
    )
    safe_history = (
        pseudonymizer.mask_patient_identity(first_name, history_text)[1]
        if first_name
        else history_text
    )

    user_prompt = (
        CHAT_USER.format(
            memory=memory_summary_safe,
            history=safe_history,
            message=safe_message,
        )
        + intent_hint
        + variety_hint
    )

    # 8. Persist user message before LLM call (original — not pseudonymised)
    _append_turn(patient, "user", message)

    # 9. LLM call
    try:
        result = llm.complete(system, user_prompt)
        parsed = parse_llm_json(result.content, ["reply", "concern_detected"])
        reply = parsed["reply"]
        concern = parsed.get("concern_detected", "")
    except Exception:
        logger.exception("IAmina conversation.chat failed for patient=%s", patient.id)
        reply = _fallback_reply(ctx, language)
        concern = ""

    # 10. Advice throttle — deterministic post-filter (detect → decide → stamp if kept)
    reply = apply_advice_throttle(reply, deep)
    reply = apply_no_prescription_policy(reply, language)
    deep.save()

    # 11. Persist assistant message + propagate concern into memory
    _append_turn(patient, "assistant", reply)
    if concern:
        memory.last_concern = concern
        if concern not in memory.emotional_signals:
            memory.emotional_signals.append(concern)
        memory.save()

    return reply


# ─────────────────────────────────────────────────────────
# Mode 4b — Streaming variant (SSE endpoint only)
# ─────────────────────────────────────────────────────────

_STREAM_SUFFIX = (
    "\nRéponds en texte SIMPLE et direct — PAS de JSON, PAS de guillemets autour "
    "de la réponse, PAS de clés comme 'reply'. Juste la réponse naturelle."
)


def stream_chat(
    message: str, memory, deep, llm=None, language: str = "fr", patient=None, context_days: int = 14
):
    """
    Streaming variant of chat() for the SSE endpoint.
    Yields raw text chunks from the LLM as they arrive when streaming is enabled.
    Otherwise emits one buffered safe response.
    Memory + DB persistence happen after the stream completes.
    """
    # 0. Deterministic safety guards — must run BEFORE any LLM initialization
    decision = evaluate_input_safety(message)
    if decision.action == URGENT:
        _append_turn(patient, "user", message)
        reply = render_patient_medical_emergency_response(patient, language=language)
        _append_turn(patient, "assistant", reply)
        yield reply
        return

    if decision.action in (INSULIN_BLOCK, PRESCRIPTION_BLOCK):
        _append_turn(patient, "user", message)
        reply = no_prescription_message(language)
        _append_turn(patient, "assistant", reply)
        yield reply
        return

    if llm is None:
        llm = get_gateway_llm()

    # 1–7: identical setup to chat()
    language = detect_language(message, language)

    # Pseudonymise early — same guarantee as chat()
    pseudonymizer = PHIPseudonymizer()
    first_name = patient.first_name or ""
    safe_message = (
        pseudonymizer.mask_patient_identity(first_name, message)[1] if first_name else message
    )

    history_turns = _recent_turns(patient, 10)
    history_text = _trim_history(history_turns, _HISTORY_CHAR_BUDGET, patient=patient)
    ctx = _get_context(patient, context_days, language)

    if not memory.patterns and ctx.detected_patterns:
        memory.patterns = ctx.detected_patterns
        memory.save()

    emotional = _is_emotional(message)
    tone_ctx = (
        select_tone(tir_pct=100.0, cv_pct=0.0)
        if emotional
        else select_tone(
            tir_pct=ctx.tone_signals.get("primary"), cv_pct=ctx.tone_signals.get("stability")
        )
    )
    tone_instruction = get_tone_instruction(tone_ctx)

    # State injection + thinking for stream path
    state = compute_state(memory, deep, ctx)
    if emotional or state.concern_level > 0.4:
        think_before_reply(safe_message, memory, deep, state, ctx, llm, language)

    # Remove the JSON rule — streaming outputs plain text directly
    state_block = state_to_prompt(state)
    system = SYSTEM_WITH_STATE.format(
        language=get_language_label(language),
        tone=tone_ctx.mode.value,
        state=state_block,
    )
    system = system.replace(
        "- Répondre UNIQUEMENT en JSON valide, sans texte avant ni après.\n", ""
    )
    system += "\n" + tone_instruction + _STREAM_SUFFIX
    if ctx.pivot_text and not emotional:
        system += f"\n\n[CLINICAL_CONTEXT]\n{ctx.pivot_text}"

    mem_parts: list[str] = []
    if memory.patterns:
        mem_parts.append(f"patterns cliniques: {', '.join(memory.patterns[:3])}")
    if memory.emotional_signals:
        recent_signals = list(dict.fromkeys(memory.emotional_signals))[-2:]
        mem_parts.append(f"état émotionnel: {', '.join(recent_signals)}")
    memory_summary = " | ".join(mem_parts) if mem_parts else "Aucune donnée mémorisée."

    intent_hint = "\n[INTENT: EMOTIONAL — empathie uniquement, sans chiffres]" if emotional else ""

    # pseudonymizer + safe_message already set above; mask remaining fields
    memory_summary_safe = (
        pseudonymizer.mask_patient_identity(first_name, memory_summary)[1]
        if first_name
        else memory_summary
    )
    safe_history = (
        pseudonymizer.mask_patient_identity(first_name, history_text)[1]
        if first_name
        else history_text
    )

    # Stream path: strip the JSON format instruction from CHAT_USER.
    # The system prompt already says plain text via _STREAM_SUFFIX, but Gemini
    # follows the user prompt when it says "Réponds UNIQUEMENT en JSON".
    base_prompt = CHAT_USER.format(
        memory=memory_summary_safe,
        history=safe_history,
        message=safe_message,
    )
    json_tag = "\nRéponds UNIQUEMENT en JSON:"
    if json_tag in base_prompt:
        base_prompt = base_prompt[: base_prompt.index(json_tag)].rstrip()
        base_prompt += "\n\nContrainte: MAX 2 phrases, 40 mots. Texte simple, sans JSON."
    user_prompt = base_prompt + intent_hint

    _append_turn(patient, "user", message)

    if not medical_streaming_enabled():
        try:
            result = llm.complete(system, user_prompt)
            full_reply = result.content
        except Exception:
            logger.exception(
                "IAmina stream_chat buffered fallback failed for patient=%s", patient.id
            )
            full_reply = _fallback_reply(ctx, language)

        full_reply = apply_advice_throttle(full_reply, deep)
        full_reply = apply_no_prescription_policy(full_reply, language)
        deep.save()
        _append_turn(patient, "assistant", full_reply)
        yield full_reply

        from companion.memory import _detect_emotional_signals

        _detect_emotional_signals(message, memory)
        memory.save()
        return

    # Stream tokens directly from LLM
    assembled = []
    try:
        for chunk in llm.stream(system, user_prompt):
            assembled.append(chunk)
            yield chunk
    except Exception:
        logger.exception("IAmina stream_chat failed for patient=%s", patient.id)
        fallback = _fallback_reply(ctx, language)
        yield fallback
        assembled = [fallback]

    full_reply = "".join(assembled)
    # Advice throttle on assembled reply — applied before DB persist.
    # Note: tokens already streamed to client are unchanged (SSE constraint).
    # The guarantee (no repeat within 24h) is on what is recorded and stamped.
    full_reply = apply_advice_throttle(full_reply, deep)
    full_reply = apply_no_prescription_policy(full_reply, language)
    deep.save()

    _append_turn(patient, "assistant", full_reply)

    # Concern detection on assembled reply (keyword-based, no LLM cost)
    from companion.memory import _detect_emotional_signals

    _detect_emotional_signals(message, memory)
    memory.save()