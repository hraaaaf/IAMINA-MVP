"""Atomic global/provider/workload FinOps policy over the shared budget ledger."""

from __future__ import annotations

import hashlib
import hmac
import re
from dataclasses import dataclass
from typing import Mapping

from .budget import (
    BudgetConfigurationError,
    BudgetExceeded,
    BudgetLedger,
    BudgetReservationBundle,
    BudgetScopeLimit,
)

_IDENTIFIER_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]{0,63}$")
_MONTH_RE = re.compile(r"^\d{4}-(?:0[1-9]|1[0-2])$")
_OPAQUE_KEY_RE = re.compile(r"^hmac256:[0-9a-f]{64}$")


@dataclass(frozen=True, slots=True)
class BudgetThreshold:
    hard_limit_microusd: int
    soft_alert_threshold_microusd: int

    def validate(self) -> None:
        if self.hard_limit_microusd <= 0:
            raise BudgetConfigurationError("hard budget limit must be positive")
        if self.soft_alert_threshold_microusd <= 0:
            raise BudgetConfigurationError("soft budget threshold must be positive")
        if self.soft_alert_threshold_microusd > self.hard_limit_microusd:
            raise BudgetConfigurationError("soft budget threshold cannot exceed hard limit")


@dataclass(frozen=True, slots=True)
class HierarchicalBudgetPolicy:
    """Explicit fail-closed monthly ceilings; no provider/workload defaults."""

    global_budget: BudgetThreshold
    provider_budgets: Mapping[str, BudgetThreshold]
    workload_budgets: Mapping[tuple[str, str], BudgetThreshold]
    max_single_reservation_microusd: int

    def validate(self) -> None:
        self.global_budget.validate()
        if self.max_single_reservation_microusd <= 0:
            raise BudgetConfigurationError("single reservation ceiling must be positive")
        if self.max_single_reservation_microusd > self.global_budget.hard_limit_microusd:
            raise BudgetConfigurationError(
                "single reservation ceiling cannot exceed global hard limit"
            )
        if not self.provider_budgets or not self.workload_budgets:
            raise BudgetConfigurationError(
                "provider and workload budgets must be explicitly configured"
            )
        for provider, threshold in self.provider_budgets.items():
            _validate_identifier(provider, "provider")
            threshold.validate()
        for key, threshold in self.workload_budgets.items():
            provider, workload = key
            _validate_identifier(provider, "provider")
            _validate_identifier(workload, "workload")
            if provider not in self.provider_budgets:
                raise BudgetConfigurationError(
                    f"workload budget references unconfigured provider {provider}"
                )
            threshold.validate()

    def scopes_for(self, *, provider: str, workload: str) -> tuple[BudgetScopeLimit, ...]:
        _validate_identifier(provider, "provider")
        _validate_identifier(workload, "workload")
        provider_budget = self.provider_budgets.get(provider)
        workload_budget = self.workload_budgets.get((provider, workload))
        if provider_budget is None or workload_budget is None:
            raise BudgetConfigurationError(
                "provider/workload budget is not explicitly configured"
            )
        return (
            _scope("finops:global", self.global_budget),
            _scope(f"finops:provider:{provider}", provider_budget),
            _scope(f"finops:workload:{provider}:{workload}", workload_budget),
        )


def _scope(subject_key: str, threshold: BudgetThreshold) -> BudgetScopeLimit:
    return BudgetScopeLimit(
        subject_key=subject_key,
        monthly_limit_microusd=threshold.hard_limit_microusd,
        soft_alert_threshold_microusd=threshold.soft_alert_threshold_microusd,
    )


def _validate_identifier(value: str, label: str) -> None:
    if not _IDENTIFIER_RE.fullmatch(value):
        raise BudgetConfigurationError(f"invalid {label} budget identifier")


def derive_opaque_budget_operation_key(
    *, key_material: bytes, operation_reference: str
) -> str:
    """Derive a non-PHI persisted idempotency key from an internal reference."""
    if len(key_material) < 32:
        raise BudgetConfigurationError("budget key material must be at least 32 bytes")
    if not operation_reference:
        raise BudgetConfigurationError("operation reference is required")
    digest = hmac.new(
        key_material,
        operation_reference.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return f"hmac256:{digest}"


class HierarchicalBudgetController:
    """Reserve one paid operation atomically across global/provider/workload scopes."""

    def __init__(self, *, policy: HierarchicalBudgetPolicy, ledger: BudgetLedger) -> None:
        policy.validate()
        self.policy = policy
        self.ledger = ledger

    def authorize(
        self,
        *,
        provider: str,
        workload: str,
        month_key: str,
        reserved_microusd: int,
        idempotency_key: str,
    ) -> BudgetReservationBundle:
        if not _MONTH_RE.fullmatch(month_key):
            raise BudgetConfigurationError("month_key must use canonical YYYY-MM format")
        if reserved_microusd <= 0:
            raise BudgetConfigurationError("reserved_microusd must be positive")
        if reserved_microusd > self.policy.max_single_reservation_microusd:
            raise BudgetExceeded("AI call reservation exceeds the single-call ceiling")
        if not _OPAQUE_KEY_RE.fullmatch(idempotency_key):
            raise BudgetConfigurationError(
                "runtime budget idempotency key must be an opaque HMAC-SHA256 key"
            )
        return self.ledger.reserve_bundle_if_within(
            scopes=self.policy.scopes_for(provider=provider, workload=workload),
            month_key=month_key,
            amount_microusd=reserved_microusd,
            idempotency_key=idempotency_key,
        )

    def settle(self, bundle: BudgetReservationBundle, actual_microusd: int) -> None:
        self.ledger.settle_bundle(bundle, actual_microusd)

    def cancel(self, bundle: BudgetReservationBundle) -> None:
        self.ledger.cancel_bundle(bundle)
