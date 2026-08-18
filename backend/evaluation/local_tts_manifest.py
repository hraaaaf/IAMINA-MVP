"""Fail-closed manifest for zero-egress native/local TTS benchmarks."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, slots=True)
class LocalTTSManifest:
    engine: str
    voice: str
    implementation_version: str
    evidence_source: str
    verified_on: date
    review_due_on: date
    approved_locales: tuple[str, ...]
    approved_for_synthetic_benchmark: bool

    def validate(self, *, today: date) -> None:
        required = {
            "engine": self.engine,
            "voice": self.voice,
            "implementation_version": self.implementation_version,
            "evidence_source": self.evidence_source,
        }
        missing = tuple(name for name, value in required.items() if not value.strip())
        if missing:
            raise ValueError(
                "missing local TTS benchmark manifest fields: " + ", ".join(missing)
            )
        if self.verified_on > today:
            raise ValueError("local TTS evidence verification date is in the future")
        if self.review_due_on < today:
            raise ValueError("local TTS evidence is stale")
        if not self.approved_locales:
            raise ValueError("local TTS requires at least one approved locale")
        if not self.approved_for_synthetic_benchmark:
            raise ValueError("local TTS engine is not approved for synthetic benchmarking")
