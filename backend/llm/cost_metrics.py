"""Deterministic aggregation for privacy-safe FRUG-5 cost telemetry.

This module reports only observed routing and provider-reported usage. Missing
provider token usage remains missing; character counts are never converted into
estimated tokens or cost.
"""

from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping
from typing import Any

_COST_PREFIX = "cost_telemetry "
_ROUTES = ("safety", "zero_model", "llm")
_TOKEN_FIELDS = (
    "input_tokens",
    "output_tokens",
    "cached_input_tokens",
    "total_tokens",
)
_DISTRIBUTION_FIELDS = ("prompt_chars", *_TOKEN_FIELDS)


def parse_cost_telemetry_lines(lines: Iterable[str]) -> list[dict[str, Any]]:
    """Extract JSON cost events from arbitrary log lines.

    Non-cost log lines are ignored. Malformed cost telemetry fails closed so a
    report cannot silently turn corrupted telemetry into reassuring metrics.
    """
    events: list[dict[str, Any]] = []
    for line in lines:
        marker = line.find(_COST_PREFIX)
        if marker < 0:
            continue
        payload = line[marker + len(_COST_PREFIX) :].strip()
        try:
            event = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise ValueError("malformed cost telemetry JSON") from exc
        if not isinstance(event, dict):
            raise ValueError("cost telemetry payload must be a JSON object")
        events.append(event)
    return events


def aggregate_cost_events(events: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Aggregate companion route and LLM usage events without guessed precision."""
    route_counts = Counter({route: 0 for route in _ROUTES})
    llm_successes: list[Mapping[str, Any]] = []
    llm_errors = 0

    for event in events:
        event_type = event.get("event")
        if event_type == "companion_route":
            route = event.get("route")
            if route not in _ROUTES:
                raise ValueError(f"unsupported companion route in telemetry: {route}")
            route_counts[route] += 1
            continue
        if event_type != "llm_usage":
            continue

        status = event.get("status")
        if status == "success":
            llm_successes.append(event)
        elif status == "error":
            llm_errors += 1
        else:
            raise ValueError(f"unsupported llm_usage status: {status}")

    interactions = sum(route_counts.values())
    route_rates = {
        route: (route_counts[route] / interactions if interactions else None)
        for route in _ROUTES
    }

    by_workload: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for event in llm_successes:
        workload = event.get("workload")
        if not isinstance(workload, str) or not workload.strip():
            raise ValueError("successful llm_usage event requires workload")
        by_workload[workload].append(event)

    return {
        "interactions": interactions,
        "route_counts": dict(route_counts),
        "route_rates": route_rates,
        "llm_call_rate_per_interaction": route_rates["llm"],
        "zero_model_rate_per_interaction": route_rates["zero_model"],
        "safety_rate_per_interaction": route_rates["safety"],
        "llm_success_events": len(llm_successes),
        "llm_error_events": llm_errors,
        "overall": _summarize_usage_group(llm_successes),
        "by_workload": {
            workload: _summarize_usage_group(group)
            for workload, group in sorted(by_workload.items())
        },
        "cost_status": "unavailable_without_reconciled_billing_and_stable_pricing",
    }


def _summarize_usage_group(events: list[Mapping[str, Any]]) -> dict[str, Any]:
    request_count = len(events)
    distributions = {
        field: _distribution(events, field)
        for field in _DISTRIBUTION_FIELDS
    }

    paired_cache_samples: list[tuple[int, int]] = []
    for event in events:
        input_tokens = _non_negative_int(event.get("input_tokens"))
        cached_tokens = _non_negative_int(event.get("cached_input_tokens"))
        if input_tokens is not None and cached_tokens is not None:
            paired_cache_samples.append((input_tokens, cached_tokens))

    total_input = sum(item[0] for item in paired_cache_samples)
    total_cached = sum(item[1] for item in paired_cache_samples)
    cached_ratio = total_cached / total_input if total_input > 0 else None

    cache_flags = [event.get("from_cache") for event in events]
    valid_cache_flags = [flag for flag in cache_flags if isinstance(flag, bool)]
    from_cache_rate = (
        sum(1 for flag in valid_cache_flags if flag) / len(valid_cache_flags)
        if valid_cache_flags
        else None
    )

    providers = Counter(
        str(event["provider_route"])
        for event in events
        if isinstance(event.get("provider_route"), str)
        and str(event["provider_route"]).strip()
    )

    return {
        "requests": request_count,
        "distributions": distributions,
        "provider_routes": dict(sorted(providers.items())),
        "cached_input_token_ratio": cached_ratio,
        "cache_ratio_sample_count": len(paired_cache_samples),
        "from_cache_rate": from_cache_rate,
    }


def _distribution(
    events: list[Mapping[str, Any]],
    field: str,
) -> dict[str, int | float | None]:
    values: list[int] = []
    for event in events:
        value = _non_negative_int(event.get(field))
        if value is not None:
            values.append(value)

    eligible = len(events)
    samples = len(values)
    return {
        "samples": samples,
        "coverage": samples / eligible if eligible else None,
        "p50": _nearest_rank(values, 0.50),
        "p95": _nearest_rank(values, 0.95),
    }


def _nearest_rank(values: list[int], percentile: float) -> int | None:
    if not values:
        return None
    ordered = sorted(values)
    rank = max(1, math.ceil(percentile * len(ordered)))
    return ordered[rank - 1]


def _non_negative_int(value: Any) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        return None
    return value
