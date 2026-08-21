from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta

import pytest
from django.db import close_old_connections, connection

from core.models import AIProviderCircuitState, AIProviderOperationAttempt
from llm.provider_guard import (
    PersistentProviderFailureGuard,
    ProviderCircuitOpen,
    ProviderFailurePolicy,
    ProviderOperationCompleted,
    ProviderOperationInFlight,
    ProviderRetryExhausted,
    ProviderStaleAttempt,
)

pytestmark = pytest.mark.django_db(transaction=True)
_KEY_A = "hmac256:" + "a" * 64
_KEY_B = "hmac256:" + "b" * 64
_KEY_C = "hmac256:" + "c" * 64
_KEY_D = "hmac256:" + "d" * 64


def _now():
    return datetime.now(UTC)


def _guard(
    *,
    max_attempts: int = 2,
    failure_threshold: int = 2,
    cooldown_seconds: int = 60,
    lease_seconds: int = 30,
) -> PersistentProviderFailureGuard:
    return PersistentProviderFailureGuard(
        ProviderFailurePolicy(
            max_attempts_per_operation=max_attempts,
            failure_threshold=failure_threshold,
            circuit_cooldown_seconds=cooldown_seconds,
            in_flight_lease_seconds=lease_seconds,
        )
    )


def test_provider_guard_rejects_non_opaque_operation_keys():
    guard = _guard()
    with pytest.raises(ValueError, match="opaque HMAC"):
        guard.begin_attempt(
            provider="groq",
            operation_key="patient-123",
            now=_now(),
        )


def test_retry_ceiling_persists_without_automatic_retry():
    guard = _guard(max_attempts=2, failure_threshold=9)
    now = _now()

    first = guard.begin_attempt(provider="groq", operation_key=_KEY_A, now=now)
    guard.record_failure(
        first,
        error_code="provider_internal_failure",
        now=now + timedelta(seconds=1),
    )
    second = guard.begin_attempt(
        provider="groq",
        operation_key=_KEY_A,
        now=now + timedelta(seconds=2),
    )
    guard.record_failure(
        second,
        error_code="provider_internal_failure",
        now=now + timedelta(seconds=3),
    )

    with pytest.raises(ProviderRetryExhausted):
        guard.begin_attempt(
            provider="groq",
            operation_key=_KEY_A,
            now=now + timedelta(seconds=4),
        )

    state = AIProviderOperationAttempt.objects.get(
        provider="groq", operation_key=_KEY_A
    )
    assert state.attempt_count == 2
    assert state.active_attempt_number is None


def test_timeout_and_5xx_equivalent_errors_open_persistent_circuit():
    guard = _guard(failure_threshold=2)
    now = _now()

    first = guard.begin_attempt(provider="groq", operation_key=_KEY_A, now=now)
    guard.record_failure(
        first,
        error_code="provider_timeout",
        now=now + timedelta(seconds=1),
    )
    second = guard.begin_attempt(
        provider="groq",
        operation_key=_KEY_B,
        now=now + timedelta(seconds=2),
    )
    guard.record_failure(
        second,
        error_code="provider_unavailable",
        now=now + timedelta(seconds=3),
    )

    circuit = AIProviderCircuitState.objects.get(provider="groq")
    assert circuit.consecutive_failures == 2
    assert circuit.opened_until is not None

    with pytest.raises(ProviderCircuitOpen):
        guard.begin_attempt(
            provider="groq",
            operation_key=_KEY_C,
            now=now + timedelta(seconds=4),
        )


def test_429_counts_toward_circuit_open():
    guard = _guard(failure_threshold=1)
    now = _now()

    permit = guard.begin_attempt(provider="groq", operation_key=_KEY_A, now=now)
    guard.record_failure(
        permit,
        error_code="provider_quota_exceeded",
        now=now + timedelta(seconds=1),
    )

    with pytest.raises(ProviderCircuitOpen):
        guard.begin_attempt(
            provider="groq",
            operation_key=_KEY_B,
            now=now + timedelta(seconds=2),
        )


def test_half_open_allows_one_probe_and_success_resets_circuit():
    guard = _guard(failure_threshold=1, cooldown_seconds=10, lease_seconds=20)
    now = _now()

    first = guard.begin_attempt(provider="groq", operation_key=_KEY_A, now=now)
    guard.record_failure(
        first,
        error_code="provider_timeout",
        now=now + timedelta(seconds=1),
    )

    probe_time = now + timedelta(seconds=12)
    probe = guard.begin_attempt(
        provider="groq",
        operation_key=_KEY_B,
        now=probe_time,
    )
    assert probe.half_open_probe is True

    with pytest.raises(ProviderCircuitOpen):
        guard.begin_attempt(
            provider="groq",
            operation_key=_KEY_C,
            now=probe_time + timedelta(seconds=1),
        )

    guard.record_success(probe, now=probe_time + timedelta(seconds=2))
    next_permit = guard.begin_attempt(
        provider="groq",
        operation_key=_KEY_C,
        now=probe_time + timedelta(seconds=3),
    )
    assert next_permit.half_open_probe is False


def test_completed_operation_cannot_call_provider_again():
    guard = _guard()
    now = _now()
    permit = guard.begin_attempt(provider="groq", operation_key=_KEY_A, now=now)
    guard.record_success(permit, now=now + timedelta(seconds=1))

    with pytest.raises(ProviderOperationCompleted):
        guard.begin_attempt(
            provider="groq",
            operation_key=_KEY_A,
            now=now + timedelta(seconds=2),
        )


def test_expired_lease_allows_retry_but_stale_result_cannot_overwrite_it():
    guard = _guard(max_attempts=2, failure_threshold=9, lease_seconds=5)
    now = _now()
    first = guard.begin_attempt(provider="groq", operation_key=_KEY_A, now=now)
    second = guard.begin_attempt(
        provider="groq",
        operation_key=_KEY_A,
        now=now + timedelta(seconds=6),
    )
    assert second.attempt_number == 2

    with pytest.raises(ProviderStaleAttempt):
        guard.record_failure(
            first,
            error_code="provider_timeout",
            now=now + timedelta(seconds=7),
        )


@pytest.mark.skipif(
    connection.vendor != "postgresql",
    reason="row-lock concurrency proof requires PostgreSQL",
)
def test_concurrent_same_operation_allows_only_one_in_flight_attempt():
    guard = _guard(max_attempts=2, failure_threshold=9, lease_seconds=30)
    now = _now()

    def attempt():
        close_old_connections()
        try:
            permit = guard.begin_attempt(
                provider="groq",
                operation_key=_KEY_D,
                now=now,
            )
            return ("ok", permit.attempt_number)
        except ProviderOperationInFlight:
            return ("blocked", None)
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: attempt(), range(2)))

    assert sorted(status for status, _ in results) == ["blocked", "ok"]
    state = AIProviderOperationAttempt.objects.get(
        provider="groq", operation_key=_KEY_D
    )
    assert state.attempt_count == 1
