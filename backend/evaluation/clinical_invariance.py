"""Deterministic clinical-decision invariance primitives.

Provider/model scoring is intentionally out of scope. These helpers compare
clinical authorization snapshots and report exact drift between equivalent
synthetic cases.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class ClinicalDecisionSnapshot:
    intent: str
    authority_level: str
    decision: str
    allowed_actions: tuple[str, ...]
    forbidden_actions: tuple[str, ...]
    rule_id: str
    rule_version: str
    language: str
    required_facts: tuple[str, ...]
    missing_facts: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    limitations: tuple[str, ...]
    escalation: str | None

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "ClinicalDecisionSnapshot":
        def text(key: str) -> str:
            value = payload.get(key)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{key} must be a non-empty string")
            return value.strip()

        def items(key: str) -> tuple[str, ...]:
            value = payload.get(key, ())
            if not isinstance(value, (list, tuple)):
                raise ValueError(f"{key} must be a list or tuple")
            cleaned = []
            for item in value:
                if not isinstance(item, str) or not item.strip():
                    raise ValueError(f"{key} entries must be non-empty strings")
                cleaned.append(item.strip())
            return tuple(sorted(set(cleaned)))

        escalation = payload.get("escalation")
        if escalation is not None:
            if not isinstance(escalation, str) or not escalation.strip():
                raise ValueError("escalation must be null or a non-empty string")
            escalation = escalation.strip()

        return cls(
            intent=text("intent"),
            authority_level=text("authority_level"),
            decision=text("decision"),
            allowed_actions=items("allowed_actions"),
            forbidden_actions=items("forbidden_actions"),
            rule_id=text("rule_id"),
            rule_version=text("rule_version"),
            language=text("language"),
            required_facts=items("required_facts"),
            missing_facts=items("missing_facts"),
            evidence_refs=items("evidence_refs"),
            limitations=items("limitations"),
            escalation=escalation,
        )


_HARD_INVARIANTS = (
    "intent",
    "authority_level",
    "decision",
    "allowed_actions",
    "forbidden_actions",
    "rule_id",
    "rule_version",
    "required_facts",
    "missing_facts",
    "evidence_refs",
    "limitations",
    "escalation",
)


@dataclass(frozen=True, slots=True)
class ClinicalInvarianceResult:
    passed: bool
    mismatches: tuple[str, ...]


def compare_clinical_decisions(
    baseline: ClinicalDecisionSnapshot,
    candidate: ClinicalDecisionSnapshot,
    *,
    include_language: bool = False,
) -> ClinicalInvarianceResult:
    fields = list(_HARD_INVARIANTS)
    if include_language:
        fields.append("language")

    mismatches = tuple(
        field
        for field in fields
        if getattr(baseline, field) != getattr(candidate, field)
    )
    return ClinicalInvarianceResult(passed=not mismatches, mismatches=mismatches)


def require_hard_invariance(
    baseline: ClinicalDecisionSnapshot,
    candidates: tuple[ClinicalDecisionSnapshot, ...],
) -> None:
    failures: list[str] = []
    for index, candidate in enumerate(candidates):
        result = compare_clinical_decisions(baseline, candidate)
        if not result.passed:
            failures.append(f"candidate[{index}]:" + ",".join(result.mismatches))
    if failures:
        raise AssertionError("clinical decision drift: " + "; ".join(failures))


__all__ = [
    "ClinicalDecisionSnapshot",
    "ClinicalInvarianceResult",
    "compare_clinical_decisions",
    "require_hard_invariance",
]
