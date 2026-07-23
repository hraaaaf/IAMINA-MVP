"""
KPI endpoint — Phase 6 SQL-first canonical analytics.
GET /api/v1/kpis/ — returns pre-computed KPIs from sql_analytics.compute_kpis().

Phase 10: responses are Redis-cached for 5 minutes per (user, days, target_low,
target_high) tuple.  Cache is invalidated automatically after any log write
(create / update / delete / batch).  If Redis is down, IGNORE_EXCEPTIONS=True
causes a transparent cache miss and the query runs fresh — no user impact.

Design: see docs/adr/0007-analytical-sql-over-llm.md
"""
from __future__ import annotations

import logging
from typing import Optional

from django.core.cache import cache
from ninja import Router
from pydantic import BaseModel

from diabetes.services.clinical.sql_analytics import AnalyticalKPIs, compute_kpis

logger = logging.getLogger(__name__)
router = Router(tags=["kpis"])

_KPI_TTL = 300  # 5 minutes


# ──────────────────────────────────────────────────────────────
# SCHEMAS
# ──────────────────────────────────────────────────────────────

class KPIsOut(BaseModel):
    avg_glucose: Optional[float]
    std_dev: Optional[float]
    cv_pct: Optional[float]
    tir_pct: Optional[float]
    tar_pct: Optional[float]
    tbr_pct: Optional[float]
    gmi: Optional[float]
    log_count: int
    days_with_data: int
    has_sufficient_data: bool
    # GMI confidence indicator (P2-B)
    gmi_confidence: Optional[str]   # "high" | "medium" | "low" | null
    gmi_basis: str                  # e.g. "47 mesures · 15j"
    # GRI — Glycemia Risk Index (Klonoff et al. 2022 / ADA consensus grid)
    gri: Optional[float]            # 0-100 composite risk score
    gri_zone: Optional[str]         # "A" | "B" | "C" | "D" | "E"
    gri_label_fr: Optional[str]     # Patient-facing French label


# ──────────────────────────────────────────────────────────────
# CACHE HELPERS
# ──────────────────────────────────────────────────────────────

def _kpi_cache_key(user_id: int, days: int, target_low: float, target_high: float) -> str:
    """Stable, human-readable Redis key for a KPI request."""
    return f"kpis:u{user_id}:d{days}:l{int(target_low)}:h{int(target_high)}"


def invalidate_kpi_cache(user_id: int) -> None:
    """
    Wipe all KPI cache entries for this user after any write operation.

    Uses django-redis delete_pattern() which supports glob wildcards.
    Wrapped in try/except so a Redis outage never blocks a write path.
    The KEY_PREFIX ('amina') is prepended by Django's cache layer, so
    the actual stored key is  :1:amina:kpis:u<id>:…  — the wildcard
    must match that prefix.
    """
    try:
        cache.delete_pattern(f"*kpis:u{user_id}:*")
    except Exception:
        # Redis down or pattern not supported — no-op; stale data expires in 5 min
        logger.debug("invalidate_kpi_cache: cache.delete_pattern unavailable (Redis down?)")


# ──────────────────────────────────────────────────────────────
# ENDPOINT
# ──────────────────────────────────────────────────────────────

@router.get("/kpis/", response=KPIsOut)
def get_kpis(
    request,
    days: int = 21,
    target_low: float = 70.0,
    target_high: float = 180.0,
):
    """
    Returns canonical KPIs for the authenticated patient.

    Computed via SQL (ADR-0007). On SQLite, cv_pct and std_dev are null
    (STDDEV_SAMP not available). Full precision requires PostgreSQL.

    Phase 10: Response is Redis-cached for 5 min.
    Cache miss is transparent — falls back to SQL query.

    Query params:
        days        — look-back window in days (default 21)
        target_low  — lower TIR bound in mg/dL (default 70)
        target_high — upper TIR bound in mg/dL (default 180)
    """
    cache_key = _kpi_cache_key(request.user.id, days, target_low, target_high)
    hit = cache.get(cache_key)
    if hit is not None:
        logger.debug("KPI cache HIT for user=%s key=%s", request.user.id, cache_key)
        return hit

    kpis: AnalyticalKPIs = compute_kpis(
        patient_id=request.user.id,
        days=days,
        target_low=target_low,
        target_high=target_high,
    )

    result = {
        "avg_glucose":         kpis.avg_glucose,
        "std_dev":             kpis.std_dev,
        "cv_pct":              kpis.cv_pct,
        "tir_pct":             kpis.tir_pct,
        "tar_pct":             kpis.tar_pct,
        "tbr_pct":             kpis.tbr_pct,
        "gmi":                 kpis.gmi,
        "log_count":           kpis.log_count,
        "days_with_data":      kpis.days_with_data,
        "has_sufficient_data": kpis.has_sufficient_data,
        "gmi_confidence":      kpis.gmi_confidence,
        "gmi_basis":           kpis.gmi_basis,
        "gri":                 kpis.gri,
        "gri_zone":            kpis.gri_zone,
        "gri_label_fr":        kpis.gri_label,
    }

    cache.set(cache_key, result, _KPI_TTL)
    logger.debug("KPI cache SET for user=%s key=%s ttl=%ds", request.user.id, cache_key, _KPI_TTL)
    return result
