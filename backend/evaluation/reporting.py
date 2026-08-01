"""Canonical machine-readable benchmark report generation."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone

from .decision import ProviderDecision
from .runner import CaseRun


@dataclass(frozen=True, slots=True)
class BenchmarkReport:
    schema_version: str
    generated_at: str
    dataset_fingerprints: tuple[str, ...]
    runs: tuple[dict[str, object], ...]
    decisions: tuple[dict[str, object], ...]


def build_report(
    runs: tuple[CaseRun, ...],
    decisions: tuple[ProviderDecision, ...],
    *,
    generated_at: datetime | None = None,
) -> BenchmarkReport:
    timestamp = generated_at or datetime.now(timezone.utc)
    if timestamp.tzinfo is None:
        raise ValueError("generated_at must be timezone-aware")
    fingerprints = tuple(sorted({run.dataset_fingerprint for run in runs}))
    return BenchmarkReport(
        schema_version="1.0",
        generated_at=timestamp.astimezone(timezone.utc).isoformat(),
        dataset_fingerprints=fingerprints,
        runs=tuple(asdict(run) for run in runs),
        decisions=tuple(asdict(decision) for decision in decisions),
    )
