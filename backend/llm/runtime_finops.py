"""Persistent runtime FinOps guard for one paid text provider completion.

This module contains no provider prices and no production budget values. Callers
must inject a current controlled pricing registry, explicit hierarchical budget
policy, persistent ledger, provider failure guard and opaque-key material.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import datetime
from typing import TypeVar

from django.db import transaction
from django.utils import timezone

from core.models import AIProviderCircuitState, AIProviderOperationAttempt

from .base import LLMResponse
from .budget import BudgetReservationBundle
from .errors import normalize_provider_exception
from .hierarchical_budget import (
    HierarchicalBudgetController,
    derive_opaque_budget_operation_key,
)
from .pricing import PricingRegistry, TextTokenPrice
from .provider_guard import (
    PersistentProviderFailureGuard,
    ProviderAttemptPermit,
    ProviderStaleAttempt,
)

logger = logging.getLogger("iamina.cost")
_T = TypeVar("_T", bound=LLMResponse)
_MICRO_PER_MILLION = 1_000_000


class RuntimeFinOpsConfigurationError(RuntimeError):
    """Raised when a paid call cannot be bounded by controlled FinOps inputs."""


def _ceil_cost(token_count: int, rate_microusd_per_million: int) -> int:
    if token_count < 0 or rate_microusd_per_million < 0:
        raise RuntimeFinOpsConfigurationError("token counts and rates cannot be negative")
    return (
        token_count * rate_microusd_per_million + _MICRO_PER_MILLION - 1
    ) // _MICRO_PER_MILLION


def _worst_case_cost(
    price: TextTokenPrice,
    *,
    max_input_tokens: int,
    max_output_tokens: int,
) -> int:
    if max_input_tokens <= 0 or max_output_tokens <= 0:
        raise RuntimeFinOpsConfigurationError(
            "paid text runtime requires positive controlled token ceilings"
        )
    cached_rate = price.cached_input_microusd_per_million
    conservative_input_rate = max(
        price.input_microusd_per_million,
        cached_rate if cached_rate is not None else price.input_microusd_per_million,
    )
    return _ceil_cost(max_input_tokens, conservative_input_rate) + _ceil_cost(
        max_output_tokens,
        price.output_microusd_per_million,
    )


def _provider_reported_actual_cost(
    price: TextTokenPrice,
    response: LLMResponse,
) -> int | None:
    """Return conservative actual cost only when provider token usage is complete."""
    usage = response.usage
    if usage is None or usage.input_tokens is None or usage.output_tokens is None:
        return None
    if usage.input_tokens < 0 or usage.output_tokens < 0:
        return None

    cached_tokens = usage.cached_input_tokens or 0
    if cached_tokens < 0 or cached_tokens > usage.input_tokens:
        return None

    cached_rate = price.cached_input_microusd_per_million
    effective_cached_rate = (
        cached_rate
        if cached_rate is not None
        else price.input_microusd_per_million
    )
    uncached_tokens = usage.input_tokens - cached_tokens
    input_numerator = (
        uncached_tokens * price.input_microusd_per_million
        + cached_tokens * effective_cached_rate
    )
    input_cost = (input_numerator + _MICRO_PER_MILLION - 1) // _MICRO_PER_MILLION
    output_cost = _ceil_cost(
        usage.output_tokens,
        price.output_microusd_per_million,
    )
    return input_cost + output_cost


def _abort_pre_provider_attempt(
    permit: ProviderAttemptPermit,
) -> None:
    """Roll back an attempt that was denied before any provider/network call.

    The persistent attempt row remains as audit-safe state, but the attempt is not
    counted against the provider retry ceiling because no provider execution took
    place. A half-open probe lease is released as part of the same transaction.
    """
    with transaction.atomic():
        try:
            circuit = AIProviderCircuitState.objects.select_for_update().get(
                provider=permit.provider
            )
            operation = AIProviderOperationAttempt.objects.select_for_update().get(
                provider=permit.provider,
                operation_key=permit.operation_key,
            )
        except (
            AIProviderCircuitState.DoesNotExist,
            AIProviderOperationAttempt.DoesNotExist,
        ) as exc:
            raise ProviderStaleAttempt(
                "provider preflight abort belongs to unknown state"
            ) from exc

        if operation.completed_at is not None:
            raise ProviderStaleAttempt(
                "provider preflight abort arrived after completion"
            )
        if operation.active_attempt_number != permit.attempt_number:
            raise ProviderStaleAttempt(
                "provider preflight abort belongs to a stale attempt"
            )
        if operation.attempt_count != permit.attempt_number:
            raise ProviderStaleAttempt(
                "provider preflight abort cannot rewind a newer attempt"
            )

        operation.attempt_count -= 1
        operation.active_attempt_number = None
        operation.in_flight_until = None
        operation.save(
            update_fields=(
                "attempt_count",
                "active_attempt_number",
                "in_flight_until",
                "updated_at",
            )
        )
        if permit.half_open_probe:
            circuit.probe_in_flight_until = None
            circuit.save(update_fields=("probe_in_flight_until", "updated_at"))


class PaidTextRuntimeEnforcer:
    """Execute exactly one bounded paid text completion with durable guardrails."""

    def __init__(
        self,
        *,
        budget: HierarchicalBudgetController,
        pricing: PricingRegistry,
        provider_guard: PersistentProviderFailureGuard,
        operation_key_material: bytes,
    ) -> None:
        if len(operation_key_material) < 32:
            raise RuntimeFinOpsConfigurationError(
                "runtime operation key material must be at least 32 bytes"
            )
        self._budget = budget
        self._pricing = pricing
        self._provider_guard = provider_guard
        self._operation_key_material = operation_key_material

    def execute_complete(
        self,
        *,
        provider: str,
        model: str,
        workload: str,
        operation_reference: str,
        month_key: str,
        now: datetime,
        max_input_tokens: int,
        max_output_tokens: int,
        call: Callable[[], _T],
    ) -> _T:
        """Authorize, execute once, then reconcile from provider-reported usage.

        Pricing is resolved before any provider attempt. The provider retry/circuit
        permit is then acquired before budget reservation. If budget authorization
        rejects the operation, the permit is atomically rewound because no provider
        call occurred. Once the provider call begins, its worst-case reservation is
        deliberately retained on failure or incomplete usage until reconciliation.
        """
        if not operation_reference:
            raise RuntimeFinOpsConfigurationError(
                "stable internal operation reference is required"
            )

        price = self._pricing.resolve_text(
            provider=provider,
            model=model,
            today=now.date(),
        )
        reserved_microusd = _worst_case_cost(
            price,
            max_input_tokens=max_input_tokens,
            max_output_tokens=max_output_tokens,
        )
        if reserved_microusd <= 0:
            raise RuntimeFinOpsConfigurationError(
                "paid text runtime requires a positive worst-case reservation"
            )

        operation_key = derive_opaque_budget_operation_key(
            key_material=self._operation_key_material,
            operation_reference=(
                f"provider={provider}|model={model}|workload={workload}|"
                f"operation={operation_reference}"
            ),
        )
        permit = self._provider_guard.begin_attempt(
            provider=provider,
            operation_key=operation_key,
            now=now,
        )

        try:
            bundle = self._budget.authorize(
                provider=provider,
                workload=workload,
                month_key=month_key,
                reserved_microusd=reserved_microusd,
                idempotency_key=operation_key,
            )
        except Exception:
            _abort_pre_provider_attempt(permit)
            raise

        response = self._execute_provider_once(
            provider=provider,
            permit=permit,
            call=call,
        )
        self._reconcile_success(
            price=price,
            response=response,
            bundle=bundle,
            reserved_microusd=reserved_microusd,
        )
        return response

    def _execute_provider_once(
        self,
        *,
        provider: str,
        permit: ProviderAttemptPermit,
        call: Callable[[], _T],
    ) -> _T:
        try:
            response = call()
        except Exception as exc:
            normalized = normalize_provider_exception(exc, provider)
            self._provider_guard.record_failure(
                permit,
                error_code=normalized.code,
                now=timezone.now(),
            )
            raise normalized from None

        self._provider_guard.record_success(permit, now=timezone.now())
        return response

    def _reconcile_success(
        self,
        *,
        price: TextTokenPrice,
        response: LLMResponse,
        bundle: BudgetReservationBundle,
        reserved_microusd: int,
    ) -> None:
        actual_microusd = _provider_reported_actual_cost(price, response)
        if actual_microusd is None:
            logger.warning(
                "runtime_finops unreconciled provider=%s reason=missing_provider_usage",
                price.provider,
            )
            return
        if actual_microusd > reserved_microusd:
            logger.error(
                "runtime_finops unreconciled provider=%s reason=usage_exceeds_reservation",
                price.provider,
            )
            return
        self._budget.settle(bundle, actual_microusd)
