"""Patient-scoped lifecycle helpers for transient document extraction cache."""
from __future__ import annotations

from django.core.cache import cache
from django_redis import get_redis_connection

_PENDING_PREFIX = "pulper:pending"


def pending_extraction_pattern(patient_id: int) -> str:
    """Return the logical cache-key pattern for one patient's pending batches."""
    if not isinstance(patient_id, int) or patient_id <= 0:
        raise ValueError("patient_id must be a positive integer")
    return f"{_PENDING_PREFIX}:{patient_id}:*"


def purge_patient_pending_extractions(patient_id: int) -> int:
    """Delete all pending extraction batches for one patient, fail-closed on Redis errors."""
    logical_pattern = pending_extraction_pattern(patient_id)
    redis = get_redis_connection("default")
    physical_pattern = cache.make_key(logical_pattern)
    keys = list(redis.scan_iter(match=physical_pattern, count=100))
    if not keys:
        return 0
    return int(redis.delete(*keys))
