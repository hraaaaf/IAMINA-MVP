"""Privacy-safe FRUG-8 anomaly detection and FRUG-0 cost reconciliation."""

from __future__ import annotations

import logging
import re
from collections import defaultdict
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

from .cost_ledger import BillingEvidence, reconcile_month

logger = logging.getLogger("iamina.cost")

_TOKEN_FIELDS = (
    "input_tokens",
    "output_tokens",
    "cached_input_tokens",
    "total_tokens",
)
_METERED_MODALITIES = frozenset({"ocr", "vision", "stt", "tts"})
_MEDIA_ACTIONS = frozenset({"uploaded", "retained", "deleted", "downloaded"})
_SAFE_UNIT = re.compile(r"^[a-z0-9_]{1,32}$")
_SAFE_METRIC = re.compile(r"^[a-z0-9_:]{1,96}$")


@dataclass(frozen=True, slots=True)
class UsageAnomaly:
    metric: str
    current: int
    baseline: int
    ratio: float | None


def _non_negative_int(value: Any, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{label} must be a non-negative integer")
    return value


def aggregate_usage_dimensions(
    events: Iterable[Mapping[str, Any]],
) -> dict[str, int]:
    """Aggregate only allowlisted count dimensions from privacy-safe telemetry."""
    totals: dict[str, int] = defaultdict(int)
    for event in events:
        event_type = event.get("event")
        if event_type == "llm_usage":
            status = event.get("status")
            if status not in {"success", "error"}:
                raise ValueError("llm_usage status must be success or error")
            if status != "success":
                continue
            for field in _TOKEN_FIELDS:
                value = event.get(field)
                if value is None:
                    continue
                totals[f"llm:{field}"] += _non_negative_int(value, field)
            continue

        if event_type == "metered_usage":
            status = event.get("status")
            if status not in {"success", "error"}:
                raise ValueError("metered_usage status must be success or error")
            modality = event.get("modality")
            unit = event.get("unit")
            if modality not in _METERED_MODALITIES:
                raise ValueError("unsupported metered modality")
            if not isinstance(unit, str) or _SAFE_UNIT.fullmatch(unit) is None:
                raise ValueError("metered unit must be a safe canonical label")
            quantity = _non_negative_int(event.get("quantity"), "quantity")
            if status == "success":
                totals[f"{modality}:{unit}"] += quantity
            continue

        if event_type == "media_bytes":
            action = event.get("action")
            if action not in _MEDIA_ACTIONS:
                raise ValueError("unsupported media byte action")
            totals[f"media_bytes:{action}"] += _non_negative_int(
                event.get("bytes"),
                "bytes",
            )

    return dict(sorted(totals.items()))


def detect_usage_anomalies(
    *,
    current: Mapping[str, int],
    baseline: Mapping[str, int],
    ratio_threshold: float = 2.0,
    minimum_delta: int = 1,
) -> tuple[UsageAnomaly, ...]:
    """Flag aggregate jumps without accepting arbitrary alert labels or payload."""
    if ratio_threshold < 1:
        raise ValueError("ratio_threshold must be at least 1")
    if minimum_delta <= 0:
        raise ValueError("minimum_delta must be positive")

    validated_baseline: dict[str, int] = {}
    for metric, value in baseline.items():
        if not isinstance(metric, str) or _SAFE_METRIC.fullmatch(metric) is None:
            raise ValueError("baseline metric must be a safe canonical label")
        validated_baseline[metric] = _non_negative_int(value, "baseline value")

    anomalies: list[UsageAnomaly] = []
    for metric, value in sorted(current.items()):
        if _SAFE_METRIC.fullmatch(metric) is None:
            raise ValueError("current metric must be a safe canonical label")
        current_value = _non_negative_int(value, "current value")
        baseline_value = validated_baseline.get(metric, 0)
        delta = current_value - baseline_value
        if delta < minimum_delta:
            continue
        ratio = None if baseline_value == 0 else current_value / baseline_value
        if baseline_value == 0 or ratio >= ratio_threshold:
            anomalies.append(
                UsageAnomaly(
                    metric=metric,
                    current=current_value,
                    baseline=baseline_value,
                    ratio=ratio,
                )
            )
    return tuple(anomalies)


def build_finops_audit_report(
    *,
    events: Iterable[Mapping[str, Any]],
    baseline_dimensions: Mapping[str, int],
    active_users: int,
    billed_microusd: int,
    workload_costs_microusd: dict[str, int],
    billing_evidence: BillingEvidence | None = None,
    reconciliation_floor: float = 0.95,
    anomaly_ratio_threshold: float = 2.0,
    anomaly_minimum_delta: int = 1,
) -> dict[str, Any]:
    """Build one aggregate-only usage/anomaly/reconciliation report."""
    dimensions = aggregate_usage_dimensions(events)
    anomalies = detect_usage_anomalies(
        current=dimensions,
        baseline=baseline_dimensions,
        ratio_threshold=anomaly_ratio_threshold,
        minimum_delta=anomaly_minimum_delta,
    )
    snapshot = reconcile_month(
        active_users=active_users,
        billed_microusd=billed_microusd,
        workload_costs_microusd=workload_costs_microusd,
        billing_evidence=billing_evidence,
    )
    reconciliation_ok = snapshot.meets_reconciliation_floor(reconciliation_floor)
    return {
        "usage_dimensions": dimensions,
        "anomalies": [
            {
                "metric": item.metric,
                "current": item.current,
                "baseline": item.baseline,
                "ratio": item.ratio,
            }
            for item in anomalies
        ],
        "reconciliation": {
            "billed_microusd": snapshot.billed_microusd,
            "explained_microusd": snapshot.explained_microusd,
            "unexplained_microusd": snapshot.unexplained_microusd,
            "ratio": snapshot.reconciliation_ratio,
            "billed_microusd_per_mau": snapshot.billed_microusd_per_mau,
            "floor": reconciliation_floor,
            "meets_floor": reconciliation_ok,
        },
    }


def emit_usage_anomaly_alerts(anomalies: Iterable[UsageAnomaly]) -> None:
    """Emit aggregate usage anomalies before provider billing is available."""
    for item in anomalies:
        if not isinstance(item, UsageAnomaly):
            raise ValueError("invalid usage anomaly")
        if _SAFE_METRIC.fullmatch(item.metric) is None:
            raise ValueError("invalid anomaly metric")
        logger.warning(
            "runtime_finops usage_anomaly metric=%s current=%d baseline=%d",
            item.metric,
            _non_negative_int(item.current, "current"),
            _non_negative_int(item.baseline, "baseline"),
        )


def emit_finops_audit_alerts(report: Mapping[str, Any]) -> None:
    """Emit aggregate-only alerts from a validated audit report."""
    anomalies = report.get("anomalies")
    reconciliation = report.get("reconciliation")
    if not isinstance(anomalies, list) or not isinstance(reconciliation, dict):
        raise ValueError("invalid FinOps audit report")

    usage_anomalies: list[UsageAnomaly] = []
    for item in anomalies:
        if not isinstance(item, dict):
            raise ValueError("invalid anomaly report item")
        metric = item.get("metric")
        ratio = item.get("ratio")
        if not isinstance(metric, str) or _SAFE_METRIC.fullmatch(metric) is None:
            raise ValueError("invalid anomaly metric")
        if ratio is not None and not isinstance(ratio, (int, float)):
            raise ValueError("invalid anomaly ratio")
        usage_anomalies.append(
            UsageAnomaly(
                metric=metric,
                current=_non_negative_int(item.get("current"), "current"),
                baseline=_non_negative_int(item.get("baseline"), "baseline"),
                ratio=None if ratio is None else float(ratio),
            )
        )
    emit_usage_anomaly_alerts(usage_anomalies)

    if reconciliation.get("meets_floor") is False:
        logger.warning(
            "runtime_finops reconciliation_gap billed_microusd=%d "
            "explained_microusd=%d unexplained_microusd=%d",
            _non_negative_int(reconciliation.get("billed_microusd"), "billed"),
            _non_negative_int(reconciliation.get("explained_microusd"), "explained"),
            _non_negative_int(reconciliation.get("unexplained_microusd"), "unexplained"),
        )
