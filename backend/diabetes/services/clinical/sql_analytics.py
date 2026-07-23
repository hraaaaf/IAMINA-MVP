"""
IAmina — Analytical SQL Layer (Phase 6)
========================================
All clinical KPIs (TIR, GMI, CV, averages) are computed via raw SQL
executed against PostgreSQL. The LLM never performs arithmetic;
it only interprets the pre-computed results.

Design decision: see docs/adr/0007-analytical-sql-over-llm.md
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

from django.db import connection

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────
# 1. RESULT STRUCTURE
# ──────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class AnalyticalKPIs:
    """Immutable KPI snapshot produced by SQL. All values are in mg/dL."""
    avg_glucose: Optional[float]       # Mean blood glucose
    std_dev: Optional[float]           # Standard deviation (variability proxy)
    cv_pct: Optional[float]            # Coefficient of Variation (%) — target ≤ 36%
    tir_pct: Optional[float]           # Time In Range 70-180 mg/dL — target ≥ 70%
    tar_pct: Optional[float]           # Time Above Range > 180 mg/dL
    tbr_pct: Optional[float]           # Time Below Range < 70 mg/dL
    gmi: Optional[float]               # Glucose Management Indicator (ADA formula)
    log_count: int                     # Number of entries analysed
    days_with_data: int                # Distinct calendar days with at least 1 log
    # GRI — Glycemia Risk Index (Klonoff et al. 2022 / ADA consensus grid)
    gri: Optional[float] = None        # 0-100 composite risk score
    gri_zone: Optional[str] = None     # "A" | "B" | "C" | "D" | "E"
    gri_label: Optional[str] = None    # Patient-facing French label
    # ATTD/Battelino 5-zone breakdown (clinician-facing doctor_brief PDF)
    # Sum invariants: tbr_level2 + tbr_level1 ≈ tbr_pct ; tar_level1 + tar_level2 ≈ tar_pct
    tbr_level2_pct: Optional[float] = None  # < 54 mg/dL
    tbr_level1_pct: Optional[float] = None  # 54–69 mg/dL
    tar_level1_pct: Optional[float] = None  # 181–250 mg/dL
    tar_level2_pct: Optional[float] = None  # > 250 mg/dL
    cgm_active_pct: Optional[float] = None  # % readings with source='cgm'

    @property
    def has_sufficient_data(self) -> bool:
        """Minimum 5 entries required for meaningful KPI computation."""
        return self.log_count >= 5

    @property
    def is_stable(self) -> bool:
        """CV ≤ 36% is the ADA threshold for glycemic stability."""
        return self.cv_pct is not None and self.cv_pct <= 36.0

    @property
    def gmi_confidence(self) -> str | None:
        """
        ADA-aligned GMI reliability grade based on data coverage.

        ADA recommends ≥ 14 days of glucose data for reliable GMI/TIR estimates.
        Thresholds tuned for SMBG (2-5 readings/day) rather than CGM.

        Returns:
            "high"   — ≥ 14 days AND ≥ 50 readings  (ADA minimum met)
            "medium" — ≥ 7 days  OR  ≥ 25 readings  (indicative, interpret with caution)
            "low"    — ≥ 5 readings  (computed but unreliable — show warning)
            None     — < 5 readings  (GMI not computed)
        """
        if self.log_count < 5:
            return None
        if self.days_with_data >= 14 and self.log_count >= 50:
            return "high"
        if self.days_with_data >= 7 or self.log_count >= 25:
            return "medium"
        return "low"

    @property
    def gmi_basis(self) -> str:
        """
        Human-readable summary of the data used to compute GMI.
        Displayed in the UI as a confidence footnote.
        e.g. "sur 47 mesures · 15 jours"
        """
        if self.log_count < 5:
            return "données insuffisantes"
        parts = [f"{self.log_count} mesures"]
        if self.days_with_data > 0:
            parts.append(f"{self.days_with_data}j")
        return " · ".join(parts)


# ──────────────────────────────────────────────────────────────
# 2. CORE SQL QUERY (dual: PostgreSQL native / SQLite fallback)
# ──────────────────────────────────────────────────────────────

# PostgreSQL: STDDEV_SAMP and CV% computed natively — no second query needed.
_KPI_SQL_PG = """
SELECT
    COUNT(*)                                                                            AS log_count,
    COUNT(DISTINCT date(COALESCE(logged_at, created_at)))                              AS days_with_data,
    ROUND(AVG(blood_sugar)::numeric, 1)                                                AS avg_glucose,
    ROUND(STDDEV_SAMP(blood_sugar)::numeric, 1)                                        AS std_dev,
    ROUND(
        (100.0 * STDDEV_SAMP(blood_sugar) / NULLIF(AVG(blood_sugar), 0))::numeric, 1
    )                                                                                   AS cv_pct,
    ROUND(
        100.0 * SUM(CASE WHEN blood_sugar BETWEEN %(low)s AND %(high)s THEN 1 ELSE 0 END)
        / NULLIF(COUNT(*), 0),
        1
    )                                                                                   AS tir_pct,
    ROUND(
        100.0 * SUM(CASE WHEN blood_sugar > %(high)s THEN 1 ELSE 0 END)
        / NULLIF(COUNT(*), 0),
        1
    )                                                                                   AS tar_pct,
    ROUND(
        100.0 * SUM(CASE WHEN blood_sugar < %(low)s THEN 1 ELSE 0 END)
        / NULLIF(COUNT(*), 0),
        1
    )                                                                                   AS tbr_pct,
    CASE
        WHEN COUNT(*) >= 5
        THEN ROUND((3.31 + 0.02392 * AVG(blood_sugar))::numeric, 1)
        ELSE NULL
    END                                                                                 AS gmi,
    ROUND(
        100.0 * SUM(CASE WHEN blood_sugar < 54 THEN 1 ELSE 0 END)
        / NULLIF(COUNT(*), 0),
        1
    )                                                                                   AS vlow_pct,
    ROUND(
        100.0 * SUM(CASE WHEN blood_sugar > 250 THEN 1 ELSE 0 END)
        / NULLIF(COUNT(*), 0),
        1
    )                                                                                   AS vhigh_pct,
    ROUND(
        100.0 * SUM(CASE WHEN blood_sugar BETWEEN 54 AND 69 THEN 1 ELSE 0 END)
        / NULLIF(COUNT(*), 0),
        1
    )                                                                                   AS tbr_level1_pct,
    ROUND(
        100.0 * SUM(CASE WHEN blood_sugar BETWEEN 181 AND 250 THEN 1 ELSE 0 END)
        / NULLIF(COUNT(*), 0),
        1
    )                                                                                   AS tar_level1_pct,
    ROUND(
        100.0 * SUM(CASE WHEN source = 'cgm' THEN 1 ELSE 0 END)
        / NULLIF(COUNT(*), 0),
        1
    )                                                                                   AS cgm_active_pct
