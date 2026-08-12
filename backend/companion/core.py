import logging

from companion.conversation import chat, stream_chat
from companion.deep_memory import IAminaDeepMemory
from companion.memory import IAminaMemory
from companion.narrator import summarize
from companion.reactor import react
from core.companion.clinical import evaluate_alert as _evaluate_alert
from core.companion.ports import get_conversation_store
from core.emergency_response import compose_emergency_for_patient
from core.input_safety import URGENT, evaluate_input_safety

logger = logging.getLogger(__name__)


class IAmina:
    """
    Thin orchestrator — no business logic here.
    Loads all memory layers on init, delegates to sub-modules.
    """

    def __init__(self, patient, language: str = "ar-MA"):
        self.patient = patient
        self.language = language
        self.memory = IAminaMemory.load(patient)
        self.deep = IAminaDeepMemory.load(patient)

    def _canonical_emergency_reply(self, message: str) -> str | None:
        """Return the shared deterministic urgent response, or None when non-urgent."""
        decision = evaluate_input_safety(message)
        if decision.action != URGENT:
            return None

        response = compose_emergency_for_patient(
            decision,
            patient=self.patient,
            language=self.language,
            message=message,
        )
        store = get_conversation_store()
        if store is not None:
            store.append(self.patient.id, "user", message)
            store.append(self.patient.id, "assistant", response.reply)
        return response.reply

    # ── on_log ────────────────────────────────────────────────────────────────

    def on_log(self, entry) -> str:
        # Offline safety gate — the active module's engine evaluates its own thresholds.
        alert = _evaluate_alert(entry, self.patient.id, self.language)

        # Layer 1: hard medical gate — offline, < 50ms, no LLM
        if alert is not None and alert.blocking:
            self.deep.record_event(
                alert.event_type,
                alert.event_description,
                glucose=alert.value,
            )
            self.deep.save()
            return alert.message

        # P0.4 truth boundary: legacy food-response heuristics are no longer
        # learned by the active runtime. Historical values remain readable only
        # for backward-compatible snapshot decoding; they are not patient facts.

        # Streak + relationship
        self.deep.update_streak(today_has_log=True)
        self.deep.total_interactions += 1
        self.deep.evolve_relationship(self.memory.emotional_signals)
        self.deep.save()

        # Pass deep=None for any clinical alert (WARNING included) so the
        # advice throttle never suppresses a clinically-triggered disclaimer.
        is_clinical_alert = alert is not None
        response = react(
            entry,
            self.memory,
            language=self.language,
            deep=None if is_clinical_alert else self.deep,
            patient=self.patient,
        )
        self.memory.update(entry)
        return response

    # ── summarize ─────────────────────────────────────────────────────────────

    def summarize(self, days: int = 7) -> str:
        return summarize(self.patient, self.memory, language=self.language, days=days)

    # ── chat ──────────────────────────────────────────────────────────────────

    def chat(self, message: str, context_days: int = 14) -> str:
        self.deep.total_interactions += 1
        self.deep.evolve_relationship(self.memory.emotional_signals)
        self.deep.save()

        emergency_reply = self._canonical_emergency_reply(message)
        if emergency_reply is not None:
            self.memory.update_from_chat(message, emergency_reply)
            return emergency_reply

        response = chat(
            message,
            self.memory,
            self.deep,
            language=self.language,
            patient=self.patient,
            context_days=context_days,
        )
        self.memory.update_from_chat(message, response)
        return response

    # ── stream_chat ───────────────────────────────────────────────────────────

    def stream_chat(self, message: str, context_days: int = 14):
        """Yields text chunks as they arrive from the LLM (SSE use only)."""
        self.deep.total_interactions += 1
        self.deep.evolve_relationship(self.memory.emotional_signals)
        self.deep.save()

        emergency_reply = self._canonical_emergency_reply(message)
        if emergency_reply is not None:
            yield emergency_reply
            return

        yield from stream_chat(
            message,
            self.memory,
            self.deep,
            language=self.language,
            patient=self.patient,
            context_days=context_days,
        )


# ── legacy compatibility helper ───────────────────────────────────────────────

def _learn_from_entry(deep: IAminaDeepMemory, entry, glucose: float) -> None:
    """Legacy food-response heuristic retained only for compatibility tests.

    The active IAmina orchestrator no longer calls this helper. P0.4 quarantines
    its output from patient-facing reasoning because the historical heuristic
    lacks the provenance/evidence needed to support a durable meal observation.
    """
    meal_desc = (getattr(entry, "meal_description", "") or "").strip()
    meal_items = getattr(entry, "meal_items", None) or []
    meal_type = getattr(entry, "meal_type", "") or ""

    if meal_type == "fasting" or glucose <= 180:
        return

    foods: list[str] = []
    if isinstance(meal_items, list):
        foods = [str(item) for item in meal_items if item]
    if not foods and meal_desc:
        foods = [meal_desc[:40]]

    if not foods:
        return

    delta = glucose - 130
    for food in foods[:3]:
        deep.learn_food_sensitivity(food, delta)
