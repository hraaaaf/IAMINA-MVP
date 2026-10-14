"""Offline smoke tests for the pinned Google Gen AI client interface.

This verifies installed SDK wiring, not an authorized clinical AI call.
Never supply real patient content, credentials or perform HTTP here.
"""
from google import genai

from llm.gemini import GeminiProvider


def test_genai_pinned_sdk_supports_existing_gemini_adapter(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "synthetic-no-network-test-key")
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    provider = GeminiProvider(model="synthetic-model-do-not-call")
    try:
        assert provider.model_name == "synthetic-model-do-not-call"
        assert provider._client is not None
        assert callable(provider._client.models.generate_content)
        assert callable(provider._client.models.generate_content_stream)
        # The constructor accepts the adapter's v1alpha client options.
        assert isinstance(provider._client, genai.Client)
    finally:
        if provider._client is not None:
            provider._client.close()
        provider._executor.shutdown(wait=True)
