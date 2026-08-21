"""Deterministic aggregation for privacy-safe patient-media usage telemetry.

Only observed byte lifecycle events are aggregated. Upload bytes are never
relabelled as retained storage, and monetary cost is never inferred without
explicit pricing/billing inputs.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from typing import Any

_MEDIA_ACTIONS = ("uploaded", "retained", "deleted", "downloaded")


def aggregate_media_usage(
    events: Iterable[Mapping[str, Any]],
    *,
    active_users: int | None = None,
) -> dict[str, Any]:
    """Aggregate observed media lifecycle bytes without inventing storage state."""
    if active_users is not None and (
        isinstance(active_users, bool)
        or not isinstance(active_users, int)
        or active_users <= 0
    ):
        raise ValueError("active_users must be a positive integer when supplied")

    action_counts = Counter({action: 0 for action in _MEDIA_ACTIONS})
    bytes_by_action = Counter({action: 0 for action in _MEDIA_ACTIONS})
    bytes_by_retention_class: Counter[str] = Counter()

    media_events = 0
    for event in events:
        if event.get("event") != "media_bytes":
            continue

        action = event.get("action")
        if action not in _MEDIA_ACTIONS:
            raise ValueError(f"unsupported media action in telemetry: {action}")

        byte_count = event.get("bytes")
        if (
            isinstance(byte_count, bool)
            or not isinstance(byte_count, int)
            or byte_count < 0
        ):
            raise ValueError("media_bytes event requires non-negative integer bytes")

        retention_class = event.get("retention_class")
        if not isinstance(retention_class, str) or not retention_class.strip():
            raise ValueError("media_bytes event requires retention_class")

        media_events += 1
        action_counts[action] += 1
        bytes_by_action[action] += byte_count
        bytes_by_retention_class[retention_class] += byte_count

    uploaded_bytes_per_mau = _per_mau(bytes_by_action["uploaded"], active_users)
    downloaded_bytes_per_mau = _per_mau(bytes_by_action["downloaded"], active_users)

    return {
        "media_events": media_events,
        "action_counts": dict(action_counts),
        "bytes_by_action": dict(bytes_by_action),
        "bytes_by_retention_class": dict(sorted(bytes_by_retention_class.items())),
        "uploaded_bytes_per_mau": uploaded_bytes_per_mau,
        "downloaded_bytes_per_mau": downloaded_bytes_per_mau,
        "storage_occupancy_bytes": None,
        "storage_occupancy_status": (
            "unavailable_without_time_weighted_retained_object_inventory"
        ),
        "storage_cost_per_mau": None,
        "egress_cost_per_mau": None,
        "cost_status": "unavailable_without_storage_and_egress_pricing",
    }


def _per_mau(byte_count: int, active_users: int | None) -> float | None:
    if active_users is None:
        return None
    return byte_count / active_users
