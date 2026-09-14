from types import SimpleNamespace

import pytest

from llm.circuit_breaker import reset_provider_circuit_breakers
from llm.errors import LLMProviderTimeout, LLMProviderUnavailable
from llm.runtime import execute_external_provider_call


@pytest.fixture(autouse=True)
def _reset_breakers():
    reset_provider_circuit_breakers()
    yield
    reset_provider_circuit_breakers()


@pytest.fixture(autouse=True)
def _authorize_multimodal(monkeypatch):
    monkeypatch.setattr(
        "llm.runtime.assert_ai_egress_allowed",
        lambda modality: SimpleNamespace(purpose="voice_transcription"),
    )
    monkeypatch.setattr(
        "llm.runtime.authorize_processor_policy",
        lambda provider, purpose, modality: None,
    )


def test_multimodal_boundary_opens_after_three_retryable_failures():
    calls = 0

    def failing_call():
        nonlocal calls
        calls += 1
        raise TimeoutError("raw multimodal vendor detail")

    for _ in range(3):
        with pytest.raises(LLMProviderTimeout):
            execute_external_provider_call(
                "gemini",
                "audio",
                "transcribe",
                failing_call,
                timeout_seconds=1.0,
            )

    with pytest.raises(LLMProviderUnavailable) as caught:
        execute_external_provider_call(
            "gemini",
            "audio",
            "transcribe",
            failing_call,
            timeout_seconds=1.0,
        )

    assert calls == 3
    assert caught.value.code == "provider_unavailable"
    assert "vendor" not in str(caught.value)


def test_multimodal_success_resets_provider_failure_counter():
    def failing_call():
        raise TimeoutError("transport detail")

    for _ in range(2):
        with pytest.raises(LLMProviderTimeout):
            execute_external_provider_call(
                "gemini",
                "image",
                "analyze",
                failing_call,
                timeout_seconds=1.0,
            )

    assert (
        execute_external_provider_call(
            "gemini",
            "image",
            "analyze",
            lambda: "healthy",
            timeout_seconds=1.0,
        )
        == "healthy"
    )
