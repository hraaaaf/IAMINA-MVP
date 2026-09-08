"""CGM metric sufficiency contracts.

``LogEntry.source == "cgm"`` proves provenance only. Normative CGM analytics
require an explicit sensor-session window with expected cadence and measurable
coverage. ANALYSIS-4 adds that proof contract without promoting any KPI by
itself; public promotion remains a separate governed step.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import floor
from typing import Protocol

from django.db.models import Q
from django.utils import timezone

from diabetes.models import CGMReadingRecord, CGMSensorSession
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


@dataclass(frozen=True)
class CgmWindowSufficiency:
    verified: bool
    reason: str
    window_days: float
    active_window_pct: float
    capture_pct: float
    coverage_pct: float
    expected_readings: int
    received_readings: int
    session_count: int
    gap_count: int
    evidence_id: str

    def to_metadata(self) -> dict[str, object]:
        return {
            "verified": self.verified,
            "reason": self.reason,
            "window_days": self.window_days,
            "active_window_pct": self.active_window_pct,
            "capture_pct": self.capture_pct,
            "coverage_pct": self.coverage_pct,
            "expected_readings": self.expected_readings,
            "received_readings": self.received_readings,
            "session_count": self.session_count,
            "gap_count": self.gap_count,
            "evidence_id": self.evidence_id,
        }


def assess_cgm_sufficiency(kpis: _KpiLike) -> CgmSufficiency:
    """Preserve the current public fail-closed decision until ANALYSIS-5.

    Row provenance cannot establish sensor wear-time. ANALYSIS-4 introduces
    ``assess_cgm_window`` as the real proof path, but no normative KPI is
    released merely because that proof path now exists.
    """
    evidence = evidence_for_kpi("gmi")
    return CgmSufficiency(
        verified=False,
        reason=(
            "CGM row provenance alone is insufficient; public CGM promotion "
            "requires a verified sensor-session window."
        ),
        days_with_data=int(getattr(kpis, "days_with_data", 0) or 0),
        cgm_row_fraction_pct=(
            float(kpis.cgm_active_pct)
            if getattr(kpis, "cgm_active_pct", None) is not None
            else None
        ),
        evidence_id=evidence.evidence_id,
    )


def _failed_window(reason: str, window_days: float = 0.0) -> CgmWindowSufficiency:
    evidence = evidence_for_kpi("gmi")
    return CgmWindowSufficiency(
        verified=False,
        reason=reason,
        window_days=round(window_days, 4),
        active_window_pct=0.0,
        capture_pct=0.0,
        coverage_pct=0.0,
        expected_readings=0,
        received_readings=0,
        session_count=0,
        gap_count=0,
        evidence_id=evidence.evidence_id,
    )


def assess_cgm_window(
    *,
    patient_id: int,
    window_start,
    window_end,
    min_window_days: float = 14.0,
    min_coverage_pct: float = 70.0,
) -> CgmWindowSufficiency:
    """Measure CGM sufficiency from persisted sensor sessions and readings.

    Coverage is deliberately conservative:

    ``active-window fraction × capture fraction inside declared sessions``.

    Time outside every declared session counts as sensor-off time. Missing
    readings inside a session count as data loss. Overlapping sensor sessions
    are considered ambiguous and fail closed rather than double-counting data.
    """
    if window_start is None or window_end is None or window_end <= window_start:
        return _failed_window("invalid_window")
    if not timezone.is_aware(window_start) or not timezone.is_aware(window_end):
        return _failed_window("timezone_required")

    window_seconds = (window_end - window_start).total_seconds()
    window_days = window_seconds / 86400.0
    if window_days < min_window_days:
        return _failed_window("insufficient_window_duration", window_days)

    sessions = list(
        CGMSensorSession.objects.filter(
            patient_id=patient_id,
            started_at__lt=window_end,
        )
        .filter(Q(ended_at__isnull=True) | Q(ended_at__gt=window_start))
        .order_by("started_at", "id")
    )
    if not sessions:
        return _failed_window("no_sensor_sessions", window_days)

    intervals: list[tuple[CGMSensorSession, object, object]] = []
    previous_end = None
    for session in sessions:
        start = max(session.started_at, window_start)
        end = min(session.ended_at or window_end, window_end)
        if end <= start:
            continue
        if previous_end is not None and start < previous_end:
            return _failed_window("overlapping_sensor_sessions", window_days)
        intervals.append((session, start, end))
        previous_end = end

    if not intervals:
        return _failed_window("no_active_sensor_interval", window_days)

    active_seconds = 0.0
    expected_readings = 0
    received_readings = 0
    gap_count = 0

    for session, start, end in intervals:
        interval_seconds = int(session.expected_interval_minutes) * 60
        duration_seconds = (end - start).total_seconds()
        active_seconds += duration_seconds
        expected_readings += floor(duration_seconds / interval_seconds) + 1

        timestamps = list(
            CGMReadingRecord.objects.filter(
                patient_id=patient_id,
                session_id=session.id,
                source=session.source,
                recorded_at__gte=start,
                recorded_at__lte=end,
            )
            .order_by("recorded_at")
            .values_list("recorded_at", flat=True)
            .distinct()
        )
        received_readings += len(timestamps)
        gap_threshold_seconds = interval_seconds * 1.5
        gap_count += sum(
            1
            for previous, current in zip(timestamps, timestamps[1:])
            if (current - previous).total_seconds() > gap_threshold_seconds
        )

    active_window_pct = min(100.0, (active_seconds / window_seconds) * 100.0)
    capture_pct = (
        min(100.0, (received_readings / expected_readings) * 100.0)
        if expected_readings
        else 0.0
    )
    coverage_pct = (active_window_pct * capture_pct) / 100.0
    verified = coverage_pct >= min_coverage_pct
    reason = "verified" if verified else "insufficient_coverage"
    evidence = evidence_for_kpi("gmi")

    return CgmWindowSufficiency(
        verified=verified,
        reason=reason,
        window_days=round(window_days, 4),
        active_window_pct=round(active_window_pct, 2),
        capture_pct=round(capture_pct, 2),
        coverage_pct=round(coverage_pct, 2),
        expected_readings=expected_readings,
        received_readings=received_readings,
        session_count=len(intervals),
        gap_count=gap_count,
        evidence_id=evidence.evidence_id,
    )
