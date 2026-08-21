from __future__ import annotations

import pytest

from llm.cost_metrics import aggregate_cost_events, parse_cost_telemetry_lines


def test_aggregate_reports_route_rates_and_provider_reported_percentiles():
    events = [
        {"event": "companion_route", "route": "llm"},
        {"event": "companion_route", "route": "llm"},
        {"event": "companion_route", "route": "zero_model"},
        {"event": "companion_route", "route": "safety"},
        {
            "event": "llm_usage",
            "status": "success",
            "workload": "conversation",
            "provider_route": "provider-a",
            "from_cache": False,
            "prompt_chars": 900,
            "input_tokens": 100,
            "output_tokens": 20,
            "cached_input_tokens": 25,
            "total_tokens": 120,
        },
        {
            "event": "llm_usage",
            "status": "success",
            "workload": "conversation",
            "provider_route": "provider-a",
            "from_cache": True,
            "prompt_chars": 1200,
            "input_tokens": 200,
            "output_tokens": 30,
            "cached_input_tokens": 100,
            "total_tokens": 230,
        },
        {
            "event": "llm_usage",
            "status": "success",
            "workload": "summary",
            "provider_route": "provider-b",
            "from_cache": False,
            "prompt_chars": 1800,
            "input_tokens": 300,
            "output_tokens": 40,
            "cached_input_tokens": None,
            "total_tokens": 340,
        },
        {
            "event": "llm_usage",
            "status": "error",
            "workload": "conversation",
            "prompt_chars": 1000,
            "error_type": "TimeoutError",
        },
        {"event": "metered_usage", "modality": "ocr", "quantity": 2},
    ]

    report = aggregate_cost_events(events)

    assert report["interactions"] == 4
    assert report["route_counts"] == {"safety": 1, "zero_model": 1, "llm": 2}
    assert report["llm_call_rate_per_interaction"] == 0.5
    assert report["zero_model_rate_per_interaction"] == 0.25
    assert report["safety_rate_per_interaction"] == 0.25
    assert report["llm_success_events"] == 3
    assert report["llm_error_events"] == 1

    overall = report["overall"]
    assert overall["distributions"]["input_tokens"] == {
        "samples": 3,
        "coverage": 1.0,
        "p50": 200,
        "p95": 300,
    }
    assert overall["distributions"]["cached_input_tokens"] == {
        "samples": 2,
        "coverage": 2 / 3,
        "p50": 25,
        "p95": 100,
    }
    assert overall["cached_input_token_ratio"] == pytest.approx(125 / 300)
    assert overall["cache_ratio_sample_count"] == 2
    assert overall["from_cache_rate"] == pytest.approx(1 / 3)
    assert overall["provider_routes"] == {"provider-a": 2, "provider-b": 1}
    assert set(report["by_workload"]) == {"conversation", "summary"}
    assert report["cost_status"] == (
        "unavailable_without_reconciled_billing_and_stable_pricing"
    )


def test_missing_provider_tokens_remain_missing_not_zero():
    report = aggregate_cost_events(
        [
            {"event": "companion_route", "route": "llm"},
            {
                "event": "llm_usage",
                "status": "success",
                "workload": "conversation",
                "provider_route": "stream-provider",
                "from_cache": False,
                "prompt_chars": 700,
                "input_tokens": None,
                "output_tokens": None,
                "cached_input_tokens": None,
                "total_tokens": None,
            },
        ]
    )

    input_distribution = report["overall"]["distributions"]["input_tokens"]
    assert input_distribution == {
        "samples": 0,
        "coverage": 0.0,
        "p50": None,
        "p95": None,
    }
    assert report["overall"]["cached_input_token_ratio"] is None


def test_no_route_events_produce_unknown_rates_not_fake_zero():
    report = aggregate_cost_events([])

    assert report["interactions"] == 0
    assert report["llm_call_rate_per_interaction"] is None
    assert report["zero_model_rate_per_interaction"] is None
    assert report["safety_rate_per_interaction"] is None
    assert report["overall"]["distributions"]["input_tokens"]["coverage"] is None


def test_parser_extracts_prefixed_events_and_ignores_other_logs():
    lines = [
        "2026-08-21 INFO unrelated message\n",
        '2026-08-21 INFO cost_telemetry {"event":"companion_route","route":"llm"}\n',
        'cost_telemetry {"event":"llm_usage","status":"error","error_type":"X"}\n',
    ]

    assert parse_cost_telemetry_lines(lines) == [
        {"event": "companion_route", "route": "llm"},
        {"event": "llm_usage", "status": "error", "error_type": "X"},
    ]


def test_malformed_known_metrics_fail_closed():
    with pytest.raises(ValueError, match="unsupported companion route"):
        aggregate_cost_events([{"event": "companion_route", "route": "patient-42"}])

    with pytest.raises(ValueError, match="malformed cost telemetry JSON"):
        parse_cost_telemetry_lines(["cost_telemetry {not-json}\n"])
