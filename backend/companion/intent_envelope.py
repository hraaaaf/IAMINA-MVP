"""Strict intent-envelope contract for IAMINA companion routing.

The external model proposes semantic classification metadata only.
It never chooses execution mode, patient-data authority, backend actions, or egress.
IAMINA derives the executable route deterministically after validation.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from enum import StrEnum

SCHEMA_VERSION = "1"


class IntentEnvelopeError(ValueError):
    """Raised when classifier output violates the candidate V1 contract."""


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

_EXACT_TARGET_BY_INTENT = {
    IntentKind.META_GREETING: IntentTarget.CONVERSATION,
    IntentKind.META_IDENTITY: IntentTarget.NONE,
    IntentKind.META_CAPABILITIES: IntentTarget.NONE,
    IntentKind.CONVERSATION_RECALL: IntentTarget.CONVERSATION,
    IntentKind.GENERAL_HEALTH_EDUCATION: IntentTarget.NONE,
    IntentKind.CLINICIAN_PREP: IntentTarget.NONE,
    IntentKind.CASUAL_CONVERSATION: IntentTarget.CONVERSATION,
    IntentKind.EMOTIONAL_SUPPORT: IntentTarget.CONVERSATION,
    IntentKind.UNKNOWN: IntentTarget.NONE,
}


@dataclass(frozen=True, slots=True)
class IntentEnvelope:
    """Untrusted semantic proposal returned by the classifier.

    Deliberately contains no execution/egress fields. IAMINA derives those.
    """

    schema_version: str
    intent: IntentKind
    target: IntentTarget
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
            "confidence",
            "ambiguity",
        }
        if set(payload) != expected:
            raise IntentEnvelopeError(
                f"classifier output keys must equal {sorted(expected)}"
            )
        if payload["schema_version"] != SCHEMA_VERSION:
            raise IntentEnvelopeError("unsupported intent envelope schema version")

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
                confidence=confidence,
                ambiguity=Ambiguity(payload["ambiguity"]),
            )
        except ValueError as exc:
            raise IntentEnvelopeError("classifier output contains an unknown enum value") from exc

        envelope.validate()
        return envelope

    def validate(self) -> None:
        if self.intent in _PATIENT_INTENTS:
            if self.target not in _PATIENT_TARGETS:
                raise IntentEnvelopeError("patient-data intent requires a patient target")
            return

        expected_target = _EXACT_TARGET_BY_INTENT.get(self.intent)
        if expected_target is None:
            raise IntentEnvelopeError("unsupported envelope state")
        if self.target is not expected_target:
            raise IntentEnvelopeError("intent target is inconsistent with intent")


@dataclass(frozen=True, slots=True)
class BackendIntentDecision:
    """IAMINA-owned executable routing decision.

    This is not an external-egress authorization.
    """

    route: RouteKind
    target: IntentTarget
    reason: str


def decide_backend_route(envelope: IntentEnvelope) -> BackendIntentDecision:
    """Derive executable routing from a validated, untrusted semantic proposal."""

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
            (
                "validated_patient_summary_intent"
                if envelope.intent is IntentKind.PATIENT_DATA_SUMMARY
                else "validated_patient_read_intent"
            ),
        )

    if envelope.intent in _META_INTENTS:
        if envelope.confidence < 0.78:
            return BackendIntentDecision(
                RouteKind.CLARIFY,
                IntentTarget.NONE,
                "meta_low_confidence",
            )
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
