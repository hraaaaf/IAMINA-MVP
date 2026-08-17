"""Governed longitudinal Companion Context shared by modules and chassis.

This contract carries read-only longitudinal companion state. It is distinct
from ``DomainContext``: DomainContext is the instant/session analytical output,
while CompanionContext is the governed longitudinal projection used by UX and
conversation narration.

The chassis may read this structure but must not create clinical meaning from
raw module data. Modules own the projection and provenance.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CompanionPattern:
    observation_key: str
    current_state: str
    markers: tuple[str, ...]
    evidence_density: str
    recurrence_count: int
    baseline_direction: str
    baseline_movement: str
    first_observed_at: str | None
    last_observed_at: str | None
    evidence_id: str
    source_version: str
    limitations: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class CompanionChange:
    observation_key: str
    change_kind: str
    evidence_strength: str
    missing_data: tuple[str, ...]
    source_version: str


@dataclass(frozen=True, slots=True)
class CompanionAfterVisit:
    status: str
    anchor_id: int | None
    occurred_at: str | None
    source: str | None
    fact_count: int
    latest_fact_at: str | None


@dataclass(frozen=True, slots=True)
class CompanionContext:
    pattern_status: str
    review_status: str
    review_anchor_captured_at: str | None
    patterns: tuple[CompanionPattern, ...]
    changes_since_review: tuple[CompanionChange, ...]
    after_visit: CompanionAfterVisit
    safety_notice: str
    source_version: str
    language: str = "fr"

    @classmethod
    def empty(cls, language: str = "fr") -> "CompanionContext":
        """Neutral read-only context for modules with no longitudinal state."""
        return cls(
            pattern_status="unavailable",
            review_status="unavailable",
            review_anchor_captured_at=None,
            patterns=(),
            changes_since_review=(),
            after_visit=CompanionAfterVisit(
                status="unavailable",
                anchor_id=None,
                occurred_at=None,
                source=None,
                fact_count=0,
                latest_fact_at=None,
            ),
            safety_notice=(
                "Companion support only. No longitudinal companion context is "
                "available for this module."
            ),
            source_version="companion-context.empty.v1",
            language=language,
        )


__all__ = [
    "CompanionAfterVisit",
    "CompanionChange",
    "CompanionContext",
    "CompanionPattern",
]
