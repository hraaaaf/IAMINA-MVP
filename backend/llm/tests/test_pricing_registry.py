from datetime import date, timedelta

import pytest

from llm.pricing import PricingRegistry, PricingUnavailable, TextTokenPrice


def _price(*, due_offset_days: int = 30) -> TextTokenPrice:
    today = date(2026, 8, 18)
    return TextTokenPrice(
        provider="provider-a",
        model="model-a",
        currency="USD",
        input_microusd_per_million=1_000_000,
        cached_input_microusd_per_million=250_000,
        output_microusd_per_million=2_000_000,
        evidence_reference="controlled-pricing-fixture",
        verified_on=today,
        review_due_on=today + timedelta(days=due_offset_days),
    )


def test_registry_requires_one_exact_current_record():
    registry = PricingRegistry((_price(),))
    resolved = registry.resolve_text(
        provider="provider-a",
        model="model-a",
        today=date(2026, 8, 18),
    )
    assert resolved.model == "model-a"


def test_registry_rejects_missing_or_duplicate_records():
    with pytest.raises(PricingUnavailable):
        PricingRegistry(()).resolve_text(
            provider="provider-a",
            model="model-a",
            today=date(2026, 8, 18),
        )

    duplicate = _price()
    with pytest.raises(PricingUnavailable):
        PricingRegistry((duplicate, duplicate)).resolve_text(
            provider="provider-a",
            model="model-a",
            today=date(2026, 8, 18),
        )


def test_registry_rejects_stale_pricing():
    registry = PricingRegistry((_price(due_offset_days=-1),))
    with pytest.raises(PricingUnavailable, match="stale"):
        registry.resolve_text(
            provider="provider-a",
            model="model-a",
            today=date(2026, 8, 18),
        )


def test_worst_case_cost_rounds_up_and_does_not_assume_cache():
    price = _price()
    assert price.worst_case_microusd(input_tokens=1, output_tokens=1) == 3
    assert price.worst_case_microusd(input_tokens=1_000_000, output_tokens=1_000_000) == 3_000_000


def test_negative_prices_or_tokens_are_rejected():
    invalid = TextTokenPrice(
        provider="provider-a",
        model="model-a",
        currency="USD",
        input_microusd_per_million=-1,
        cached_input_microusd_per_million=None,
        output_microusd_per_million=1,
        evidence_reference="fixture",
        verified_on=date(2026, 8, 18),
        review_due_on=date(2026, 9, 18),
    )
    with pytest.raises(ValueError):
        invalid.validate(today=date(2026, 8, 18))

    with pytest.raises(ValueError):
        _price().worst_case_microusd(input_tokens=-1, output_tokens=1)
