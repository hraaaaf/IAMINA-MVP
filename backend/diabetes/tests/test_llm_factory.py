"""
LLM Factory — provider resolution tests.

Tests that `get_llm()` returns the correct provider type depending on
the LLM_PROVIDER setting, without making any real API calls.
"""
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

    @override_settings(LLM_PROVIDER="gemini")
    def test_gemini_provider_uses_central_runtime_guard(self):
        """Gemini stays directly visible so persistent FinOps can observe 429s."""
        from llm.factory import get_llm
        from llm.gemini import GeminiProvider
        from llm.rate_guard import GuardedGeminiProvider

        with patch("llm.rate_guard.should_use_gemini", return_value=True):
            provider = get_llm()

        self.assertIsInstance(provider, GeminiProvider)
        self.assertNotIsInstance(provider, GuardedGeminiProvider)
        self.assertTrue(getattr(provider, "_iamina_text_payload_policy", False))

    @override_settings(LLM_PROVIDER="gemini")
    def test_gemini_cap_hit_returns_local_quota_exhausted(self):
        """When Gemini daily cap is hit, the factory stays local and deterministic."""
        from llm.factory import get_llm
        with patch("llm.rate_guard.should_use_gemini", return_value=False):
            provider = get_llm()
        self.assertIsInstance(provider, QuotaExhaustedProvider)


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
