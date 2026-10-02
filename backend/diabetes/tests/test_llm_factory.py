"""
LLM Factory — provider resolution tests.

Tests that `get_llm()` returns the correct provider type depending on
the LLM_PROVIDER setting, without making any real API calls.
"""
import os
from unittest.mock import patch

from django.test import SimpleTestCase, override_settings

from llm.fallback import FallbackProvider, QuotaExhaustedProvider


class LlmFactoryProviderResolutionTest(SimpleTestCase):
    """get_llm() selects the right provider based on LLM_PROVIDER setting."""

    @override_settings(LLM_PROVIDER="fallback")
    def test_fallback_provider_returned_when_configured(self):
        from llm.factory import get_llm
        provider = get_llm()
        self.assertIsInstance(provider, FallbackProvider)

    @override_settings(LLM_PROVIDER="unknown_provider_xyz")
    def test_unknown_provider_falls_back_to_fallback(self):
        from llm.factory import get_llm
        provider = get_llm()
        self.assertIsInstance(provider, FallbackProvider)

    @override_settings(LLM_PROVIDER="groq", LLM_MODEL="openai/gpt-oss-120b")
    @patch.dict(os.environ, {"GROQ_API_KEY": "test-groq-key"}, clear=False)
    def test_groq_provider_is_text_runtime_default(self):
        from llm.factory import get_llm
        from llm.lowcost_openai_compatible import OpenAICompatibleLowCostProvider

        provider = get_llm()

        self.assertIsInstance(provider, OpenAICompatibleLowCostProvider)
        self.assertEqual(provider.provider_id, "groq")
        self.assertEqual(provider.model_name, "openai/gpt-oss-120b")
        self.assertTrue(getattr(provider, "_iamina_text_payload_policy", False))

    @override_settings(LLM_PROVIDER="gemini", LLM_MODEL="gemini-2.5-flash")
    @patch.dict(os.environ, {"GROQ_API_KEY": "test-groq-key"}, clear=False)
    def test_legacy_gemini_text_config_is_remapped_to_groq(self):
        """Stale prod env cannot silently reactivate Gemini for text."""
        from llm.factory import get_llm

        provider = get_llm()

        self.assertEqual(provider.provider_id, "groq")
        self.assertEqual(provider.model_name, "openai/gpt-oss-120b")


    @override_settings(LLM_PROVIDER="groq", LLM_MODEL="openai/gpt-oss-120b")
    @patch.dict(os.environ, {"GROQ_API_KEY": ""}, clear=False)
    def test_provider_name_does_not_require_groq_credentials(self):
        from llm.factory import get_ai_provider_name

        self.assertEqual(get_ai_provider_name(), "groq")

    @override_settings(LLM_PROVIDER="gemini", LLM_MODEL="gemini-2.5-flash")
    @patch.dict(os.environ, {"GROQ_API_KEY": ""}, clear=False)
    def test_provider_name_remaps_legacy_gemini_without_credentials(self):
        from llm.factory import get_ai_provider_name

        self.assertEqual(get_ai_provider_name(), "groq")


class LlmProviderInterfaceTest(SimpleTestCase):
    """FallbackProvider and QuotaExhaustedProvider satisfy the BaseLLMProvider interface."""

    def test_fallback_has_complete_method(self):
        provider = FallbackProvider()
        self.assertTrue(hasattr(provider, "complete"))
        self.assertTrue(callable(provider.complete))

    def test_quota_exhausted_has_complete_method(self):
        provider = QuotaExhaustedProvider()
        self.assertTrue(hasattr(provider, "complete"))
        self.assertTrue(callable(provider.complete))

    def test_fallback_complete_returns_llm_response(self):
        from llm.base import LLMResponse
        provider = FallbackProvider()
        result = provider.complete(system="chat assistant", user="bonjour")
        self.assertIsInstance(result, LLMResponse)
        self.assertIsInstance(result.content, str)
        self.assertGreater(len(result.content), 0)

    def test_quota_exhausted_complete_returns_quota_message(self):
        from llm.base import LLMResponse
        provider = QuotaExhaustedProvider()
        result = provider.complete(system="chat assistant", user="bonjour")
        self.assertIsInstance(result, LLMResponse)
        # Must communicate the quota situation to the user (not a generic error)
        self.assertGreater(len(result.content), 20)

    def test_fallback_stream_yields_string(self):
        provider = FallbackProvider()
        chunks = list(provider.stream(system="chat assistant", user="bonjour"))
        self.assertGreater(len(chunks), 0)
        self.assertIsInstance(chunks[0], str)
