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
    half_open_probe_in_flight: bool = False


_lock = threading.Lock()
_states: dict[str, _CircuitState] = {}


def _state(provider: str) -> _CircuitState:
    return _states.setdefault(provider, _CircuitState())


def assert_provider_available(provider: str, *, now: float | None = None) -> None:
    """Fail fast while open and admit only one half-open recovery probe."""

    current = time.monotonic() if now is None else now
    with _lock:
        state = _state(provider)
        if state.opened_at is None:
            return
        if current - state.opened_at < _RECOVERY_SECONDS:
            raise LLMProviderUnavailable(provider)
        if state.half_open_probe_in_flight:
            raise LLMProviderUnavailable(provider)
        state.half_open_probe_in_flight = True


def record_provider_success(provider: str) -> None:
    """Close the provider circuit after one successful operation."""

    with _lock:
        state = _state(provider)
        state.consecutive_failures = 0
        state.opened_at = None
        state.half_open_probe_in_flight = False


def record_provider_failure(
    provider: str,
    error: LLMProviderError,
    *,
    now: float | None = None,
) -> None:
    """Open on repeated retryable failures; non-retryable responses close recovery probes."""

    current = time.monotonic() if now is None else now
    with _lock:
        state = _state(provider)
        state.half_open_probe_in_flight = False
        if not error.retryable:
            state.consecutive_failures = 0
            state.opened_at = None
            return
        state.consecutive_failures += 1
        if state.consecutive_failures >= _FAILURE_THRESHOLD:
            state.opened_at = current


def reset_provider_circuit_breakers() -> None:
    """Test/support hook; contains no production state beyond local counters."""

    with _lock:
        _states.clear()