FROM diabetes_logentry
WHERE
    patient_id = %(patient_id)s
    AND COALESCE(logged_at, created_at) >= %(cutoff)s
    AND blood_sugar IS NOT NULL
    AND blood_sugar > 0
"""

# SQLite: STDDEV_SAMP unavailable — std_dev/cv_pct computed by _compute_stddev_cv().
_KPI_SQL_SQLITE = """
SELECT
    COUNT(*)                                                    AS log_count,
    COUNT(DISTINCT date(logged_at))                            AS days_with_data,
    AVG(blood_sugar)                                           AS avg_glucose,
    NULL                                                       AS std_dev,
    NULL                                                       AS cv_pct,
    ROUND(
        100.0 * SUM(CASE WHEN blood_sugar BETWEEN %(low)s AND %(high)s THEN 1 ELSE 0 END)
        / NULLIF(COUNT(*), 0),
        1
    )                                                          AS tir_pct,
    ROUND(
        100.0 * SUM(CASE WHEN blood_sugar > %(high)s THEN 1 ELSE 0 END)
        / NULLIF(COUNT(*), 0),
        1
    )                                                          AS tar_pct,
    ROUND(
        100.0 * SUM(CASE WHEN blood_sugar < %(low)s THEN 1 ELSE 0 END)
        / NULLIF(COUNT(*), 0),
        1
    )                                                          AS tbr_pct,
    CASE
        WHEN COUNT(*) >= 5
        THEN (3.31 + 0.02392 * AVG(blood_sugar))
        ELSE NULL
    END                                                        AS gmi,
    ROUND(
        100.0 * SUM(CASE WHEN blood_sugar < 54 THEN 1 ELSE 0 END)
        / NULLIF(COUNT(*), 0),
        1
    )                                                          AS vlow_pct,
    ROUND(
        100.0 * SUM(CASE WHEN blood_sugar > 250 THEN 1 ELSE 0 END)
        / NULLIF(COUNT(*), 0),
        1
    )                                                          AS vhigh_pct,
    ROUND(
        100.0 * SUM(CASE WHEN blood_sugar BETWEEN 54 AND 69 THEN 1 ELSE 0 END)
        / NULLIF(COUNT(*), 0),
        1
    )                                                          AS tbr_level1_pct,
    ROUND(
        100.0 * SUM(CASE WHEN blood_sugar BETWEEN 181 AND 250 THEN 1 ELSE 0 END)
        / NULLIF(COUNT(*), 0),
        1
    )                                                          AS tar_level1_pct,
    ROUND(
        100.0 * SUM(CASE WHEN source = 'cgm' THEN 1 ELSE 0 END)
        / NULLIF(COUNT(*), 0),
        1
    )                                                          AS cgm_active_pct
