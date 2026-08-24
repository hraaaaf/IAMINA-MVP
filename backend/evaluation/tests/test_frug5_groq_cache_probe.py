from datetime import date

import pytest

from evaluation.frug5_groq_cache_probe import (
    _PROBE_CALLS,
    projected_spend_microusd,
    request_body,
    shared_prefix,
    usage_cache_row,
)
from evaluation.frug5_multilingual_quality_benchmark import load_controlled_price


def test_raw_cache_probe_uses_three_identical_bounded_requests():
    assert _PROBE_CALLS == 3
    body1 = request_body()
    body2 = request_body()
    assert body1 == body2
    assert body1["max_tokens"] == 64
    assert body1["reasoning_effort"] == "low"
    assert "Synthetic cache probe" in body1["messages"][1]["content"]
    assert len(shared_prefix()) > 6_000


@pytest.mark.parametrize(
    ("details", "present", "cached", "ratio"),
    [
        ({}, False, None, None),
        ({"cached_tokens": None}, True, None, None),
        ({"cached_tokens": 0}, True, 0, 0.0),
        ({"cached_tokens": 800}, True, 800, 0.5),
    ],
)
def test_usage_cache_row_preserves_absent_null_zero_and_hit(
    details, present, cached, ratio
):
    raw = {
        "usage": {
            "prompt_tokens": 1600,
            "completion_tokens": 10,
            "total_tokens": 1610,
            "prompt_tokens_details": details,
        }
    }
    row = usage_cache_row(raw)
    assert row["cached_field_present"] is present
    assert row["cached_input_tokens"] == cached
    assert row["cache_ratio"] == ratio


def test_raw_cache_probe_stays_under_explicit_spend_ceiling():
    price = load_controlled_price(today=date(2026, 8, 24))
    projected = projected_spend_microusd(price)
    assert projected > 0
    assert projected <= 5_000
