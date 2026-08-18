import pytest
from django.test import override_settings

from llm.factory import _provider_policy_name
from llm.lowcost_openai_compatible import DeepSeekProvider, QwenProvider


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
