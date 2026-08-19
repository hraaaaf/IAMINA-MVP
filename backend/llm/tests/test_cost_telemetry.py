import json
import logging

import pytest

from llm.base import LLMResponse, LLMUsage
from llm.middleware.logging import LoggingMiddleware
from llm.usage_telemetry import usage_workload_scope


def _event_from_caplog(caplog):
    record = next(record for record in caplog.records if record.name == "iamina.cost")
    prefix = "cost_telemetry "
    assert record.message.startswith(prefix)
    return json.loads(record.message[len(prefix) :])


def test_cost_telemetry_records_scoped_usage_without_content(caplog):
    middleware = LoggingMiddleware()
    response = LLMResponse(
        content="SECRET_RESPONSE_TEXT",
        provider="gpt-oss-120b",
        usage=LLMUsage(
            input_tokens=120,
            output_tokens=18,
            cached_input_tokens=80,
            total_tokens=138,
        ),
    )

    with caplog.at_level(logging.INFO, logger="iamina.cost"):
        with usage_workload_scope("conversation"):
            result = middleware.process(
                "SECRET_SYSTEM_TEXT",
                "SECRET_USER_TEXT",
                lambda _system, _user: response,
            )

    assert result is response
    event = _event_from_caplog(caplog)
    assert event == {
        "cached_input_tokens": 80,
        "event": "llm_usage",
        "from_cache": False,
        "input_tokens": 120,
        "latency_ms": event["latency_ms"],
        "output_tokens": 18,
        "prompt_chars": len("SECRET_SYSTEM_TEXTSECRET_USER_TEXT"),
        "provider_route": "gpt-oss-120b",
        "response_chars": len("SECRET_RESPONSE_TEXT"),
        "status": "success",
        "total_tokens": 138,
        "workload": "conversation",
    }
    assert event["latency_ms"] >= 0
    assert "SECRET_SYSTEM_TEXT" not in caplog.text
    assert "SECRET_USER_TEXT" not in caplog.text
    assert "SECRET_RESPONSE_TEXT" not in caplog.text


def test_cost_telemetry_records_error_type_not_exception_message(caplog):
    middleware = LoggingMiddleware()

    def fail(_system, _user):
        raise RuntimeError("SECRET_PROVIDER_ERROR_BODY")

    with caplog.at_level(logging.INFO, logger="iamina.cost"):
        with usage_workload_scope("summary"):
            with pytest.raises(RuntimeError, match="SECRET_PROVIDER_ERROR_BODY"):
                middleware.process("safe", "input", fail)

    event = _event_from_caplog(caplog)
    assert event["status"] == "error"
    assert event["workload"] == "summary"
    assert event["error_type"] == "RuntimeError"
    assert "SECRET_PROVIDER_ERROR_BODY" not in caplog.text


def test_workload_scope_rejects_unknown_or_unclassified_values():
    with pytest.raises(ValueError, match="unsupported cost workload"):
        with usage_workload_scope("patient-42"):
            pass

    with pytest.raises(ValueError, match="unsupported cost workload"):
        with usage_workload_scope("unclassified"):
            pass
