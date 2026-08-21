"""Persistent retry ceilings and circuit breaker for paid provider operations.

This guard stores only provider identifiers, opaque HMAC operation keys, attempt
counters and stable error codes. It never stores prompts, responses, patient
identifiers or raw exception text.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timedelta

from django.db import transaction
from django.utils import timezone

from core.models import AIProviderCircuitState, AIProviderOperationAttempt

_IDENTIFIER_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]{0,63}$")
_OPAQUE_KEY_RE = re.compile(r"^hmac256:[0-9a-f]{64}$")
_STABLE_ERROR_CODES = frozenset(
    {
        "provider_timeout",
        "provider_unavailable",
        "provider_quota_exceeded",
        "provider_malformed_response",
        "provider_internal_failure",
    }
)
_CIRCUIT_ERROR_CODES = frozenset(
    {
        "provider_timeout",
        "provider_unavailable",
        "provider_quota_exceeded",
    }
)
_ABSOLUTE_MAX_ATTEMPTS = 3


class ProviderGuardError(RuntimeError):
    """Base class for stable, non-sensitive provider guard failures."""

    code = "provider_guard_error"


class ProviderCircuitOpen(ProviderGuardError):
    code = "provider_circuit_open"


class ProviderOperationInFlight(ProviderGuardError):
    code = "provider_operation_in_flight"


class ProviderRetryExhausted(ProviderGuardError):
    code = "provider_retry_exhausted"


class ProviderOperationCompleted(ProviderGuardError):
    code = "provider_operation_completed"


class ProviderStaleAttempt(ProviderGuardError):
    code = "provider_stale_attempt"


@dataclass(frozen=True, slots=True)
class ProviderFailurePolicy:
    max_attempts_per_operation: int
    failure_threshold: int
    circuit_cooldown_seconds: int
    in_flight_lease_seconds: int

    def validate(self) -> None:
        if not 1 <= self.max_attempts_per_operation <= _ABSOLUTE_MAX_ATTEMPTS:
            raise ValueError(
                "max_attempts_per_operation must be between 1 and "
                f"{_ABSOLUTE_MAX_ATTEMPTS}"
            )
        if self.failure_threshold <= 0:
            raise ValueError("failure_threshold must be positive")
        if self.circuit_cooldown_seconds <= 0:
            raise ValueError("circuit_cooldown_seconds must be positive")
        if self.in_flight_lease_seconds <= 0:
            raise ValueError("in_flight_lease_seconds must be positive")


@dataclass(frozen=True, slots=True)
class ProviderAttemptPermit:
    provider: str
    operation_key: str
    attempt_number: int
    half_open_probe: bool


class PersistentProviderFailureGuard:
    """Cross-worker retry/circuit guard using PostgreSQL row locks.

    The guard deliberately performs no automatic retry and no sleep. A caller
    may make another attempt only by presenting the same opaque operation key;
    the persistent attempt counter then enforces the configured ceiling.
    """

    def __init__(self, policy: ProviderFailurePolicy) -> None:
        policy.validate()
        self.policy = policy

    @staticmethod
    def _validate_provider(provider: str) -> None:
        if not _IDENTIFIER_RE.fullmatch(provider):
            raise ValueError("invalid provider guard identifier")

    @staticmethod
    def _validate_operation_key(operation_key: str) -> None:
        if not _OPAQUE_KEY_RE.fullmatch(operation_key):
            raise ValueError(
                "provider operation key must be an opaque HMAC-SHA256 key"
            )

    @staticmethod
    def _validate_now(now: datetime) -> None:
        if not timezone.is_aware(now):
            raise ValueError("provider guard timestamps must be timezone-aware")

    @staticmethod
    def _locked_circuit(provider: str) -> AIProviderCircuitState:
        state, _ = AIProviderCircuitState.objects.get_or_create(provider=provider)
        return AIProviderCircuitState.objects.select_for_update().get(pk=state.pk)

    @staticmethod
    def _locked_operation(
        *, provider: str, operation_key: str
    ) -> AIProviderOperationAttempt:
        state, _ = AIProviderOperationAttempt.objects.get_or_create(
            provider=provider,
            operation_key=operation_key,
        )
        return AIProviderOperationAttempt.objects.select_for_update().get(pk=state.pk)

    def begin_attempt(
        self,
        *,
        provider: str,
        operation_key: str,
        now: datetime,
    ) -> ProviderAttemptPermit:
        self._validate_provider(provider)
        self._validate_operation_key(operation_key)
        self._validate_now(now)
        lease_until = now + timedelta(seconds=self.policy.in_flight_lease_seconds)

        with transaction.atomic():
            circuit = self._locked_circuit(provider)
            half_open_probe = False
            if circuit.opened_until is not None:
                if circuit.opened_until > now:
                    raise ProviderCircuitOpen("provider circuit is open")
                if (
                    circuit.probe_in_flight_until is not None
                    and circuit.probe_in_flight_until > now
                ):
                    raise ProviderCircuitOpen(
                        "provider circuit half-open probe is in flight"
                    )
                half_open_probe = True

            operation = self._locked_operation(
                provider=provider,
                operation_key=operation_key,
            )
            if operation.completed_at is not None:
                raise ProviderOperationCompleted("provider operation already completed")
            if (
                operation.in_flight_until is not None
                and operation.in_flight_until > now
            ):
                raise ProviderOperationInFlight(
                    "provider operation attempt is in flight"
                )
            if operation.attempt_count >= self.policy.max_attempts_per_operation:
                raise ProviderRetryExhausted("provider retry ceiling exhausted")

            operation.attempt_count += 1
            operation.active_attempt_number = operation.attempt_count
            operation.in_flight_until = lease_until
            operation.save(
                update_fields=(
                    "attempt_count",
                    "active_attempt_number",
                    "in_flight_until",
                    "updated_at",
                )
            )

            if half_open_probe:
                circuit.probe_in_flight_until = lease_until
                circuit.save(update_fields=("probe_in_flight_until", "updated_at"))

            return ProviderAttemptPermit(
                provider=provider,
                operation_key=operation_key,
                attempt_number=operation.attempt_count,
                half_open_probe=half_open_probe,
            )

    def record_success(
        self,
        permit: ProviderAttemptPermit,
        *,
        now: datetime,
    ) -> None:
        self._validate_permit(permit)
        self._validate_now(now)
        with transaction.atomic():
            circuit = self._locked_circuit(permit.provider)
            operation = self._locked_operation(
                provider=permit.provider,
                operation_key=permit.operation_key,
            )
            if operation.completed_at is not None:
                return
            if operation.active_attempt_number != permit.attempt_number:
                raise ProviderStaleAttempt(
                    "provider success belongs to a stale attempt"
                )

            operation.completed_at = now
            operation.in_flight_until = None
            operation.active_attempt_number = None
            operation.last_error_code = ""
            operation.save(
                update_fields=(
                    "completed_at",
                    "in_flight_until",
                    "active_attempt_number",
                    "last_error_code",
                    "updated_at",
                )
            )

            circuit.consecutive_failures = 0
            circuit.opened_until = None
            circuit.probe_in_flight_until = None
            circuit.last_error_code = ""
            circuit.save(
                update_fields=(
                    "consecutive_failures",
                    "opened_until",
                    "probe_in_flight_until",
                    "last_error_code",
                    "updated_at",
                )
            )

    def record_failure(
        self,
        permit: ProviderAttemptPermit,
        *,
        error_code: str,
        now: datetime,
    ) -> None:
        self._validate_permit(permit)
        self._validate_now(now)
        if error_code not in _STABLE_ERROR_CODES:
            raise ValueError("provider guard requires a stable provider error code")

        with transaction.atomic():
            circuit = self._locked_circuit(permit.provider)
            operation = self._locked_operation(
                provider=permit.provider,
                operation_key=permit.operation_key,
            )
            if operation.completed_at is not None:
                raise ProviderStaleAttempt(
                    "provider failure arrived after completion"
                )
            if operation.active_attempt_number != permit.attempt_number:
                raise ProviderStaleAttempt(
                    "provider failure belongs to a stale attempt"
                )

            operation.in_flight_until = None
            operation.active_attempt_number = None
            operation.last_error_code = error_code
            operation.save(
                update_fields=(
                    "in_flight_until",
                    "active_attempt_number",
                    "last_error_code",
                    "updated_at",
                )
            )

            if error_code not in _CIRCUIT_ERROR_CODES:
                if permit.half_open_probe:
                    circuit.probe_in_flight_until = None
                    circuit.save(
                        update_fields=("probe_in_flight_until", "updated_at")
                    )
                return

            if permit.half_open_probe:
                circuit.consecutive_failures = max(
                    circuit.consecutive_failures,
                    self.policy.failure_threshold,
                )
            else:
                circuit.consecutive_failures += 1
            circuit.last_error_code = error_code
            circuit.probe_in_flight_until = None
            if circuit.consecutive_failures >= self.policy.failure_threshold:
                circuit.opened_until = now + timedelta(
                    seconds=self.policy.circuit_cooldown_seconds
                )
            circuit.save(
                update_fields=(
                    "consecutive_failures",
                    "opened_until",
                    "probe_in_flight_until",
                    "last_error_code",
                    "updated_at",
                )
            )

    def _validate_permit(self, permit: ProviderAttemptPermit) -> None:
        self._validate_provider(permit.provider)
        self._validate_operation_key(permit.operation_key)
        if permit.attempt_number <= 0:
            raise ValueError("attempt_number must be positive")
