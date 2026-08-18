"""Fail-closed manifest for zero-egress local/on-device STT benchmarks."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, slots=True)
class LocalSTTManifest:
    engine: str
    model: str
    implementation_version: str
    evidence_source: str
    verified_on: date
    review_due_on: date
    approved_for_synthetic_benchmark: bool

    def validate(self, *, today: date) -> None:
        required = {
            "engine": self.engine,
            "model": self.model,
            "implementation_version": self.implementation_version,
            "evidence_source": self.evidence_source,
        }
        missing = tuple(name for name, value in required.items() if not value.strip())
        if missing:
            raise ValueError(
                "missing local STT benchmark manifest fields: " + ", ".join(missing)
            )
        if self.verified_on > today:
            raise ValueError("local STT evidence verification date is in the future")
        if self.review_due_on < today:
            raise ValueError("local STT evidence is stale")
        if not self.approved_for_synthetic_benchmark:
            raise ValueError("local STT engine is not approved for synthetic benchmarking")
