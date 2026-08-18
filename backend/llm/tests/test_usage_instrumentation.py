import logging
from types import SimpleNamespace

from llm.base import LLMResponse, LLMUsage
from llm.gemini import _usage_from_response as gemini_usage
from llm.kimi import _usage_from_response as kimi_usage
from llm.middleware.logging import LoggingMiddleware


def test_llm_response_remains_backward_compatible_without_usage():
    response = LLMResponse(content="ok", provider="synthetic")
    assert response.usage is None


def test_gemini_usage_reads_provider_reported_counts():
    response = SimpleNamespace(
        usage_metadata=SimpleNamespace(
            prompt_token_count=120,
            candidates_token_count=18,
            cached_content_token_count=80,
            total_token_count=138,
        )
    )
    assert gemini_usage(response) == LLMUsage(
        input_tokens=120,
        output_tokens=18,
        cached_input_tokens=80,
        total_tokens=138,
    )


def test_openai_compatible_usage_reads_cached_tokens_when_present():
    response = SimpleNamespace(
        usage=SimpleNamespace(
            prompt_tokens=90,
            completion_tokens=12,
            total_tokens=102,
            prompt_tokens_details=SimpleNamespace(cached_tokens=60),
        )
    )
    assert kimi_usage(response) == LLMUsage(
        input_tokens=90,
        output_tokens=12,
        cached_input_tokens=60,
        total_tokens=102,
    )


def test_logging_records_usage_without_prompt_or_response_content(caplog):
    middleware = LoggingMiddleware()
    response = LLMResponse(
        content="SECRET_RESPONSE_TEXT",
        provider="cheap-model",
        usage=LLMUsage(
            input_tokens=100,
            output_tokens=20,
            cached_input_tokens=70,
            total_tokens=120,
        ),
    )

    with caplog.at_level(logging.DEBUG, logger="llm.middleware.logging"):
        result = middleware.process(
            "SECRET_SYSTEM_TEXT",
            "SECRET_USER_TEXT",
            lambda _system, _user: response,
        )

    assert result is response
    logged = caplog.text
    assert "input_tokens=100" in logged
    assert "output_tokens=20" in logged
    assert "cached_input_tokens=70" in logged
    assert "SECRET_SYSTEM_TEXT" not in logged
    assert "SECRET_USER_TEXT" not in logged
    assert "SECRET_RESPONSE_TEXT" not in logged


def test_logging_does_not_guess_tokens_when_provider_omits_usage(caplog):
    middleware = LoggingMiddleware()
    with caplog.at_level(logging.DEBUG, logger="llm.middleware.logging"):
        middleware.process(
            "abc",
            "def",
            lambda _system, _user: LLMResponse(content="ok", provider="legacy"),
        )

    assert "input_tokens=None" in caplog.text
    assert "output_tokens=None" in caplog.text
