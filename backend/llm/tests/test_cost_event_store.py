from datetime import timedelta

import pytest
from django.utils import timezone

from core.finops_events import FinOpsTelemetryEvent
from llm.cost_event_store import load_cost_events, persist_cost_event, validate_cost_event
from llm.cost_metrics import aggregate_cost_events

pytestmark = pytest.mark.django_db


def test_persist_and_load_anonymous_cost_events() -> None:
    assert persist_cost_event({"event": "companion_route", "route": "llm"}) is True
    assert persist_cost_event(
        {
            "event": "llm_usage",
            "status": "success",
            "workload": "conversation",
            "provider_route": "openai/gpt-oss-120b",
            "from_cache": False,
            "prompt_chars": 1200,
            "response_chars": 120,
            "latency_ms": 42.0,
            "input_tokens": 300,
            "output_tokens": 30,
            "cached_input_tokens": None,
            "total_tokens": 330,
        }
    ) is True

    now = timezone.now()
    events = load_cost_events(start=now - timedelta(minutes=1), end=now + timedelta(minutes=1))
    report = aggregate_cost_events(events)

    assert report["interactions"] == 1
    assert report["llm_call_rate_per_interaction"] == 1.0
    assert report["zero_model_rate_per_interaction"] == 0.0
    assert report["overall"]["distributions"]["input_tokens"]["p50"] == 300
    assert report["overall"]["distributions"]["input_tokens"]["p95"] == 300
    assert report["overall"]["distributions"]["cached_input_tokens"]["p50"] is None


def test_missing_interaction_denominator_remains_unavailable() -> None:
    assert persist_cost_event(
        {
            "event": "llm_usage",
            "status": "success",
            "workload": "conversation",
            "provider_route": "openai/gpt-oss-120b",
            "from_cache": False,
            "prompt_chars": 100,
            "response_chars": 20,
            "latency_ms": 10.0,
            "input_tokens": 10,
            "output_tokens": 5,
            "cached_input_tokens": None,
            "total_tokens": 15,
        }
    ) is True
    now = timezone.now()
    report = aggregate_cost_events(
        load_cost_events(start=now - timedelta(minutes=1), end=now + timedelta(minutes=1))
    )
    assert report["interactions"] == 0
    assert report["llm_call_rate_per_interaction"] is None
    assert report["zero_model_rate_per_interaction"] is None


def test_non_allowlisted_payload_is_rejected_and_not_persisted() -> None:
    event = {
        "event": "companion_route",
        "route": "llm",
        "patient_id": 123,
    }
    with pytest.raises(ValueError, match="non-allowlisted"):
        validate_cost_event(event)
    assert persist_cost_event(event) is False
    assert FinOpsTelemetryEvent.objects.count() == 0


def test_free_text_is_rejected() -> None:
    assert persist_cost_event(
        {
            "event": "llm_usage",
            "status": "error",
            "workload": "conversation",
            "prompt_chars": 10,
            "latency_ms": 1.0,
            "error_type": "contains patient name here",
        }
    ) is False
    assert FinOpsTelemetryEvent.objects.count() == 0


def test_reporting_window_must_be_timezone_aware_and_ordered() -> None:
    now = timezone.now()
    with pytest.raises(ValueError, match="start must be before end"):
        load_cost_events(start=now, end=now)
