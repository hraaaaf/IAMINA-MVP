import logging

from companion.conversation import chat, stream_chat
from companion.deep_memory import IAminaDeepMemory
from companion.memory import IAminaMemory
from companion.narrator import summarize
from companion.reactor import react
from core.companion.clinical import evaluate_alert as _evaluate_alert

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

        # Legacy single-entry meal sensitivity learning was retired by P0.4.
        # Personal metabolic response belongs to the evidence-bounded deterministic
        # Journal analysis, not durable companion heuristic memory.

        # Streak + relationship
        self.deep.update_streak(today_has_log=True)
        self.deep.total_interactions += 1
        self.deep.evolve_relationship(self.memory.emotional_signals)
        self.deep.save()

        # Pass deep=None for any clinical alert (WARNING included) so the
        # advice throttle never suppresses a clinically-triggered disclaimer.
        is_clinical_alert = alert is not None
        response = react(
            entry, self.memory, language=self.language,
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

        response = chat(
            message, self.memory, self.deep,
            language=self.language, patient=self.patient, context_days=context_days,
        )
        self.memory.update_from_chat(message, response)
        return response

    # ── stream_chat ───────────────────────────────────────────────────────────

    def stream_chat(self, message: str, context_days: int = 14):
        """Yields text chunks as they arrive from the LLM (SSE use only)."""
        self.deep.total_interactions += 1
        self.deep.evolve_relationship(self.memory.emotional_signals)
        self.deep.save()

        yield from stream_chat(
            message, self.memory, self.deep,
            language=self.language, patient=self.patient, context_days=context_days,
        )
