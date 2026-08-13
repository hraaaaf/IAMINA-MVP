"""Read-only normalization boundary for P3-HORIZON source adapters."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Protocol

from diabetes.services.clinical.evidence_horizon_contract import HorizonCandidate


class HorizonScanState(StrEnum):
    COMPLETE = "complete"
    INCOMPLETE = "incomplete"


@dataclass(frozen=True, slots=True)
class HorizonScanBatch:
    source_key: str
    retrieved_at: datetime
    state: HorizonScanState
    candidates: tuple[HorizonCandidate, ...] = ()
    failure_reason: str = ""

    def __post_init__(self) -> None:
        if not self.source_key.strip():
            raise ValueError("source_key must be non-empty")
        if self.retrieved_at.tzinfo is None or self.retrieved_at.utcoffset() is None:
            raise ValueError("retrieved_at must be timezone-aware")
        if self.state == HorizonScanState.INCOMPLETE and not self.failure_reason.strip():
            raise ValueError("incomplete scan requires failure_reason")
        if self.state == HorizonScanState.COMPLETE and self.failure_reason.strip():
            raise ValueError("complete scan cannot carry failure_reason")
        for candidate in self.candidates:
            if candidate.retrieved_at != self.retrieved_at:
                raise ValueError("candidate retrieval timestamp must match batch")

    @property
    def proves_no_updates(self) -> bool:
        return self.state == HorizonScanState.COMPLETE and not self.candidates


class HorizonSourceAdapter(Protocol):
    """Adapter contract. Implementations may fetch externally, this module does not."""

    source_key: str

    def scan(self, *, retrieved_at: datetime) -> HorizonScanBatch: ...


def merge_scan_batches(*batches: HorizonScanBatch) -> HorizonScanBatch:
    """Combine adapter results without turning failures into false empty scans."""
    if not batches:
        raise ValueError("at least one batch is required")
    retrieved_at = batches[0].retrieved_at
    if any(batch.retrieved_at != retrieved_at for batch in batches):
        raise ValueError("all batches must share one retrieval timestamp")

    candidates = tuple(candidate for batch in batches for candidate in batch.candidates)
    incomplete = tuple(batch for batch in batches if batch.state == HorizonScanState.INCOMPLETE)
    if incomplete:
        reason = "; ".join(
            f"{batch.source_key}: {batch.failure_reason}" for batch in incomplete
        )
        state = HorizonScanState.INCOMPLETE
    else:
        reason = ""
        state = HorizonScanState.COMPLETE

    return HorizonScanBatch(
        source_key="aggregate",
        retrieved_at=retrieved_at,
        state=state,
        candidates=candidates,
        failure_reason=reason,
    )
