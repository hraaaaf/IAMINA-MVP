"""
Tests for KimiProvider — mocked, no real API calls.

T1: complete() returns LLMResponse with model as provider.
T2: stream() yields text chunks from the OpenAI stream.
T3: missing openai package logs an error and sets client=None.
T4: complete() raises RuntimeError when client is None.
T5: factory resolves KimiProvider when LLM_PROVIDER=kimi.
T6: Gemini quota exhaustion stays local even when KIMI_API_KEY is set.
"""
from unittest.mock import MagicMock, patch

import pytest

# ── helpers ───────────────────────────────────────────────────────────────────

def _make_completion(content: str, model: str = "kimi-k2"):
    choice = MagicMock()
    choice.message.content = content
    resp = MagicMock()
    resp.choices = [choice]
    return resp


def _make_kimi(api_key="test-key", base_url="http://kimi.local/v1", model="kimi-k2"):
    mock_client = MagicMock()
    with patch("llm.kimi.settings") as mock_settings, \
         patch("llm.kimi.OpenAI", return_value=mock_client) as _:
        mock_settings.KIMI_API_KEY = api_key
        mock_settings.KIMI_BASE_URL = base_url
        from llm.kimi import KimiProvider
        provider = KimiProvider(model=model)
    provider.client = mock_client
    return provider


# ── T1: complete() ────────────────────────────────────────────────────────────

def test_complete_returns_llm_response():
    provider = _make_kimi()
    provider.client.chat.completions.create.return_value = _make_completion("Bonjour!")
    from llm.base import LLMResponse
    result = provider.complete("system", "user")
    assert isinstance(result, LLMResponse)
    assert result.content == "Bonjour!"
    assert result.provider == "kimi-k2"


def test_complete_passes_system_and_user():
    provider = _make_kimi()
    provider.client.chat.completions.create.return_value = _make_completion("ok")
    provider.complete("sys-prompt", "user-prompt")
    call_kwargs = provider.client.chat.completions.create.call_args
    call_kwargs.kwargs.get("messages") or call_kwargs.args[0] if call_kwargs.args else call_kwargs.kwargs["messages"]
    # find messages in the call
    all_kwargs = dict(call_kwargs.kwargs)
    msgs = all_kwargs.get("messages", [])
    assert any(m["role"] == "system" and m["content"] == "sys-prompt" for m in msgs)
    assert any(m["role"] == "user" and m["content"] == "user-prompt" for m in msgs)


# ── T2: stream() ──────────────────────────────────────────────────────────────

def test_stream_yields_chunks():
    provider = _make_kimi()

    mock_stream_ctx = MagicMock()
    mock_stream_ctx.__enter__ = MagicMock(return_value=mock_stream_ctx)
    mock_stream_ctx.__exit__ = MagicMock(return_value=False)
    mock_stream_ctx.text_stream = iter(["Bonjour", " monde", "!"])
    provider.client.chat.completions.stream.return_value = mock_stream_ctx

    chunks = list(provider.stream("sys", "user"))
    assert chunks == ["Bonjour", " monde", "!"]


def test_stream_skips_empty_chunks():
    provider = _make_kimi()

    mock_stream_ctx = MagicMock()
    mock_stream_ctx.__enter__ = MagicMock(return_value=mock_stream_ctx)
    mock_stream_ctx.__exit__ = MagicMock(return_value=False)
    mock_stream_ctx.text_stream = iter(["Hello", "", None, " world"])
    provider.client.chat.completions.stream.return_value = mock_stream_ctx

    chunks = list(provider.stream("sys", "user"))
    assert "" not in chunks
    assert None not in chunks
    assert "Hello" in chunks
    assert " world" in chunks


# ── T3: missing openai logs error ─────────────────────────────────────────────

def test_missing_openai_sets_client_none():
    with patch("llm.kimi.OpenAI", None), \
         patch("llm.kimi.settings") as mock_settings:
        mock_settings.KIMI_API_KEY = "key"
        mock_settings.KIMI_BASE_URL = "http://x"
        from llm.kimi import KimiProvider
        provider = KimiProvider()
        assert provider.client is None


# ── T4: complete() raises when client=None ────────────────────────────────────

def test_complete_raises_when_no_client():
    provider = _make_kimi()
    provider.client = None
    with pytest.raises(RuntimeError, match="client not initialized"):
        provider.complete("sys", "user")


def test_stream_raises_when_no_client():
    provider = _make_kimi()
    provider.client = None
    with pytest.raises(RuntimeError, match="client not initialized"):
        list(provider.stream("sys", "user"))


# ── T5: factory resolves KimiProvider when LLM_PROVIDER=kimi ─────────────────

def test_factory_resolves_kimi_provider():
    with patch("llm.factory.settings") as mock_settings, \
         patch("llm.kimi.settings") as ks, \
         patch("llm.kimi.OpenAI", return_value=MagicMock()):
        mock_settings.LLM_PROVIDER = "kimi"
        mock_settings.LLM_MODEL = None
        ks.KIMI_API_KEY = "test-key"
        ks.KIMI_BASE_URL = "http://kimi.local/v1"
        from llm.factory import get_llm
        from llm.kimi import KimiProvider
        provider = get_llm()
        assert isinstance(provider, KimiProvider)


# ── T6: Gemini quota exhaustion never selects Kimi implicitly ────────────────

def test_factory_gemini_quota_exhaustion_stays_local():
    with patch("llm.factory.settings") as mock_settings, \
         patch("llm.rate_guard.should_use_gemini", return_value=False), \
         patch("llm.kimi.KimiProvider") as mock_kimi:
        mock_settings.LLM_PROVIDER = "gemini"
        mock_settings.LLM_MODEL = None
        mock_settings.KIMI_API_KEY = "test-key"
        from llm.factory import get_llm
        from llm.fallback import QuotaExhaustedProvider
        result = get_llm()
        assert isinstance(result, QuotaExhaustedProvider)
        mock_kimi.assert_not_called()
