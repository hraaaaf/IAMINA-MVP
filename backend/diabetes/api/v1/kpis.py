"""KPI endpoint — SQL-first analytics with evidence-gated public authority.

GET /api/v1/kpis/ computes descriptive analytics through ``sql_analytics`` and
then projects only clinically eligible metric labels through P1-EVIDENCE.
Cached response shape remains backward-compatible.
"""
from __future__ import annotations

import logging
from typing import Optional

from django.core.cache import cache
from ninja import Router
from pydantic import BaseModel

from diabetes.services.clinical.evidence_projection import project_public_kpis
from diabetes.services.clinical.sql_analytics import AnalyticalKPIs, compute_kpis

logger = logging.getLogger(__name__)
router = Router(tags=["kpis"])

_KPI_TTL = 300


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
    gmi_confidence: Optional[str]
    gmi_basis: str
    gri: Optional[float]
    gri_zone: Optional[str]
    gri_label_fr: Optional[str]


def _kpi_cache_key(user_id: int, days: int, target_low: float, target_high: float) -> str:
    return f"kpis:u{user_id}:d{days}:l{int(target_low)}:h{int(target_high)}"


def invalidate_kpi_cache(user_id: int) -> None:
    try:
        cache.delete_pattern(f"*kpis:u{user_id}:*")
    except Exception:
        logger.debug("invalidate_kpi_cache: cache.delete_pattern unavailable (Redis down?)")


@router.get("/kpis/", response=KPIsOut)
def get_kpis(
    request,
    days: int = 21,
    target_low: float = 70.0,
    target_high: float = 180.0,
):
    """Return evidence-gated KPIs for the authenticated patient.

    Raw SQL remains descriptive source data. Normative CGM labels such as TIR,
    CV stability, GMI and GRI are returned only when the governed CGM sufficiency
    contract verifies actual coverage. The current LogEntry schema cannot prove
    wear-time/cadence, so those fields fail closed to null rather than being
    inferred from the fraction of rows labelled ``source='cgm'``.
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
    projection = project_public_kpis(kpis)
    result = {
        "avg_glucose": projection["avg_glucose"],
        "std_dev": projection["std_dev"],
        "cv_pct": projection["cv_pct"],
        "tir_pct": projection["tir_pct"],
        "tar_pct": projection["tar_pct"],
        "tbr_pct": projection["tbr_pct"],
        "gmi": projection["gmi"],
        "log_count": projection["log_count"],
        "days_with_data": projection["days_with_data"],
        "has_sufficient_data": projection["has_sufficient_data"],
        "gmi_confidence": projection["gmi_confidence"],
        "gmi_basis": projection["gmi_basis"],
        "gri": projection["gri"],
        "gri_zone": projection["gri_zone"],
        "gri_label_fr": projection["gri_label_fr"],
    }

    cache.set(cache_key, result, _KPI_TTL)
    logger.debug("KPI cache SET for user=%s key=%s ttl=%ds", request.user.id, cache_key, _KPI_TTL)
    return result
