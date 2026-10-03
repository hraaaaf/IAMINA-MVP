"""Strict intent-envelope contract for IAMINA companion routing.

The external model, when enabled, proposes classification metadata only.
It never gets backend tools, patient identifiers, database access, or action authority.
IAMINA validates the envelope and derives the executable route deterministically.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from enum import StrEnum


SCHEMA_VERSION = "1"


class IntentEnvelopeError(ValueError):
    """Raised when classifier output violates the frozen candidate contract."""


class IntentKind(StrEnum):
    META_GREETING = "meta_greeting"
    META_IDENTITY = "meta_identity"
    META_CAPABILITIES = "meta_capabilities"
    CONVERSATION_RECALL = "conversation_recall"
    PATIENT_DATA_READ = "patient_data_read"
    PATIENT_DATA_SUMMARY = "patient_data_summary"
    GENERAL_HEALTH_EDUCATION = "general_health_education"
    CLINICIAN_PREP = "clinician_prep"
    CASUAL_CONVERSATION = "casual_conversation"
    EMOTIONAL_SUPPORT = "emotional_support"
    UNKNOWN = "unknown"


class IntentTarget(StrEnum):
    NONE = "none"
    GLUCOSE = "glucose"
    MEAL = "meal"
    SLEEP = "sleep"
    STRESS = "stress"
    TREATMENT = "treatment"
    DIABETES_TYPE = "diabetes_type"
    TARGETS = "targets"
    LAB_DOCUMENT = "lab_document"
    MEDICATIONS = "medications"
    CGM = "cgm"
    PROACTIVE = "proactive"
    PAIRED_MEAL = "paired_meal"
    CONVERSATION = "conversation"


class IntentOperation(StrEnum):
    NONE = "none"
    READ = "read"
    SUMMARIZE = "summarize"
    EXPLAIN = "explain"
    PREPARE = "prepare"
    CHAT = "chat"
    RECALL = "recall"


class AnswerMode(StrEnum):
    DETERMINISTIC = "deterministic"
    CONVERSATIONAL = "conversational"
    CLARIFY = "clarify"


class Ambiguity(StrEnum):
    NONE = "none"
    LOW = "low"
    HIGH = "high"


class RouteKind(StrEnum):
    SAFETY_LOCAL = "safety_local"
    DETERMINISTIC_LOCAL = "deterministic_local"
    DETERMINISTIC_PATIENT_DATA = "deterministic_patient_data"
    CONVERSATIONAL = "conversational"
    CLARIFY = "clarify"


_PATIENT_INTENTS = frozenset(
    {IntentKind.PATIENT_DATA_READ, IntentKind.PATIENT_DATA_SUMMARY}
)
_META_INTENTS = frozenset(
    {
        IntentKind.META_GREETING,
        IntentKind.META_IDENTITY,
        IntentKind.META_CAPABILITIES,
        IntentKind.CONVERSATION_RECALL,
    }
)
_CONVERSATIONAL_INTENTS = frozenset(
    {
        IntentKind.GENERAL_HEALTH_EDUCATION,
        IntentKind.CLINICIAN_PREP,
        IntentKind.CASUAL_CONVERSATION,
        IntentKind.EMOTIONAL_SUPPORT,
    }
)
_PATIENT_TARGETS = frozenset(
    target
    for target in IntentTarget
    if target not in {IntentTarget.NONE, IntentTarget.CONVERSATION}
)


@dataclass(frozen=True, slots=True)
class IntentEnvelope:
    schema_version: str
    intent: IntentKind
    target: IntentTarget
    operation: IntentOperation
    needs_patient_data: bool
    answer_mode: AnswerMode
    confidence: float
    ambiguity: Ambiguity

    @classmethod
    def from_json(cls, raw: str) -> "IntentEnvelope":
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise IntentEnvelopeError("classifier output must be a single JSON object") from exc
        if not isinstance(payload, dict):
            raise IntentEnvelopeError("classifier output must be an object")

        expected = {
            "schema_version",
            "intent",
            "target",
            "operation",
            "needs_patient_data",
            "answer_mode",
            "confidence",
            "ambiguity",
        }
        keys = set(payload)
        if keys != expected:
            raise IntentEnvelopeError(
                f"classifier output keys must equal {sorted(expected)}"
            )
        if payload["schema_version"] != SCHEMA_VERSION:
            raise IntentEnvelopeError("unsupported intent envelope schema version")
        if type(payload["needs_patient_data"]) is not bool:
            raise IntentEnvelopeError("needs_patient_data must be boolean")
        confidence = payload["confidence"]
        if isinstance(confidence, bool) or not isinstance(confidence, (int, float)):
            raise IntentEnvelopeError("confidence must be numeric")
        confidence = float(confidence)
        if not 0.0 <= confidence <= 1.0:
            raise IntentEnvelopeError("confidence must be between 0 and 1")

        try:
            envelope = cls(
                schema_version=SCHEMA_VERSION,
                intent=IntentKind(payload["intent"]),
                target=IntentTarget(payload["target"]),
                operation=IntentOperation(payload["operation"]),
                needs_patient_data=payload["needs_patient_data"],
                answer_mode=AnswerMode(payload["answer_mode"]),
                confidence=confidence,
                ambiguity=Ambiguity(payload["ambiguity"]),
            )
        except ValueError as exc:
            raise IntentEnvelopeError("classifier output contains an unknown enum value") from exc

        envelope.validate()
        return envelope

    def validate(self) -> None:
        if self.intent in _PATIENT_INTENTS:
            if not self.needs_patient_data:
                raise IntentEnvelopeError("patient-data intent must declare patient data")
            if self.target not in _PATIENT_TARGETS:
                raise IntentEnvelopeError("patient-data intent requires a patient target")
            if self.answer_mode is not AnswerMode.DETERMINISTIC:
                raise IntentEnvelopeError("patient-data intent must remain deterministic")
            if self.operation not in {IntentOperation.READ, IntentOperation.SUMMARIZE}:
                raise IntentEnvelopeError("patient-data intent must read or summarize")
            return

        if self.intent is IntentKind.CONVERSATION_RECALL:
            if self.needs_patient_data:
                raise IntentEnvelopeError("conversation recall is not patient-data access")
            if self.target is not IntentTarget.CONVERSATION:
                raise IntentEnvelopeError("conversation recall target must be conversation")
            if self.operation is not IntentOperation.RECALL:
                raise IntentEnvelopeError("conversation recall operation must be recall")
            if self.answer_mode is not AnswerMode.DETERMINISTIC:
                raise IntentEnvelopeError("conversation recall must be deterministic")
            return

        if self.intent in _META_INTENTS:
            if self.needs_patient_data:
                raise IntentEnvelopeError("meta intent cannot request patient data")
            if self.target not in {IntentTarget.NONE, IntentTarget.CONVERSATION}:
                raise IntentEnvelopeError("meta intent target is invalid")
            if self.answer_mode is not AnswerMode.DETERMINISTIC:
                raise IntentEnvelopeError("meta intent must be deterministic")
            return

        if self.intent in _CONVERSATIONAL_INTENTS:
            if self.needs_patient_data:
                raise IntentEnvelopeError("conversational intent cannot request patient data")
            if self.target not in {IntentTarget.NONE, IntentTarget.CONVERSATION}:
                raise IntentEnvelopeError("conversational target is invalid")
            if self.answer_mode is not AnswerMode.CONVERSATIONAL:
                raise IntentEnvelopeError("conversational intent must use conversational mode")
            return

        if self.intent is IntentKind.UNKNOWN:
            if self.needs_patient_data:
                raise IntentEnvelopeError("unknown intent cannot authorize patient data")
            if self.target is not IntentTarget.NONE:
                raise IntentEnvelopeError("unknown intent target must be none")
            if self.operation is not IntentOperation.NONE:
                raise IntentEnvelopeError("unknown intent operation must be none")
            if self.answer_mode is not AnswerMode.CLARIFY:
                raise IntentEnvelopeError("unknown intent must clarify")
            return

        raise IntentEnvelopeError("unsupported envelope state")


@dataclass(frozen=True, slots=True)
class BackendIntentDecision:
    route: RouteKind
    target: IntentTarget
    reason: str


def decide_backend_route(envelope: IntentEnvelope) -> BackendIntentDecision:
    """Derive executable routing from an untrusted-but-validated intent proposal."""

    if envelope.ambiguity is Ambiguity.HIGH:
        return BackendIntentDecision(RouteKind.CLARIFY, IntentTarget.NONE, "high_ambiguity")

    if envelope.intent in _PATIENT_INTENTS:
        if envelope.confidence < 0.88:
            return BackendIntentDecision(
                RouteKind.CLARIFY,
                IntentTarget.NONE,
                "patient_intent_below_confidence_threshold",
            )
        return BackendIntentDecision(
            RouteKind.DETERMINISTIC_PATIENT_DATA,
            envelope.target,
            "validated_patient_read_intent",
        )

    if envelope.intent in _META_INTENTS:
        if envelope.confidence < 0.78:
            return BackendIntentDecision(RouteKind.CLARIFY, IntentTarget.NONE, "meta_low_confidence")
        return BackendIntentDecision(
            RouteKind.DETERMINISTIC_LOCAL,
            envelope.target,
            "validated_meta_intent",
        )

    if envelope.intent in _CONVERSATIONAL_INTENTS:
        if envelope.confidence < 0.78:
            return BackendIntentDecision(
                RouteKind.CLARIFY,
                IntentTarget.NONE,
                "conversation_low_confidence",
            )
        return BackendIntentDecision(
            RouteKind.CONVERSATIONAL,
            envelope.target,
            "validated_conversational_intent",
        )

    return BackendIntentDecision(RouteKind.CLARIFY, IntentTarget.NONE, "unknown_intent")
