"""
Health check endpoint — used by docker-compose / load balancers.

GET /api/v1/health
Returns 200 when the service is operational.
Returns 503 when a critical dependency (DB) is unreachable.

Response:
  {
    "status": "ok" | "degraded",
    "db":    "ok" | "error",
    "cache": "ok" | "unavailable"
  }
"""
from __future__ import annotations

import logging

from django.core.cache import cache
from django.db import OperationalError, connection
from ninja import Router, Schema

logger = logging.getLogger(__name__)

router = Router()


class HealthSchema(Schema):
    status: str
    db: str
    cache: str


@router.get("/health", auth=None, tags=["ops"], response={200: HealthSchema, 503: HealthSchema})
def health_check(request):
    """
    Liveness + readiness probe.

    - DB unreachable → 503 (blocks gunicorn from receiving traffic)
    - Cache unavailable → 200 degraded (non-fatal: falls back to DB)
    """
    db_status   = _check_db()
    cache_status = _check_cache()

    overall = "ok" if db_status == "ok" else "degraded"
    status_code = 200 if db_status == "ok" else 503

    return status_code, {
        "status": overall,
        "db":     db_status,
        "cache":  cache_status,
    }


# ── private ──────────────────────────────────────────────────────────────────

def _check_db() -> str:
    try:
        connection.ensure_connection()
        return "ok"
    except OperationalError as exc:
        logger.error("Health: DB unreachable — %s", exc)
        return "error"


def _check_cache() -> str:
    try:
        cache.set("__health_probe__", "1", timeout=5)
        return "ok" if cache.get("__health_probe__") == "1" else "unavailable"
    except Exception as exc:
        logger.warning("Health: Cache unavailable — %s", exc)
        return "unavailable"