FROM diabetes_logentry
WHERE
    patient_id = %(patient_id)s
    AND COALESCE(logged_at, created_at) >= %(cutoff)s
    AND blood_sugar IS NOT NULL
    AND blood_sugar > 0
"""


def compute_kpis(
    patient_id: int,
    days: int = 21,
    target_low: float = 70.0,
    target_high: float = 180.0,
) -> AnalyticalKPIs:
    """
    Execute the analytical SQL query and return an immutable KPI snapshot.

    Args:
        patient_id: Django User PK (patient owner).
        days: Look-back window in days.
        target_low: Lower TIR bound in mg/dL.
        target_high: Upper TIR bound in mg/dL.

    Returns:
        AnalyticalKPIs dataclass. All float fields may be None if insufficient data.
    """
    from datetime import timedelta

    from django.utils import timezone

    cutoff = timezone.now() - timedelta(days=days)
    params = {
        "patient_id": patient_id,
        "cutoff": cutoff,
        "low": target_low,
        "high": target_high,
    }

    sql = _KPI_SQL_PG if connection.vendor == "postgresql" else _KPI_SQL_SQLITE

    try:
        with connection.cursor() as cursor:
            cursor.execute(sql, params)
            row = cursor.fetchone()

        if not row:
            return _empty_kpis()

        (
            log_count, days_with_data, avg_glucose, std_dev,
            cv_pct, tir_pct, tar_pct, tbr_pct, gmi,
            vlow_pct, vhigh_pct, tbr_level1_pct, tar_level1_pct, cgm_active_pct,
        ) = row

        # Python fallback for std_dev/cv_pct on SQLite (PostgreSQL computes natively)
        if std_dev is None and avg_glucose and int(log_count or 0) >= 2:
            std_dev, cv_pct = _compute_stddev_cv(
                patient_id=patient_id,
                cutoff=cutoff,
                avg_glucose=float(avg_glucose),
            )

        # GRI — Glycemia Risk Index (Klonoff et al. 2022)
        stats = {
            "vlow_pct":  float(vlow_pct  or 0),
            "low_pct":   float(tbr_pct   or 0),
            "vhigh_pct": float(vhigh_pct or 0),
            "high_pct":  float(tar_pct   or 0),
            "log_count": int(log_count   or 0),
        }
        gri_score = _compute_gri(stats)
        gri_zone_val = gri_zone(gri_score) if gri_score is not None else None
        gri_label_val = gri_label_fr(gri_zone_val) if gri_zone_val is not None else None

        return AnalyticalKPIs(
            avg_glucose=_round(avg_glucose),
            std_dev=_round(std_dev),
            cv_pct=_round(cv_pct),
            tir_pct=_round(tir_pct),
            tar_pct=_round(tar_pct),
            tbr_pct=_round(tbr_pct),
            gmi=_round(gmi),
            log_count=int(log_count or 0),
            days_with_data=int(days_with_data or 0),
            gri=gri_score,
            gri_zone=gri_zone_val,
            gri_label=gri_label_val,
            tbr_level2_pct=_round(vlow_pct),
            tbr_level1_pct=_round(tbr_level1_pct),
            tar_level1_pct=_round(tar_level1_pct),
            tar_level2_pct=_round(vhigh_pct),
            cgm_active_pct=_round(cgm_active_pct),
        )

    except Exception:
        logger.exception("sql_analytics.compute_kpis failed for patient=%s", patient_id)
        return _empty_kpis()


# ──────────────────────────────────────────────────────────────
# 3. TIME-SLICED BREAKDOWN (for chart contextualisation)
# ──────────────────────────────────────────────────────────────

_DAILY_AVG_SQL = """
SELECT
    date(COALESCE(logged_at, created_at))  AS day,
    AVG(blood_sugar)                       AS avg_glucose,
    COUNT(*)                               AS entries
