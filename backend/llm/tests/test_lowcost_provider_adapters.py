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
