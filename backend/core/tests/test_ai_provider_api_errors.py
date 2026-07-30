import json

import pytest
from django.test import RequestFactory

from diabetes.api.main import provider_error_handler
from llm.errors import (
    LLMProviderInternalFailure,
    LLMProviderMalformedResponse,
    LLMProviderQuotaExceeded,
    LLMProviderTimeout,
    LLMProviderUnavailable,
)


@pytest.mark.parametrize(
    ("exc", "status", "code", "retryable"),
    [
        (LLMProviderTimeout("gemini"), 503, "provider_timeout", True),
        (LLMProviderUnavailable("kimi"), 503, "provider_unavailable", True),
        (LLMProviderQuotaExceeded("gemini"), 429, "provider_quota_exceeded", False),
        (LLMProviderMalformedResponse("kimi"), 502, "provider_malformed_response", True),
        (LLMProviderInternalFailure("gemini"), 500, "provider_internal_failure", False),
    ],
)
def test_provider_errors_map_to_stable_non_sensitive_api_contract(
    exc,
    status,
    code,
    retryable,
):
    request = RequestFactory().get("/api/v1/ai/chat")
    response = provider_error_handler(request, exc)
    payload = json.loads(response.content)

    assert response.status_code == status
    assert payload == {
        "error": {
            "code": code,
            "message": exc.safe_message,
            "retryable": retryable,
        }
    }
    assert exc.provider not in response.content.decode()
