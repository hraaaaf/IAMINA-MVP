from pathlib import Path
from types import SimpleNamespace

import pytest

from core.ai_processor_policy import AIProcessorPolicyDenied
from llm.errors import LLMProviderInternalFailure, LLMProviderTimeout
from llm.runtime import execute_external_provider_call

_BACKEND = Path(__file__).resolve().parents[2]
_MULTIMODAL_CALLSITES = (
    _BACKEND / "media" / "voice.py",
    _BACKEND / "media" / "vision.py",
    _BACKEND / "media" / "documents" / "extractors" / "image.py",
)


def test_all_multimodal_sdk_calls_use_central_runtime_boundary():
    for path in _MULTIMODAL_CALLSITES:
        source = path.read_text()
        assert "execute_external_provider_call" in source, path
        assert "assert_ai_egress_allowed" not in source, path


def test_runtime_checks_scope_and_processor_policy_before_provider_call(monkeypatch):
    events: list[str] = []

    monkeypatch.setattr(
        "llm.runtime.assert_ai_egress_allowed",
        lambda modality: events.append(f"scope:{modality}")
        or SimpleNamespace(purpose="meal_vision"),
    )
    monkeypatch.setattr(
        "llm.runtime.authorize_processor_policy",
        lambda provider, purpose, modality: events.append(
            f"policy:{provider}:{purpose}:{modality}"
        ),
    )

    result = execute_external_provider_call(
        "gemini",
        "image",
        "meal_vision",
        lambda: events.append("provider") or "ok",
    )

    assert result == "ok"
    assert events == [
        "scope:image",
        "policy:gemini:meal_vision:image",
        "provider",
    ]


def test_processor_policy_denial_prevents_provider_invocation(monkeypatch):
    called = False
    monkeypatch.setattr(
        "llm.runtime.assert_ai_egress_allowed",
        lambda modality: SimpleNamespace(purpose="voice_transcription"),
    )

    def deny(*args):
        raise AIProcessorPolicyDenied("pending")

    monkeypatch.setattr("llm.runtime.authorize_processor_policy", deny)

    def provider_call():
        nonlocal called
        called = True

    with pytest.raises(AIProcessorPolicyDenied):
        execute_external_provider_call(
            "gemini",
            "audio",
            "transcribe",
            provider_call,
        )

    assert called is False


def test_multimodal_timeout_is_typed_and_non_sensitive(monkeypatch):
    class PendingFuture:
        def result(self, timeout):
            from concurrent.futures import TimeoutError

            raise TimeoutError("vendor request secret")

        def cancel(self):
            return True

    class Executor:
        def __init__(self, **kwargs):
            pass

        def submit(self, call):
            return PendingFuture()

        def shutdown(self, **kwargs):
            pass

    monkeypatch.setattr(
        "llm.runtime.assert_ai_egress_allowed",
        lambda modality: SimpleNamespace(purpose="meal_vision"),
    )
    monkeypatch.setattr("llm.runtime.authorize_processor_policy", lambda *args: None)
    monkeypatch.setattr("llm.runtime.ThreadPoolExecutor", Executor)

    with pytest.raises(LLMProviderTimeout) as caught:
        execute_external_provider_call(
            "gemini",
            "image",
            "meal_vision",
            lambda: "unused",
        )

    assert caught.value.code == "provider_timeout"
    assert "secret" not in str(caught.value)


def test_multimodal_vendor_exception_is_normalized(monkeypatch):
    monkeypatch.setattr(
        "llm.runtime.assert_ai_egress_allowed",
        lambda modality: SimpleNamespace(purpose="document_ingest"),
    )
    monkeypatch.setattr("llm.runtime.authorize_processor_policy", lambda *args: None)

    with pytest.raises(LLMProviderInternalFailure) as caught:
        execute_external_provider_call(
            "gemini",
            "image",
            "document_image_ocr",
            lambda: (_ for _ in ()).throw(ValueError("private vendor payload")),
        )

    assert caught.value.code == "provider_internal_failure"
    assert "private vendor payload" not in str(caught.value)
