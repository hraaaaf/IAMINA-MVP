from evaluation.frug5_multilingual_quality_benchmark import CASES as REFERENCE_CASES
from evaluation.provider_multilingual_comparison import (
    CONTROL_PROVIDER_ID,
    NEW_PROVIDER_IDS,
    ProviderSpec,
    latency_summary,
    list_price_equivalent_microusd,
    load_provider_specs,
    projected_spend_microusd,
    resolve_credentials,
)


def test_comparison_reuses_exact_retained_ten_locale_corpus():
    assert [case.case_id for case in REFERENCE_CASES] == [
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


def test_controlled_provider_matrix_is_exact_and_current():
    specs = load_provider_specs()
    assert {spec.provider_id for spec in specs} == NEW_PROVIDER_IDS | {
        CONTROL_PROVIDER_ID
    }
    assert {spec.verified_on for spec in specs} == {"2026-08-26"}
    by_id = {spec.provider_id: spec for spec in specs}
    assert by_id["deepinfra"].input_microusd_per_million == 37_000
    assert by_id["deepinfra"].output_microusd_per_million == 170_000
    assert by_id["together"].input_microusd_per_million == 150_000
    assert by_id["cloudflare"].input_microusd_per_million == 350_000
    assert by_id["groq"].cached_input_microusd_per_million == 75_000


def test_missing_credentials_are_skipped_not_inferred():
    deepinfra = next(
        spec for spec in load_provider_specs() if spec.provider_id == "deepinfra"
    )
    assert resolve_credentials(deepinfra, {}) == (None, None, "missing_api_key")
    key, base_url, reason = resolve_credentials(
        deepinfra,
        {"DEEPINFRA_TOKEN": "controlled-token"},
    )
    assert key == "controlled-token"
    assert base_url == "https://api.deepinfra.com/v1/openai"
    assert reason is None


def test_cloudflare_requires_account_id_separately_from_token():
    cloudflare = next(
        spec for spec in load_provider_specs() if spec.provider_id == "cloudflare"
    )
    assert resolve_credentials(
        cloudflare,
        {"CLOUDFLARE_API_TOKEN": "controlled-token"},
    ) == (None, None, "missing_account_id")
    key, base_url, reason = resolve_credentials(
        cloudflare,
        {
            "CLOUDFLARE_API_TOKEN": "controlled-token",
            "CLOUDFLARE_ACCOUNT_ID": "account-123",
        },
    )
    assert key == "controlled-token"
    assert base_url == (
        "https://api.cloudflare.com/client/v4/accounts/account-123/ai/v1"
    )
    assert reason is None


def test_list_price_uses_cached_rate_only_when_provider_reports_cache():
    spec = ProviderSpec(
        provider_id="test",
        model="model",
        base_url="https://example.test/v1",
        api_key_envs=("KEY",),
        input_microusd_per_million=100_000,
        cached_input_microusd_per_million=50_000,
        output_microusd_per_million=200_000,
        evidence_reference="https://example.test/pricing",
        verified_on="2026-08-26",
    )
    assert list_price_equivalent_microusd(
        spec,
        {"input_tokens": 1000, "cached_input_tokens": 400, "output_tokens": 100},
    ) == 100
    assert list_price_equivalent_microusd(
        spec,
        {"input_tokens": 1000, "cached_input_tokens": None, "output_tokens": 100},
    ) == 120


def test_latency_and_projected_spend_are_bounded_without_network():
    assert latency_summary([100, 200, 300, 400]) == {
        "successful_calls": 4,
        "p50_ms": 250.0,
        "p95_ms": 400,
    }
    assert latency_summary([]) == {
        "successful_calls": 0,
        "p50_ms": None,
        "p95_ms": None,
    }
    for spec in load_provider_specs():
        assert 0 < projected_spend_microusd(spec) <= 20_000
