from datetime import date

from evaluation.frug5_multilingual_quality_benchmark import CASES as GROQ_REFERENCE_CASES
from evaluation.mistral_multilingual_quality_benchmark import (
    CASES,
    MODEL,
    PROVIDER,
    SPEND_CEILING_MICROUSD,
    latency_summary,
    load_controlled_price,
    projected_spend_microusd,
)


def test_mistral_benchmark_reuses_exact_ten_locale_reference_corpus():
    assert CASES is GROQ_REFERENCE_CASES
    assert [case.case_id for case in CASES] == [
        "fr",
        "en",
        "msa",
        "darija_ma",
        "saudi",
        "emirati",
        "kuwaiti",
        "qatari",
        "omani",
        "code_switch_fr_darija",
    ]


def test_mistral_small4_controlled_price_matches_verified_model():
    price = load_controlled_price(today=date(2026, 8, 25))
    assert PROVIDER == "mistral"
    assert MODEL == "mistral-small-2603"
    assert price.provider == PROVIDER
    assert price.model == MODEL
    assert price.input_microusd_per_million == 150_000
    assert price.output_microusd_per_million == 600_000
    assert price.cached_input_microusd_per_million is None


def test_ten_call_projected_list_price_equivalent_is_bounded():
    price = load_controlled_price(today=date(2026, 8, 25))
    projected = projected_spend_microusd(price)
    assert projected > 0
    assert projected <= SPEND_CEILING_MICROUSD


def test_latency_summary_uses_nearest_rank_p95_and_median_p50():
    summary = latency_summary([100, 200, 300, 400, 500, 600, 700, 800, 900, 1000])
    assert summary == {"successful_calls": 10, "p50_ms": 550.0, "p95_ms": 1000}
    assert latency_summary([]) == {
        "successful_calls": 0,
        "p50_ms": None,
        "p95_ms": None,
    }
