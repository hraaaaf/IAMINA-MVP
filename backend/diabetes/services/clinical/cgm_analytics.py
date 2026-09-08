"""Deterministic CGM analytics over verified sensor-session readings only."""
from __future__ import annotations

from dataclasses import dataclass
from statistics import stdev

from django.db.models import F, Q

from diabetes.models import CGMReadingRecord


@dataclass(frozen=True)
class VerifiedCgmMetrics:
    cv_pct: float | None
    tir_pct: float | None
    tar_pct: float | None
    tbr_pct: float | None
    reading_count: int


def compute_verified_cgm_metrics(
    *,
    patient_id: int,
    window_start,
    window_end,
    target_low: float = 70.0,
    target_high: float = 180.0,
) -> VerifiedCgmMetrics:
    """Compute descriptive CGM metrics from valid session-linked readings.

    The caller must separately prove CGM sufficiency. This function deliberately
    ignores unlinked transport rows, source/session mismatches and readings that
    fall outside the linked session interval. Duplicate timestamps are collapsed
    so sensor replacement boundaries cannot double-weight a reading.
    """
    rows = (
        CGMReadingRecord.objects.filter(
            patient_id=patient_id,
            session__isnull=False,
            recorded_at__gte=window_start,
            recorded_at__lte=window_end,
            source=F("session__source"),
        )
        .filter(recorded_at__gte=F("session__started_at"))
        .filter(Q(session__ended_at__isnull=True) | Q(recorded_at__lte=F("session__ended_at")))
        .order_by("recorded_at", "id")
        .values_list("recorded_at", "glucose_mg_dl")
    )

    by_timestamp: dict[object, float] = {}
    for recorded_at, glucose in rows:
        by_timestamp.setdefault(recorded_at, float(glucose))

    values = list(by_timestamp.values())
    count = len(values)
    if count == 0:
        return VerifiedCgmMetrics(None, None, None, None, 0)

    tir = 100.0 * sum(target_low <= value <= target_high for value in values) / count
    tar = 100.0 * sum(value > target_high for value in values) / count
    tbr = 100.0 * sum(value < target_low for value in values) / count
    mean = sum(values) / count
    cv = None
    if count >= 2 and mean > 0:
        cv = 100.0 * stdev(values) / mean

    return VerifiedCgmMetrics(
        cv_pct=round(cv, 1) if cv is not None else None,
        tir_pct=round(tir, 1),
        tar_pct=round(tar, 1),
        tbr_pct=round(tbr, 1),
        reading_count=count,
    )
