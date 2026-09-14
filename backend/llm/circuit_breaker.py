"""Process-local fail-fast circuit breaker for outbound LLM providers.

The breaker is deliberately provider-scoped and contains no patient/prompt data.
Network timeouts remain enforced by provider adapters; this layer prevents a
known-unhealthy provider from being hammered repeatedly inside one runtime.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass

from .errors import LLMProviderError, LLMProviderUnavailable

_FAILURE_THRESHOLD = 3
_RECOVERY_SECONDS = 30.0


@dataclass
class _CircuitState:
    consecutive_failures: int = 0
    opened_at: float | None = None


_lock = threading.Lock()
_states: dict[str, _CircuitState] = {}


def _state(provider: str) -> _CircuitState:
    return _states.setdefault(provider, _CircuitState())


def assert_provider_available(provider: str, *, now: float | None = None) -> None:
    """Fail fast while the provider circuit is open.

    Once the recovery window expires, one caller is allowed through as a
    half-open probe. A successful call closes the circuit; another retryable
    failure opens it again.
    """

    current = time.monotonic() if now is None else now
    with _lock:
        state = _state(provider)
        if state.opened_at is None:
            return
        if current - state.opened_at < _RECOVERY_SECONDS:
            raise LLMProviderUnavailable(provider)
        # Half-open probe. Reset the timestamp so a failed probe can reopen it.
        state.opened_at = None
        state.consecutive_failures = _FAILURE_THRESHOLD - 1


def record_provider_success(provider: str) -> None:
    """Close the provider circuit after one successful operation."""

    with _lock:
        state = _state(provider)
        state.consecutive_failures = 0
        state.opened_at = None


def record_provider_failure(
    provider: str,
    error: LLMProviderError,
    *,
    now: float | None = None,
) -> None:
    """Count retryable transport/service failures and open after the threshold."""

    if not error.retryable:
        return
    current = time.monotonic() if now is None else now
    with _lock:
        state = _state(provider)
        state.consecutive_failures += 1
        if state.consecutive_failures >= _FAILURE_THRESHOLD:
            state.opened_at = current


def reset_provider_circuit_breakers() -> None:
    """Test/support hook; contains no production state beyond local counters."""

    with _lock:
        _states.clear()
