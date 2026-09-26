"""Structured narration contract between deterministic authority and language models.

The envelope is local product state. It does not grant clinical authority and
must never be interpreted as permission for a model to derive new clinical
meaning.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType
from typing import Mapping

from core.contracts.advice_decision import AdviceDecision

NARRATION_ENVELOPE_CONTRACT_ID = "narration-envelope.v1"
_FACT_KEY_RE = re.compile(r"^FACT_[A-Z0-9_]+$")


class NarrationEnvelopeError(ValueError):
    """Raised when a narration envelope is ambiguous or unsafe."""


class NarrationSpeechAct(StrEnum):
    ACKNOWLEDGE_EMOTION = "acknowledge_emotion"
    EXPLAIN_APPROVED_DATA = "explain_approved_data"
    SUMMARIZE_APPROVED_DATA = "summarize_approved_data"
    PREPARE_CLINICIAN_QUESTIONS = "prepare_clinician_questions"
    RESTATE_GOVERNED_ADVICE = "restate_governed_advice"
    CONVERSATION = "conversation"


class FactEgressPolicy(StrEnum):
    LOCAL_ONLY = "local_only"
    COARSENED_ONLY = "coarsened_only"


@dataclass(frozen=True, slots=True)
class NarrationFact:
    key: str
    semantic_type: str
    rendered_value: str
    egress_policy: FactEgressPolicy = FactEgressPolicy.LOCAL_ONLY
    provider_hint: str | None = None
    required: bool = True
    provenance_ref: str | None = None

    def __post_init__(self) -> None:
        if not _FACT_KEY_RE.fullmatch(self.key):
            raise NarrationEnvelopeError("fact key must match FACT_[A-Z0-9_]+")
        if not self.semantic_type.strip():
            raise NarrationEnvelopeError("semantic_type is required")
        if not self.rendered_value.strip():
            raise NarrationEnvelopeError("rendered_value is required")
        if not isinstance(self.egress_policy, FactEgressPolicy):
            raise NarrationEnvelopeError("egress_policy must be explicit")
        if self.provider_hint is not None and not self.provider_hint.strip():
            raise NarrationEnvelopeError("provider_hint cannot be blank")
        if (
            self.egress_policy is FactEgressPolicy.LOCAL_ONLY
            and self.provider_hint is not None
        ):
            raise NarrationEnvelopeError(
                "local-only fact cannot expose a provider_hint"
            )
        if (
            self.egress_policy is FactEgressPolicy.COARSENED_ONLY
            and self.provider_hint is None
        ):
            raise NarrationEnvelopeError(
                "coarsened-only fact requires a provider_hint"
            )
        if self.provenance_ref is not None and not self.provenance_ref.strip():
            raise NarrationEnvelopeError("provenance_ref cannot be blank")

    @property
    def token(self) -> str:
        return "{{" + self.key + "}}"


@dataclass(frozen=True, slots=True)
class LocaleContract:
    locale: str
    script: str
    register: str = "natural"
    code_switching: bool = False

    def __post_init__(self) -> None:
        if not self.locale.strip():
            raise NarrationEnvelopeError("locale is required")
        if self.script not in {"latin", "arabic", "mixed", "default"}:
            raise NarrationEnvelopeError("unsupported locale script")
        if not self.register.strip():
            raise NarrationEnvelopeError("register is required")


@dataclass(frozen=True, slots=True)
class NarrationEnvelope:
    decision: AdviceDecision
    speech_act: NarrationSpeechAct
    locale: LocaleContract
    facts: tuple[NarrationFact, ...] = ()
    allowed_claims: tuple[str, ...] = ()
    required_claims: tuple[str, ...] = ()
    forbidden_claims: tuple[str, ...] = ()
    relationship_context: Mapping[str, str] = MappingProxyType({})
    style_contract: Mapping[str, str] = MappingProxyType({})
    fallback_reply: str = ""
    verifier_id: str = "structural-shadow.v1"
    contract_id: str = NARRATION_ENVELOPE_CONTRACT_ID

    def __post_init__(self) -> None:
        if self.contract_id != NARRATION_ENVELOPE_CONTRACT_ID:
            raise NarrationEnvelopeError("unsupported narration envelope contract")
        if not isinstance(self.decision, AdviceDecision):
            raise NarrationEnvelopeError("decision must be an AdviceDecision")
        if not isinstance(self.speech_act, NarrationSpeechAct):
            raise NarrationEnvelopeError("speech_act must be explicit")
        if not isinstance(self.locale, LocaleContract):
            raise NarrationEnvelopeError("locale must be a LocaleContract")
        if not self.verifier_id.strip():
            raise NarrationEnvelopeError("verifier_id is required")

        keys = tuple(fact.key for fact in self.facts)
        if len(keys) != len(set(keys)):
            raise NarrationEnvelopeError("fact keys must be unique")

        for field_name in (
            "allowed_claims",
            "required_claims",
            "forbidden_claims",
        ):
            values = getattr(self, field_name)
            if any(not isinstance(value, str) or not value.strip() for value in values):
                raise NarrationEnvelopeError(
                    f"{field_name} must contain non-empty strings"
                )
            if len(values) != len(set(values)):
                raise NarrationEnvelopeError(f"{field_name} must be unique")

        overlap = set(self.required_claims) & set(self.forbidden_claims)
        if overlap:
            raise NarrationEnvelopeError(
                "required_claims cannot also be forbidden_claims"
            )

        object.__setattr__(
            self,
            "relationship_context",
            MappingProxyType(dict(self.relationship_context)),
        )
        object.__setattr__(
            self,
            "style_contract",
            MappingProxyType(dict(self.style_contract)),
        )

    def provider_view(self) -> dict[str, object]:
        """Return the bounded linguistic task surface.

        Local fact values and provenance references are intentionally omitted.
        """
        return {
            "contract_id": self.contract_id,
            "speech_act": self.speech_act.value,
            "authority_level": self.decision.authority_level.value,
            "decision": self.decision.decision.value,
            "allowed_actions": self.decision.allowed_actions,
            "forbidden_actions": self.decision.forbidden_actions,
            "limitations": self.decision.limitations,
            "locale": {
                "code": self.locale.locale,
                "script": self.locale.script,
                "register": self.locale.register,
                "code_switching": self.locale.code_switching,
            },
            "facts": tuple(
                {
                    "token": fact.token,
                    "semantic_type": fact.semantic_type,
                    "required": fact.required,
                    "provider_hint": fact.provider_hint,
                }
                for fact in self.facts
            ),
            "allowed_claims": self.allowed_claims,
            "required_claims": self.required_claims,
            "forbidden_claims": self.forbidden_claims,
            "relationship_context": dict(self.relationship_context),
            "style_contract": dict(self.style_contract),
            "verifier_id": self.verifier_id,
        }


__all__ = [
    "FactEgressPolicy",
    "LocaleContract",
    "NarrationEnvelope",
    "NarrationEnvelopeError",
    "NarrationFact",
    "NarrationSpeechAct",
    "NARRATION_ENVELOPE_CONTRACT_ID",
]