FROM diabetes_logentry
WHERE
    patient_id = %(patient_id)s
    AND COALESCE(logged_at, created_at) >= %(cutoff)s
    AND blood_sugar IS NOT NULL
    AND blood_sugar > 0
GROUP BY date(logged_at)
ORDER BY date(logged_at) ASC
"""


def compute_daily_averages(patient_id: int, days: int = 21) -> list[dict]:
    """
    Returns a list of {day, avg_glucose, entries} dicts for chart rendering.
    Used by the Flutter contextual overlay (Benchmark Linx).
    """
    from datetime import timedelta

    from django.utils import timezone

    cutoff = timezone.now() - timedelta(days=days)
    try:
        with connection.cursor() as cursor:
            cursor.execute(_DAILY_AVG_SQL, {"patient_id": patient_id, "cutoff": cutoff})
            rows = cursor.fetchall()
        return [
            {"day": str(r[0]), "avg_glucose": float(r[1]), "entries": int(r[2])}
            for r in rows
        ]
    except Exception:
        logger.exception("sql_analytics.compute_daily_averages failed for patient=%s", patient_id)
        return []


# ──────────────────────────────────────────────────────────────
# 4. AGP HOURLY PROFILE — real percentiles
# ──────────────────────────────────────────────────────────────
# PostgreSQL: PERCENTILE_CONT native (exact linear interpolation, O(n log n)).
# SQLite: fetch raw (hour, blood_sugar) pairs → Python-side percentile.
# Both paths return identical {hour, avg, p5, p25, p75, p95} structure.

_AGP_PROFILE_SQL_PG = """
SELECT
    EXTRACT(HOUR FROM COALESCE(logged_at, created_at))::int          AS hour,
    ROUND(AVG(blood_sugar)::numeric, 1)                              AS avg,
    ROUND(PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY blood_sugar)::numeric, 1) AS p5,
    ROUND(PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY blood_sugar)::numeric, 1) AS p25,
    ROUND(PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY blood_sugar)::numeric, 1) AS p50,
    ROUND(PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY blood_sugar)::numeric, 1) AS p75,
    ROUND(PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY blood_sugar)::numeric, 1) AS p95
FROM diabetes_logentry
WHERE
    patient_id = %(patient_id)s
    AND COALESCE(logged_at, created_at) >= %(cutoff)s
    AND blood_sugar IS NOT NULL
    AND blood_sugar > 0
GROUP BY hour
ORDER BY hour ASC
"""

_AGP_RAW_SQL_SQLITE = """
SELECT
    CAST(strftime('%%H', COALESCE(logged_at, created_at)) AS INTEGER) AS hour,
    blood_sugar
FROM diabetes_logentry
WHERE
    patient_id = %(patient_id)s
    AND COALESCE(logged_at, created_at) >= %(cutoff)s
    AND blood_sugar IS NOT NULL
    AND blood_sugar > 0
