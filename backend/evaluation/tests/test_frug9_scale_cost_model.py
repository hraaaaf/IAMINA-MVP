from decimal import Decimal

import pytest

from evaluation.frug9_scale_cost_model import (
    SCALE_TIERS,
    EvidenceValue,
    ScalePriceInputs,
    ScaleUsageInputs,
    build_scale_scaffold,
)


def ev(value: str, *, kind: str = "measured", source: str = "fixture") -> EvidenceValue:
    return EvidenceValue(Decimal(value), kind, source)  # type: ignore[arg-type]


def complete_usage() -> ScaleUsageInputs:
    return ScaleUsageInputs(
        interactions_per_mau=ev("20"),
        llm_calls_per_interaction=ev("0.4"),
        llm_input_tokens_per_call=ev("500"),
        llm_output_tokens_per_call=ev("80"),
        cloud_ocr_pages_per_mau=ev("0.2"),
        storage_gb_month_per_mau=ev("0.01"),
        egress_gb_per_mau=ev("0.02"),
    )


def complete_prices() -> ScalePriceInputs:
    return ScalePriceInputs(
        llm_input_microusd_per_million_tokens=ev("100000"),
        llm_output_microusd_per_million_tokens=ev("200000"),
        cloud_ocr_microusd_per_page=ev("500"),
        storage_microusd_per_gb_month=ev("23000"),
        egress_microusd_per_gb=ev("90000"),
        fixed_monthly_microusd=ev("1000000"),
    )


def test_builds_exact_canonical_scale_tiers() -> None:
    scaffold = build_scale_scaffold(complete_usage(), complete_prices())

    assert tuple(tier.mau for tier in scaffold.tiers) == SCALE_TIERS
    assert scaffold.fully_costed is True
    assert all(tier.total_cost_microusd is not None for tier in scaffold.tiers)
    assert all(tier.cost_per_mau_microusd is not None for tier in scaffold.tiers)


def test_missing_price_remains_unavailable_instead_of_becoming_zero() -> None:
    prices = complete_prices()
    prices = ScalePriceInputs(
        llm_input_microusd_per_million_tokens=prices.llm_input_microusd_per_million_tokens,
        llm_output_microusd_per_million_tokens=prices.llm_output_microusd_per_million_tokens,
        cloud_ocr_microusd_per_page=prices.cloud_ocr_microusd_per_page,
        storage_microusd_per_gb_month=prices.storage_microusd_per_gb_month,
        egress_microusd_per_gb=None,
        fixed_monthly_microusd=prices.fixed_monthly_microusd,
    )

    scaffold = build_scale_scaffold(complete_usage(), prices)
    tier = scaffold.tiers[0]

    assert tier.egress_cost_microusd is None
    assert tier.total_cost_microusd is None
    assert tier.cost_per_mau_microusd is None
    assert "egress_microusd_per_gb" in tier.unresolved_inputs
    assert scaffold.fully_costed is False


def test_explicit_measured_zero_is_distinct_from_missing() -> None:
    usage = complete_usage()
    usage = ScaleUsageInputs(
        interactions_per_mau=usage.interactions_per_mau,
        llm_calls_per_interaction=usage.llm_calls_per_interaction,
        llm_input_tokens_per_call=usage.llm_input_tokens_per_call,
        llm_output_tokens_per_call=usage.llm_output_tokens_per_call,
        cloud_ocr_pages_per_mau=usage.cloud_ocr_pages_per_mau,
        storage_gb_month_per_mau=usage.storage_gb_month_per_mau,
        egress_gb_per_mau=ev("0"),
    )

    tier = build_scale_scaffold(usage, complete_prices()).tiers[0]

    assert tier.egress_cost_microusd == Decimal(0)
    assert "egress_gb_per_mau" not in tier.unresolved_inputs
    assert tier.total_cost_microusd is not None


def test_scenario_inputs_are_retained_as_scenario_evidence() -> None:
    usage = complete_usage()
    usage = ScaleUsageInputs(
        interactions_per_mau=ev("20", kind="scenario", source="load scenario A"),
        llm_calls_per_interaction=usage.llm_calls_per_interaction,
        llm_input_tokens_per_call=usage.llm_input_tokens_per_call,
        llm_output_tokens_per_call=usage.llm_output_tokens_per_call,
        cloud_ocr_pages_per_mau=usage.cloud_ocr_pages_per_mau,
        storage_gb_month_per_mau=usage.storage_gb_month_per_mau,
        egress_gb_per_mau=usage.egress_gb_per_mau,
    )

    tier = build_scale_scaffold(usage, complete_prices()).tiers[0]

    assert tier.evidence_kinds == ("measured", "scenario")
    assert tier.fully_costed is True


def test_variable_costs_scale_linearly_while_fixed_cost_does_not() -> None:
    scaffold = build_scale_scaffold(complete_usage(), complete_prices())
    one_k, ten_k = scaffold.tiers[0], scaffold.tiers[1]

    assert ten_k.llm_input_cost_microusd == one_k.llm_input_cost_microusd * 10
    assert ten_k.cloud_ocr_cost_microusd == one_k.cloud_ocr_cost_microusd * 10
    assert ten_k.fixed_cost_microusd == one_k.fixed_cost_microusd
    assert ten_k.total_cost_microusd != one_k.total_cost_microusd * 10


def test_invalid_evidence_fails_closed() -> None:
    with pytest.raises(ValueError, match="negative"):
        EvidenceValue(Decimal("-1"), "measured", "fixture")

    with pytest.raises(ValueError, match="source"):
        EvidenceValue(Decimal("1"), "measured", "  ")
