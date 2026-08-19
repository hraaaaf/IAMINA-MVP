import json
import logging

import pytest

from llm.base import LLMResponse, LLMUsage
from llm.middleware.logging import LoggingMiddleware
from llm.usage_telemetry import (
    record_media_bytes,
    record_metered_usage,
    usage_workload_scope,
)


def _events_from_caplog(caplog):
    prefix = "cost_telemetry "
    return [
        json.loads(record.message[len(prefix) :])
        for record in caplog.records
        if record.name == "iamina.cost" and record.message.startswith(prefix)
    ]


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
    event = _events_from_caplog(caplog)[0]
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

    event = _events_from_caplog(caplog)[0]
    assert event["status"] == "error"
    assert event["workload"] == "summary"
    assert event["error_type"] == "RuntimeError"
    assert "SECRET_PROVIDER_ERROR_BODY" not in caplog.text


def test_metered_and_media_events_are_content_free(caplog):
    with caplog.at_level(logging.INFO, logger="iamina.cost"):
        with usage_workload_scope("ocr"):
            record_metered_usage(
                modality="ocr",
                unit="page",
                quantity=3,
                provider_route="mistral-ocr",
                latency_ms=420.25,
            )
            record_media_bytes(
                action="uploaded",
                byte_count=700_000,
                retention_class="TRANSIENT_EXTRACTION",
            )
            record_media_bytes(
                action="deleted",
                byte_count=700_000,
                retention_class="TRANSIENT_EXTRACTION",
            )

    events = _events_from_caplog(caplog)
    assert events[0] == {
        "event": "metered_usage",
        "latency_ms": 420.2,
        "modality": "ocr",
        "provider_route": "mistral-ocr",
        "quantity": 3,
        "status": "success",
        "unit": "page",
        "workload": "ocr",
    }
    assert events[1]["event"] == "media_bytes"
    assert events[1]["action"] == "uploaded"
    assert events[2]["action"] == "deleted"
    assert all(event.get("bytes") in (None, 700_000) for event in events)


def test_workload_and_metered_contracts_fail_closed():
    with pytest.raises(ValueError, match="unsupported cost workload"):
        with usage_workload_scope("patient-42"):
            pass

    with pytest.raises(ValueError, match="unsupported cost workload"):
        with usage_workload_scope("unclassified"):
            pass

    with pytest.raises(ValueError, match="unsupported metered modality"):
        record_metered_usage(
            modality="database",
            unit="query",
            quantity=1,
            provider_route="db",
        )

    with pytest.raises(ValueError, match="byte_count cannot be negative"):
        record_media_bytes(
            action="retained",
            byte_count=-1,
            retention_class="TRANSIENT_EXTRACTION",
        )
