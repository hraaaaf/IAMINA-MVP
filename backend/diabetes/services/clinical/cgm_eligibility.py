"""Fail-closed CGM metric sufficiency contract.

`LogEntry.source == "cgm"` proves provenance only. The current schema does not
store device identity/cadence, expected readings, sensor-active intervals or a
vendor-provided wear-time percentage. Therefore the runtime cannot honestly
prove the data sufficiency needed for normative CGM target interpretation.

This module centralizes that fact so individual consumers cannot quietly treat
`cgm_active_pct` (the fraction of stored rows labelled CGM) as sensor wear-time.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from diabetes.services.clinical.evidence_registry import evidence_for_kpi


class _KpiLike(Protocol):
    days_with_data: int
    cgm_active_pct: float | None


@dataclass(frozen=True)
class CgmSufficiency:
    verified: bool
    reason: str
    days_with_data: int
    cgm_row_fraction_pct: float | None
    evidence_id: str

    def to_metadata(self) -> dict[str, object]:
        return {
            "verified": self.verified,
            "reason": self.reason,
            "days_with_data": self.days_with_data,
            "cgm_row_fraction_pct": self.cgm_row_fraction_pct,
            "evidence_id": self.evidence_id,
        }


def assess_cgm_sufficiency(kpis: _KpiLike) -> CgmSufficiency:
    """Return the current CGM sufficiency decision.

    Until ingestion stores a real wear-time/cadence contract, this intentionally
    returns ``verified=False`` for every snapshot. A future LOT may change this
    function only when it can prove actual sensor coverage from governed data.
    """
    evidence = evidence_for_kpi("gmi")
    return CgmSufficiency(
        verified=False,
        reason=(
            "CGM provenance is recorded, but sensor wear-time/cadence coverage "
            "is not available in the current LogEntry schema."
        ),
        days_with_data=int(getattr(kpis, "days_with_data", 0) or 0),
        cgm_row_fraction_pct=(
            float(kpis.cgm_active_pct) if getattr(kpis, "cgm_active_pct", None) is not None else None
        ),
        evidence_id=evidence.evidence_id,
    )