ORDER BY hour ASC
"""


def _percentile(sorted_vals: list[float], p: float) -> Optional[float]:
    """Linear-interpolation percentile on a pre-sorted list."""
    if not sorted_vals:
        return None
    n = len(sorted_vals)
    idx = p * (n - 1)
    lo, hi = int(idx), min(int(idx) + 1, n - 1)
    frac = idx - lo
    return _round(sorted_vals[lo] * (1 - frac) + sorted_vals[hi] * frac)


def compute_agp_profile(patient_id: int, days: int = 21) -> list[dict]:
    """
    24h time-of-day glucose profile with true percentiles (p5/p25/p75/p95).
    Uses PERCENTILE_CONT on PostgreSQL; Python-side on SQLite (dev).
    """
    from collections import defaultdict
    from datetime import timedelta

    from django.utils import timezone

    cutoff = timezone.now() - timedelta(days=days)
    params = {"patient_id": patient_id, "cutoff": cutoff}

    if connection.vendor == "postgresql":
        try:
            with connection.cursor() as cursor:
                cursor.execute(_AGP_PROFILE_SQL_PG, params)
                rows = cursor.fetchall()
            return [
                {
                    "hour": int(r[0]),
                    "avg":  _round(r[1]),
                    "p5":   _round(r[2]),
                    "p25":  _round(r[3]),
                    "p50":  _round(r[4]),   # true median — ADA AGP standard
                    "p75":  _round(r[5]),
                    "p95":  _round(r[6]),
                }
                for r in rows
            ]
        except Exception:
            logger.exception("compute_agp_profile (PG) failed for patient=%s", patient_id)
            return []

    # SQLite: fetch raw rows, group in Python, compute percentiles
    try:
        with connection.cursor() as cursor:
            cursor.execute(_AGP_RAW_SQL_SQLITE, params)
            raw = cursor.fetchall()

        by_hour: dict[int, list[float]] = defaultdict(list)
        for hour, val in raw:
            by_hour[int(hour)].append(float(val))

        result = []
        for hour in sorted(by_hour):
            vals = sorted(by_hour[hour])
            avg = _round(sum(vals) / len(vals))
            result.append({
                "hour": hour,
                "avg":  avg,
                "p5":   _percentile(vals, 0.05),
                "p25":  _percentile(vals, 0.25),
                "p50":  _percentile(vals, 0.50),   # true median — ADA AGP standard
                "p75":  _percentile(vals, 0.75),
                "p95":  _percentile(vals, 0.95),
            })
        return result
    except Exception:
        logger.exception("compute_agp_profile (SQLite) failed for patient=%s", patient_id)
        return []


# ──────────────────────────────────────────────────────────────
# 5. WEEK-OVER-WEEK TREND
# ──────────────────────────────────────────────────────────────

_TREND_SQL = """
SELECT
    ROUND(
        100.0 * SUM(CASE WHEN blood_sugar BETWEEN %(low)s AND %(high)s THEN 1 ELSE 0 END)
        / NULLIF(COUNT(*), 0),
        1
    )  AS tir_pct,
    ROUND(AVG(blood_sugar)::numeric, 1)  AS avg_glucose
FROM diabetes_logentry
WHERE
    patient_id = %(patient_id)s
    AND COALESCE(logged_at, created_at) >= %(cutoff)s
    AND COALESCE(logged_at, created_at) < %(end)s
    AND blood_sugar IS NOT NULL
    AND blood_sugar > 0
"""

_TREND_SQL_SQLITE = """
SELECT
    ROUND(
        100.0 * SUM(CASE WHEN blood_sugar BETWEEN %(low)s AND %(high)s THEN 1 ELSE 0 END)
        / NULLIF(COUNT(*), 0),
        1
    )  AS tir_pct,
    AVG(blood_sugar)  AS avg_glucose
FROM diabetes_logentry
WHERE
    patient_id = %(patient_id)s
    AND COALESCE(logged_at, created_at) >= %(cutoff)s
    AND COALESCE(logged_at, created_at) < %(end)s
    AND blood_sugar IS NOT NULL
    AND blood_sugar > 0
