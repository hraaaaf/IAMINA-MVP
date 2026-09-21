"""Governed clinical-advice authorization contract.

The contract separates *clinical authority* from narration. A generative model may
render an already-authorized decision, but it may never issue an AdviceDecision.
Invalid/untrusted payloads fail closed to a deterministic refusal.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Mapping

from core.contracts.capabilities import Authority


class AdviceAuthorityLevel(StrEnum):
    """Maximum patient-facing authority granted to one decision."""

    L0_CONVERSATION = "L0"
    L1_EDUCATION = "L1"
    L2_LOW_RISK_PRACTICAL = "L2"
    L3_CONTEXTUAL_CLINICAL = "L3"
    L4_PROFESSIONAL_VALIDATION = "L4"
    L5_PROHIBITED = "L5"


class AdviceDisposition(StrEnum):
    ALLOW = "allow"
    CONSTRAIN = "constrain"
    REFUSE = "refuse"
    ESCALATE = "escalate"


_ALLOWED_ISSUERS = frozenset(
    {
        Authority.DETERMINISTIC_ENGINE,
        Authority.SYSTEM,
    }
)


def _clean_tuple(values: tuple[str, ...], *, field_name: str) -> tuple[str, ...]:
    cleaned: list[str] = []
    seen: set[str] = set()
    for raw in values:
        if not isinstance(raw, str) or not raw.strip():
            raise ValueError(f"{field_name} entries must be non-empty strings")
        value = raw.strip()
        if value in seen:
            continue
        seen.add(value)
        cleaned.append(value)
    return tuple(cleaned)


def _mapping_text(payload: Mapping[str, Any], key: str, *, default: str | None = None) -> str:
    raw = payload.get(key, default)
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError(f"{key} must be a non-empty string")
    return raw.strip()


def _mapping_tuple(payload: Mapping[str, Any], key: str) -> tuple[str, ...]:
    raw = payload.get(key, ())
    if not isinstance(raw, (list, tuple)):
        raise ValueError(f"{key} must be a list or tuple")
    return tuple(raw)


@dataclass(frozen=True, slots=True)
class AdviceDecision:
    """One versioned authorization decision produced before narration."""

    intent: str
    authority_level: AdviceAuthorityLevel
    decision: AdviceDisposition
    rule_id: str
    rule_version: str

    allowed_actions: tuple[str, ...] = ()
    forbidden_actions: tuple[str, ...] = ()
    required_facts: tuple[str, ...] = ()
    missing_facts: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()
    escalation: str | None = None
    language: str = "fr"
    issued_by: Authority = Authority.DETERMINISTIC_ENGINE

    def __post_init__(self) -> None:
        for field_name in ("intent", "rule_id", "rule_version", "language"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} is required")
            object.__setattr__(self, field_name, value.strip())

        if not isinstance(self.authority_level, AdviceAuthorityLevel):
            raise ValueError("authority_level must be an AdviceAuthorityLevel")
        if not isinstance(self.decision, AdviceDisposition):
            raise ValueError("decision must be an AdviceDisposition")
        if not isinstance(self.issued_by, Authority):
            raise ValueError("issued_by must be an Authority")
        if self.issued_by not in _ALLOWED_ISSUERS:
            raise PermissionError(
                "AdviceDecision may only be issued by deterministic_engine or system"
            )
        if (
            self.decision in {AdviceDisposition.ALLOW, AdviceDisposition.CONSTRAIN}
            and self.issued_by is not Authority.DETERMINISTIC_ENGINE
        ):
            raise PermissionError(
                "only deterministic_engine may authorize patient-facing advice"
            )

        for field_name in (
            "allowed_actions",
            "forbidden_actions",
            "required_facts",
            "missing_facts",
            "evidence_refs",
            "limitations",
        ):
            object.__setattr__(
                self,
                field_name,
                _clean_tuple(getattr(self, field_name), field_name=field_name),
            )

        if self.escalation is not None:
            if not isinstance(self.escalation, str) or not self.escalation.strip():
                raise ValueError("escalation cannot be blank")
            object.__setattr__(self, "escalation", self.escalation.strip())

        overlap = set(self.allowed_actions) & set(self.forbidden_actions)
        if overlap:
            raise ValueError(
                "an action cannot be both allowed and forbidden: "
                + ", ".join(sorted(overlap))
            )

        if self.decision is AdviceDisposition.REFUSE and self.allowed_actions:
            raise ValueError("refuse decisions cannot contain allowed_actions")

        if self.decision is AdviceDisposition.ESCALATE and self.escalation is None:
            raise ValueError("escalate decisions require escalation")

        if self.authority_level is AdviceAuthorityLevel.L4_PROFESSIONAL_VALIDATION:
            if self.decision is not AdviceDisposition.ESCALATE:
                raise ValueError("L4 decisions must escalate for professional validation")

        if self.authority_level is AdviceAuthorityLevel.L5_PROHIBITED:
            if self.decision is not AdviceDisposition.REFUSE:
                raise ValueError("L5 decisions must refuse")
            if self.allowed_actions:
                raise ValueError("L5 decisions cannot contain allowed_actions")

        if (
            self.authority_level
            in {
                AdviceAuthorityLevel.L2_LOW_RISK_PRACTICAL,
                AdviceAuthorityLevel.L3_CONTEXTUAL_CLINICAL,
            }
            and self.decision
            in {AdviceDisposition.ALLOW, AdviceDisposition.CONSTRAIN}
            and not self.evidence_refs
        ):
            raise ValueError("L2/L3 allowed advice requires evidence_refs")

        if (
            self.authority_level is AdviceAuthorityLevel.L3_CONTEXTUAL_CLINICAL
            and self.decision
            in {AdviceDisposition.ALLOW, AdviceDisposition.CONSTRAIN}
            and self.missing_facts
        ):
            raise ValueError("L3 contextual advice cannot proceed with missing_facts")

    @property
    def can_narrate_patient_action(self) -> bool:
        return (
            self.decision in {AdviceDisposition.ALLOW, AdviceDisposition.CONSTRAIN}
            and bool(self.allowed_actions)
            and self.authority_level
            not in {
                AdviceAuthorityLevel.L4_PROFESSIONAL_VALIDATION,
                AdviceAuthorityLevel.L5_PROHIBITED,
            }
        )

    def is_action_allowed(self, action: str) -> bool:
        action = (action or "").strip()
        return (
            bool(action)
            and self.can_narrate_patient_action
            and action in self.allowed_actions
            and action not in self.forbidden_actions
        )

    def assert_action_allowed(self, action: str) -> None:
        if not self.is_action_allowed(action):
            raise PermissionError(
                f"action {action!r} is not authorized by {self.rule_id}@{self.rule_version}"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "intent": self.intent,
            "authority_level": self.authority_level.value,
            "decision": self.decision.value,
            "allowed_actions": list(self.allowed_actions),
            "forbidden_actions": list(self.forbidden_actions),
            "required_facts": list(self.required_facts),
            "missing_facts": list(self.missing_facts),
            "evidence_refs": list(self.evidence_refs),
            "rule_id": self.rule_id,
            "rule_version": self.rule_version,
            "limitations": list(self.limitations),
            "escalation": self.escalation,
            "language": self.language,
            "issued_by": self.issued_by.value,
        }

    @classmethod
    def from_mapping_fail_closed(
        cls,
        payload: Mapping[str, Any],
        *,
        language: str = "fr",
    ) -> "AdviceDecision":
        """Parse an untrusted serialized decision or return a safe refusal."""

        try:
            escalation = payload.get("escalation")
            if escalation is not None and not isinstance(escalation, str):
                raise ValueError("escalation must be a string or null")
            return cls(
                intent=_mapping_text(payload, "intent"),
                authority_level=AdviceAuthorityLevel(
                    _mapping_text(payload, "authority_level")
                ),
                decision=AdviceDisposition(_mapping_text(payload, "decision")),
                rule_id=_mapping_text(payload, "rule_id"),
                rule_version=_mapping_text(payload, "rule_version"),
                allowed_actions=_mapping_tuple(payload, "allowed_actions"),
                forbidden_actions=_mapping_tuple(payload, "forbidden_actions"),
                required_facts=_mapping_tuple(payload, "required_facts"),
                missing_facts=_mapping_tuple(payload, "missing_facts"),
                evidence_refs=_mapping_tuple(payload, "evidence_refs"),
                limitations=_mapping_tuple(payload, "limitations"),
                escalation=escalation,
                language=_mapping_text(payload, "language", default=language),
                issued_by=Authority(
                    _mapping_text(
                        payload,
                        "issued_by",
                        default=Authority.DETERMINISTIC_ENGINE.value,
                    )
                ),
            )
        except (KeyError, TypeError, ValueError, PermissionError):
            return cls.fail_closed(language=language)

    @classmethod
    def fail_closed(cls, *, language: str = "fr") -> "AdviceDecision":
        """Canonical refusal for invalid, missing or untrusted authorization."""

        return cls(
            intent="authorization_invalid",
            authority_level=AdviceAuthorityLevel.L5_PROHIBITED,
            decision=AdviceDisposition.REFUSE,
            rule_id="core.advice.fail_closed",
            rule_version="1",
            forbidden_actions=("patient_facing_clinical_action",),
            limitations=("invalid_or_untrusted_advice_decision",),
            language=language,
            issued_by=Authority.SYSTEM,
        )


__all__ = [
    "AdviceAuthorityLevel",
    "AdviceDecision",
    "AdviceDisposition",
]
