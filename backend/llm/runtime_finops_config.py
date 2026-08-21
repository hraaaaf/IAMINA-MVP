"""Strict external configuration loader for paid text runtime FinOps.

No provider prices, budget amounts, throttle ceilings or retry values are defined
here. Any approved external provider must have complete runtime configuration
before network egress.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from datetime import date
from typing import Any

from .hierarchical_budget import (
    BudgetThreshold,
    HierarchicalBudgetController,
    HierarchicalBudgetPolicy,
)
from .persistent_budget import PersistentBudgetLedger
from .pricing import PricingRegistry, TextTokenPrice
from .provider_guard import PersistentProviderFailureGuard, ProviderFailurePolicy
from .runtime_finops import PaidTextRuntimeEnforcer, RuntimeFinOpsConfigurationError
from .user_abuse_throttle import (
    PersistentUserAbuseThrottle,
    UserAbuseThrottlePolicy,
)

_CONFIG_ENV = "AI_FINOPS_RUNTIME_CONFIG_JSON"
_HMAC_ENV = "AI_FINOPS_HMAC_KEY"
_ALLOWED_TOP_LEVEL = frozenset(
    {
        "global_budget",
        "provider_budgets",
        "workload_budgets",
        "prices",
        "call_limits",
        "provider_failure_policies",
        "user_throttle",
        "max_single_reservation_microusd",
    }
)


@dataclass(frozen=True, slots=True)
class RuntimeTextBinding:
    enforcer: PaidTextRuntimeEnforcer
    user_throttle: PersistentUserAbuseThrottle
    max_input_tokens: int
    max_output_tokens: int


logger = logging.getLogger("iamina.cost")


class _AlertingBudgetController(HierarchicalBudgetController):
    """Emit privacy-safe soft-threshold signals while preserving hard-stop semantics."""

    def authorize(
        self,
        *,
        provider: str,
        workload: str,
        month_key: str,
        reserved_microusd: int,
        idempotency_key: str,
    ):
        bundle = super().authorize(
            provider=provider,
            workload=workload,
            month_key=month_key,
            reserved_microusd=reserved_microusd,
            idempotency_key=idempotency_key,
        )
        if bundle.soft_alert_subject_keys:
            logger.warning(
                "runtime_finops soft_budget_alert provider=%s workload=%s scopes=%s",
                provider,
                workload,
                ",".join(bundle.soft_alert_subject_keys),
            )
        return bundle


def _mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise RuntimeFinOpsConfigurationError(f"{label} must be an object")
    return value


def _list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise RuntimeFinOpsConfigurationError(f"{label} must be a list")
    return value


def _str(item: dict[str, Any], key: str) -> str:
    value = item.get(key)
    if not isinstance(value, str) or not value.strip():
        raise RuntimeFinOpsConfigurationError(f"{key} must be a non-empty string")
    return value.strip()


def _int(item: dict[str, Any], key: str, *, allow_zero: bool = False) -> int:
    value = item.get(key)
    if not isinstance(value, int) or isinstance(value, bool):
        raise RuntimeFinOpsConfigurationError(f"{key} must be an integer")
    if value < 0 or (value == 0 and not allow_zero):
        raise RuntimeFinOpsConfigurationError(f"{key} must be positive")
    return value


def _optional_int(item: dict[str, Any], key: str) -> int | None:
    value = item.get(key)
    if value is None:
        return None
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise RuntimeFinOpsConfigurationError(
            f"{key} must be null or a non-negative integer"
        )
    return value


def _date(item: dict[str, Any], key: str) -> date:
    raw = _str(item, key)
    try:
        return date.fromisoformat(raw)
    except ValueError as exc:
        raise RuntimeFinOpsConfigurationError(
            f"{key} must use canonical YYYY-MM-DD"
        ) from exc


def _threshold(value: Any, label: str) -> BudgetThreshold:
    item = _mapping(value, label)
    return BudgetThreshold(
        hard_limit_microusd=_int(item, "hard_limit_microusd"),
        soft_alert_threshold_microusd=_int(
            item, "soft_alert_threshold_microusd"
        ),
    )


def _load_config() -> tuple[dict[str, Any], bytes]:
    raw = os.environ.get(_CONFIG_ENV, "").strip()
    key_raw = os.environ.get(_HMAC_ENV, "")
    if not raw:
        raise RuntimeFinOpsConfigurationError(
            f"{_CONFIG_ENV} is required for external paid AI"
        )
    if len(key_raw.encode("utf-8")) < 32:
        raise RuntimeFinOpsConfigurationError(
            f"{_HMAC_ENV} must contain at least 32 bytes"
        )
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeFinOpsConfigurationError(
            f"{_CONFIG_ENV} must contain valid JSON"
        ) from exc
    config = _mapping(parsed, _CONFIG_ENV)
    unknown = set(config) - _ALLOWED_TOP_LEVEL
    missing = _ALLOWED_TOP_LEVEL - set(config)
    if unknown or missing:
        raise RuntimeFinOpsConfigurationError(
            "runtime FinOps config keys are incomplete or unknown"
        )
    return config, key_raw.encode("utf-8")


def _unique_match(
    values: list[Any],
    *,
    label: str,
    predicate,
) -> dict[str, Any]:
    items = [_mapping(value, label) for value in values]
    matches = [item for item in items if predicate(item)]
    if len(matches) != 1:
        raise RuntimeFinOpsConfigurationError(
            f"exactly one {label} entry is required"
        )
    return matches[0]


def load_runtime_text_binding(
    *,
    provider: str,
    model: str,
    workload: str,
) -> RuntimeTextBinding:
    """Build one fail-closed persistent runtime binding for an exact paid route."""
    config, key_material = _load_config()

    global_budget = _threshold(config["global_budget"], "global_budget")

    provider_budgets: dict[str, BudgetThreshold] = {}
    for raw_item in _list(config["provider_budgets"], "provider_budgets"):
        item = _mapping(raw_item, "provider_budget")
        item_provider = _str(item, "provider")
        if item_provider in provider_budgets:
            raise RuntimeFinOpsConfigurationError("duplicate provider budget")
        provider_budgets[item_provider] = _threshold(item, "provider_budget")

    workload_budgets: dict[tuple[str, str], BudgetThreshold] = {}
    for raw_item in _list(config["workload_budgets"], "workload_budgets"):
        item = _mapping(raw_item, "workload_budget")
        key = (_str(item, "provider"), _str(item, "workload"))
        if key in workload_budgets:
            raise RuntimeFinOpsConfigurationError("duplicate workload budget")
        workload_budgets[key] = _threshold(item, "workload_budget")

    call_limit = _unique_match(
        _list(config["call_limits"], "call_limits"),
        label="call_limit",
        predicate=lambda item: (
            item.get("provider") == provider
            and item.get("model") == model
            and item.get("workload") == workload
        ),
    )
    max_input_tokens = _int(call_limit, "max_input_tokens")
    max_output_tokens = _int(call_limit, "max_output_tokens")

    failure = _unique_match(
        _list(config["provider_failure_policies"], "provider_failure_policies"),
        label="provider_failure_policy",
        predicate=lambda item: item.get("provider") == provider,
    )
    failure_policy = ProviderFailurePolicy(
        max_attempts_per_operation=_int(failure, "max_attempts_per_operation"),
        failure_threshold=_int(failure, "failure_threshold"),
        circuit_cooldown_seconds=_int(failure, "circuit_cooldown_seconds"),
        in_flight_lease_seconds=_int(failure, "in_flight_lease_seconds"),
    )

    throttle = _mapping(config["user_throttle"], "user_throttle")
    throttle_policy = UserAbuseThrottlePolicy(
        window_seconds=_int(throttle, "window_seconds"),
        max_requests=_int(throttle, "max_requests"),
    )

    prices: list[TextTokenPrice] = []
    for raw_item in _list(config["prices"], "prices"):
        item = _mapping(raw_item, "price")
        prices.append(
            TextTokenPrice(
                provider=_str(item, "provider"),
                model=_str(item, "model"),
                currency=_str(item, "currency"),
                input_microusd_per_million=_int(
                    item, "input_microusd_per_million", allow_zero=True
                ),
                cached_input_microusd_per_million=_optional_int(
                    item, "cached_input_microusd_per_million"
                ),
                output_microusd_per_million=_int(
                    item, "output_microusd_per_million", allow_zero=True
                ),
                evidence_reference=_str(item, "evidence_reference"),
                verified_on=_date(item, "verified_on"),
                review_due_on=_date(item, "review_due_on"),
            )
        )

    policy = HierarchicalBudgetPolicy(
        global_budget=global_budget,
        provider_budgets=provider_budgets,
        workload_budgets=workload_budgets,
        max_single_reservation_microusd=_int(
            config, "max_single_reservation_microusd"
        ),
    )
    controller = _AlertingBudgetController(
        policy=policy,
        ledger=PersistentBudgetLedger(),
    )
    pricing = PricingRegistry(tuple(prices))

    return RuntimeTextBinding(
        enforcer=PaidTextRuntimeEnforcer(
            budget=controller,
            pricing=pricing,
            provider_guard=PersistentProviderFailureGuard(failure_policy),
            operation_key_material=key_material,
        ),
        user_throttle=PersistentUserAbuseThrottle(
            policy=throttle_policy,
            key_material=key_material,
        ),
        max_input_tokens=max_input_tokens,
        max_output_tokens=max_output_tokens,
    )
