from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from django.test import override_settings

from llm.errors import (
    LLMProviderQuotaExceeded,
    LLMProviderTimeout,
    LLMProviderUnavailable,
)
from llm.factory import _provider_policy_name
from llm.lowcost_openai_compatible import (
    DeepSeekProvider,
    OpenAICompatibleLowCostProvider,
    QwenProvider,
)


@pytest.mark.parametrize("provider_cls", [DeepSeekProvider, QwenProvider])
def test_lowcost_provider_requires_explicit_configuration(provider_cls):
    with override_settings(
        DEEPSEEK_API_KEY="",
        DEEPSEEK_BASE_URL="",
        DEEPSEEK_MODEL="",
        QWEN_API_KEY="",
        QWEN_BASE_URL="",
        QWEN_MODEL="",
    ):
        with pytest.raises(RuntimeError, match="API key, base URL and model"):
            provider_cls()


def test_processor_policy_names_are_explicit():
    deepseek = object.__new__(DeepSeekProvider)
    qwen = object.__new__(QwenProvider)
    assert _provider_policy_name(deepseek) == "deepseek"
    assert _provider_policy_name(qwen) == "qwen"


def test_compatible_provider_reads_environment_when_django_setting_is_blank(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "synthetic-env-key")
    monkeypatch.setenv("GROQ_BASE_URL", "https://example.invalid/openai/v1")
    monkeypatch.setenv("GROQ_MODEL", "synthetic-model")

    with override_settings(GROQ_API_KEY="", GROQ_BASE_URL="", GROQ_MODEL=""):
        provider = OpenAICompatibleLowCostProvider(
            provider_id="groq",
            settings_prefix="GROQ",
        )
    try:
        assert provider.model_name == "synthetic-model"
        assert str(provider.client.base_url) == "https://example.invalid/openai/v1/"
    finally:
        provider.client.close()


class SyntheticHTTPError(Exception):
    def __init__(self, status_code: int):
        super().__init__(f"synthetic HTTP {status_code}")
        self.status_code = status_code


def _synthetic_provider(exc: Exception) -> tuple[OpenAICompatibleLowCostProvider, MagicMock]:
    provider = object.__new__(OpenAICompatibleLowCostProvider)
    provider.provider_id = "groq"
    provider.model = "openai/gpt-oss-120b"
    provider.timeout_seconds = 15.0
    client = MagicMock()
    client.chat.completions.create.side_effect = exc
    provider.client = client
    return provider, client


def _successful_provider(
    provider_id: str,
    model: str,
) -> tuple[OpenAICompatibleLowCostProvider, MagicMock]:
    provider = object.__new__(OpenAICompatibleLowCostProvider)
    provider.provider_id = provider_id
    provider.model = model
    provider.timeout_seconds = 15.0
    client = MagicMock()
    response = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content="{}"))],
        usage=None,
    )
    client.chat.completions.create.return_value = response
    provider.client = client
    return provider, client


@pytest.mark.parametrize(
    ("exc", "expected_error"),
    [
        (TimeoutError("synthetic timeout"), LLMProviderTimeout),
        (SyntheticHTTPError(429), LLMProviderQuotaExceeded),
        (SyntheticHTTPError(503), LLMProviderUnavailable),
    ],
)
def test_openai_compatible_failures_are_normalized_without_hidden_retry(exc, expected_error):
    provider, client = _synthetic_provider(exc)

    with pytest.raises(expected_error) as raised:
        provider.complete("system", "synthetic user")

    assert raised.value.provider == "groq"
    assert client.chat.completions.create.call_count == 1


def test_groq_gpt_oss_uses_low_reasoning_with_fixed_160_token_ceiling():
    provider, client = _successful_provider("groq", "openai/gpt-oss-120b")

    provider.complete("system", "synthetic user")

    kwargs = client.chat.completions.create.call_args.kwargs
    assert kwargs["max_tokens"] == 160
    assert kwargs["reasoning_effort"] == "low"


@pytest.mark.parametrize(
    ("provider_id", "model"),
    [
        ("qwen", "qwen-plus"),
        ("deepseek", "deepseek-chat"),
        ("groq", "llama-3.3-70b-versatile"),
    ],
)
def test_reasoning_effort_is_not_leaked_to_other_provider_model_pairs(provider_id, model):
    provider, client = _successful_provider(provider_id, model)

    provider.complete("system", "synthetic user")

    kwargs = client.chat.completions.create.call_args.kwargs
    assert kwargs["max_tokens"] == 160
    assert "reasoning_effort" not in kwargs
