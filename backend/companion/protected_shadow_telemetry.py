"""Content-free telemetry for protected narration provider shadow."""
from __future__ import annotations

import json
import logging

from llm.cost_event_store import persist_cost_event

logger = logging.getLogger("iamina.cost")

_ALLOWED_STATUSES = frozenset(
    {"disabled", "blocked", "accepted", "rejected", "error"}
)
_ALLOWED_PROVIDERS = frozenset({"groq"})
_ALLOWED_FAMILIES = frozenset({"clinician_prep"})


def record_protected_narration_shadow(
    *,
    status: str,
    provider: str = "groq",
    family: str = "clinician_prep",
) -> None:
    if status not in _ALLOWED_STATUSES:
        raise ValueError("unsupported protected shadow status")
    if provider not in _ALLOWED_PROVIDERS:
        raise ValueError("unsupported protected shadow provider")
    if family not in _ALLOWED_FAMILIES:
        raise ValueError("unsupported protected shadow family")

    event = {
        "event": "protected_narration_shadow",
        "status": status,
        "provider": provider,
        "family": family,
    }
    logger.info(
        "cost_telemetry %s",
        json.dumps(event, sort_keys=True, separators=(",", ":")),
    )
    persist_cost_event(event)


__all__ = ["record_protected_narration_shadow"]
