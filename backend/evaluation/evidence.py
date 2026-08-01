"""Evidence contract for privacy, legal and operational provider facts."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, slots=True)
class ProviderEvidence:
    provider: str
    model: str
    modality: str
    source_owner: str
    source_reference: str
    verified_on: date
    review_due_on: date
    data_regions: tuple[str, ...]
    retention_days: int | None
    training_use: bool | None
    no_retention_available: bool | None
    subprocessors_known: bool

    def disqualifications(self, *, today: date) -> tuple[str, ...]:
        reasons: list[str] = []
        if today > self.review_due_on:
            reasons.append("evidence_stale")
        if not self.source_owner or not self.source_reference:
            reasons.append("evidence_unattributed")
        if not self.data_regions:
            reasons.append("data_region_unknown")
        if self.training_use is not False:
            reasons.append("training_use_not_excluded")
        if self.no_retention_available is not True:
            reasons.append("no_retention_not_confirmed")
        if not self.subprocessors_known:
            reasons.append("subprocessors_unknown")
        return tuple(reasons)
