"""Validated persistence for privacy-safe cost telemetry."""

from __future__ import annotations

import logging
import re
from collections.abc import Mapping
from datetime import datetime
from typing import Any

from core.finops_events import FinOpsTelemetryEvent

logger = logging.getLogger(__name__)

_SAFE_LABEL = re.compile(r"^[A-Za-z0-9_./:-]{1,160}$")
_EVENT_FIELDS = {
    "companion_route": frozenset({"event", "route"}),
    "ocr_route": frozenset({"event", "modality", "script", "bounded_capture", "lane"}),
    "llm_usage": frozenset(
        {
            "event",
            "status",
            "workload",
            "provider_route",
            "from_cache",
            "prompt_chars",
            "response_chars",
            "latency_ms",
            "input_tokens",
            "output_tokens",
            "cached_input_tokens",
            "total_tokens",
            "error_type",
        }
    ),
    "metered_usage": frozenset(
        {
            "event",
            "status",
            "workload",
            "modality",
            "unit",
            "quantity",
            "provider_route",
            "latency_ms",
            "error_type",
        }
    ),
    "media_bytes": frozenset(
        {"event", "action", "workload", "bytes", "retention_class"}
    ),
}


def _validate_scalar(value: object) -> None:
    if value is None or isinstance(value, (bool, int, float)):
        return
    if isinstance(value, str) and _SAFE_LABEL.fullmatch(value) is not None:
        return
    raise ValueError("FinOps telemetry accepts only bounded canonical scalar values")


def validate_cost_event(event: Mapping[str, Any]) -> dict[str, Any]:
    event_type = event.get("event")
    if not isinstance(event_type, str) or event_type not in _EVENT_FIELDS:
        raise ValueError("unsupported FinOps telemetry event")
    if set(event) - _EVENT_FIELDS[event_type]:
        raise ValueError("FinOps telemetry contains non-allowlisted fields")
    normalized = dict(event)
    for value in normalized.values():
        _validate_scalar(value)
    return normalized


def persist_cost_event(event: Mapping[str, Any]) -> bool:
    """Persist one anonymous event; telemetry failure never interrupts product flow."""
    try:
        normalized = validate_cost_event(event)
        FinOpsTelemetryEvent.objects.create(
            event_type=str(normalized["event"]),
            payload=normalized,
        )
    except Exception as exc:
        logger.warning("FinOps telemetry persistence failed: %s", type(exc).__name__)
        return False
    return True


def load_cost_events(*, start: datetime, end: datetime) -> list[dict[str, Any]]:
    """Return persisted events for one half-open reporting window [start, end)."""
    if start.tzinfo is None or end.tzinfo is None:
        raise ValueError("FinOps reporting bounds must be timezone-aware")
    if start >= end:
        raise ValueError("FinOps reporting start must be before end")
    rows = FinOpsTelemetryEvent.objects.filter(
        timestamp__gte=start,
        timestamp__lt=end,
    ).order_by("timestamp", "id")
    return [dict(payload) for payload in rows.values_list("payload", flat=True)]