"""


def compute_trend(
    patient_id: int,
    target_low: float = 70.0,
    target_high: float = 180.0,
) -> dict:
    """
    Week-over-week TIR and average glucose trend.

    Returns:
        {
            "current_week_tir": float | None,
            "prev_week_tir": float | None,
            "tir_delta": float | None,      # positive = improving
            "current_week_avg": float | None,
            "prev_week_avg": float | None,
            "direction": "up" | "down" | "stable" | "unknown",
        }
    """
    from datetime import timedelta

    from django.utils import timezone

    now = timezone.now()
    week_start = now - timedelta(days=7)
    prev_start = now - timedelta(days=14)

    sql = _TREND_SQL if connection.vendor == "postgresql" else _TREND_SQL_SQLITE
    base_params = {"patient_id": patient_id, "low": target_low, "high": target_high}

    def _query(cutoff, end):
        params = {**base_params, "cutoff": cutoff, "end": end}
        try:
            with connection.cursor() as cur:
                cur.execute(sql, params)
                row = cur.fetchone()
            if row:
                return _round(row[0]), _round(row[1])
        except Exception:
            logger.exception("compute_trend window query failed for patient=%s", patient_id)
        return None, None

    curr_tir, curr_avg = _query(week_start, now)
    prev_tir, prev_avg = _query(prev_start, week_start)

    tir_delta = None
    direction = "unknown"
    if curr_tir is not None and prev_tir is not None:
        tir_delta = round(curr_tir - prev_tir, 1)
        if tir_delta > 3:
            direction = "up"
        elif tir_delta < -3:
            direction = "down"
        else:
            direction = "stable"

    return {
        "current_week_tir": curr_tir,
        "prev_week_tir": prev_tir,
        "tir_delta": tir_delta,
        "current_week_avg": curr_avg,
        "prev_week_avg": prev_avg,
        "direction": direction,
    }


# ──────────────────────────────────────────────────────────────
# 6. HELPERS
# ──────────────────────────────────────────────────────────────

def _round(value, ndigits: int = 1) -> Optional[float]:
    """Safe round — returns None if value is None."""
    return round(float(value), ndigits) if value is not None else None


def _empty_kpis() -> AnalyticalKPIs:
    return AnalyticalKPIs(
        avg_glucose=None, std_dev=None, cv_pct=None,
        tir_pct=None, tar_pct=None, tbr_pct=None,
        gmi=None, log_count=0, days_with_data=0,
        gri=None, gri_zone=None, gri_label=None,
    )


def _compute_gri(stats: dict) -> Optional[float]:
    """
    Glycemia Risk Index — Klonoff et al. 2022 / ADA consensus.

    GRI = 3.0 × VLow% + 2.4 × Low% + 1.6 × VHigh% + 0.8 × High%

    Requires at least 5 readings; returns None otherwise.
    All percentage inputs are 0-100 (not fractions).

    Args:
        stats: dict with keys vlow_pct, low_pct, vhigh_pct, high_pct, log_count
    """
    if stats.get("log_count", 0) < 5:
        return None
    score = (
        3.0 * stats.get("vlow_pct",  0.0)
        + 2.4 * stats.get("low_pct",   0.0)
        + 1.6 * stats.get("vhigh_pct", 0.0)
        + 0.8 * stats.get("high_pct",  0.0)
    )
    # GRI is capped at 100 per the original paper
    return _round(min(score, 100.0))


def gri_zone(gri_score: Optional[float]) -> Optional[str]:
    """
    ADA consensus grid zone classifier.

    A: 0-20   — excellent glycemic health
    B: 20-40  — good glycemic health
    C: 40-60  — moderate risk
    D: 60-80  — poor control
    E: >80    — very high risk
    """
    if gri_score is None:
        return None
    if gri_score <= 20:
        return "A"
    if gri_score <= 40:
        return "B"
    if gri_score <= 60:
        return "C"
    if gri_score <= 80:
        return "D"
    return "E"


def gri_label_fr(zone: Optional[str]) -> Optional[str]:
    """Patient-facing French labels for each GRI zone."""
    labels = {
        "A": "Contrôle glycémique excellent",
        "B": "Bon contrôle glycémique",
        "C": "Risque glycémique modéré",
        "D": "Contrôle glycémique insuffisant",
        "E": "Risque glycémique très élevé",
    }
    return labels.get(zone)


def _compute_stddev_cv(
    patient_id: int,
    cutoff,
    avg_glucose: float,
) -> tuple[Optional[float], Optional[float]]:
    """
    Python fallback for std_dev and cv_pct on SQLite.
    Only called when STDDEV_SAMP is unavailable (non-PostgreSQL).
    """
    import math

    sql = """
        SELECT blood_sugar
        FROM diabetes_logentry
        WHERE patient_id = %(patient_id)s
          AND COALESCE(logged_at, created_at) >= %(cutoff)s
          AND blood_sugar IS NOT NULL
          AND blood_sugar > 0
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute(sql, {"patient_id": patient_id, "cutoff": cutoff})
            values = [float(row[0]) for row in cursor.fetchall()]

        if len(values) < 2:
            return None, None

        variance = sum((v - avg_glucose) ** 2 for v in values) / (len(values) - 1)
        std_dev = math.sqrt(variance)
        cv_pct  = (std_dev / avg_glucose) * 100 if avg_glucose > 0 else None
        return _round(std_dev), _round(cv_pct)

    except Exception:
        logger.exception("_compute_stddev_cv failed for patient=%s", patient_id)
        return None, None
