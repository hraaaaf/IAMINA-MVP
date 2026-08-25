"""Privacy-safe route telemetry for companion turns."""

from __future__ import annotations

import json
import logging

from llm.cost_event_store import persist_cost_event

logger = logging.getLogger("iamina.cost")
_ALLOWED_ROUTES = frozenset({"safety", "zero_model", "llm"})


def record_companion_route(route: str) -> None:
    """Record one content-free routing decision for call-rate reconciliation."""
    if route not in _ALLOWED_ROUTES:
        raise ValueError(f"unsupported companion route: {route}")
    event = {"event": "companion_route", "route": route}
    logger.info(
        "cost_telemetry %s",
        json.dumps(event, sort_keys=True, separators=(",", ":")),
    )
    persist_cost_event(event)
