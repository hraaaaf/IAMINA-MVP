import pytest

from llm.circuit_breaker import (
    assert_provider_available,
    record_provider_failure,
    record_provider_success,
    reset_provider_circuit_breakers,
)
from llm.errors import LLMProviderTimeout, LLMProviderUnavailable
from llm.factory import _execute_provider_call


@pytest.fixture(autouse=True)
def _reset_breakers():
    reset_provider_circuit_breakers()
    yield
    reset_provider_circuit_breakers()


def test_factory_boundary_opens_after_three_retryable_failures_and_fails_fast():
    calls = 0

    def failing_call():
        nonlocal calls
        calls += 1
        raise TimeoutError("raw vendor timeout detail")

    for _ in range(3):
        with pytest.raises(LLMProviderTimeout):
            _execute_provider_call("test-provider", "complete", failing_call)

    with pytest.raises(LLMProviderUnavailable) as caught:
        _execute_provider_call("test-provider", "complete", failing_call)

    assert calls == 3
    assert caught.value.code == "provider_unavailable"
    assert caught.value.retryable is True
    assert "vendor" not in str(caught.value)


def test_success_resets_consecutive_failure_counter():
    def timeout():
        raise TimeoutError("transport detail")

    for _ in range(2):
        with pytest.raises(LLMProviderTimeout):
            _execute_provider_call("test-provider", "complete", timeout)

    assert _execute_provider_call(
        "test-provider",
        "complete",
        lambda: "healthy",
    ) == "healthy"

    for _ in range(2):
        with pytest.raises(LLMProviderTimeout):
            _execute_provider_call("test-provider", "complete", timeout)

    # Two failures after a success must not leave the circuit open.
    assert _execute_provider_call(
        "test-provider",
        "complete",
        lambda: "recovered",
    ) == "recovered"


def test_recovery_window_allows_only_one_half_open_probe():
    provider = "test-provider"
    error = LLMProviderTimeout(provider)
    for _ in range(3):
        record_provider_failure(provider, error, now=100.0)

    with pytest.raises(LLMProviderUnavailable):
        assert_provider_available(provider, now=110.0)

    # Recovery window elapsed: first caller becomes the half-open probe.
    assert_provider_available(provider, now=131.0)
    with pytest.raises(LLMProviderUnavailable):
        assert_provider_available(provider, now=131.0)

    record_provider_success(provider)
    assert_provider_available(provider, now=131.0)
