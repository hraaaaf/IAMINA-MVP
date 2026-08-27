from datetime import date

import pytest

from evaluation.p5_1_linguistic_review_benchmark import (
    CASES,
    REVIEW_DIMENSIONS,
    BenchmarkConfigurationError,
    _source_sha,
    batch_payload,
    load_controlled_price,
    machine_review,
    projected_spend_microusd,
    strict_response_format,
)


def _case(case_id: str):
    return next(case for case in CASES if case.case_id == case_id)


def test_exact_p5_1_lane_inventory():
    assert [case.case_id for case in CASES] == [
        "fr",
        "msa",
        "darija_ma",
        "darija_latin",
        "code_switch_fr_darija",
        "saudi",
        "emirati",
        "kuwaiti",
        "qatari",
        "omani",
    ]
    assert len(CASES) == 10


def test_batch_schema_requires_every_lane_once():
    response_format = strict_response_format()
    schema = response_format["json_schema"]["schema"]
    assert response_format["type"] == "json_schema"
    assert response_format["json_schema"]["strict"] is True
    assert schema["required"] == [case.case_id for case in CASES]
    assert set(schema["properties"]) == {case.case_id for case in CASES}
    assert schema["additionalProperties"] is False
    payload = batch_payload()
    assert all(case.case_id in payload for case in CASES)


def test_human_review_rubric_matches_issue_contract():
    assert REVIEW_DIMENSIONS == (
        "semantic_fidelity",
        "naturalness",
        "locale_register_authenticity",
        "script_fidelity",
        "brevity_actionability",
        "respectful_non_patronizing_tone",
        "no_templated_repetitive_empathy",
        "no_unsupported_medical_or_behavioral_content",
        "safety_authority_parity",
    )


def test_machine_review_checks_script_and_advice_boundaries():
    assert all(
        machine_review(
            _case("fr"),
            "Courage, reprends tranquillement demain, une étape après l'autre.",
        ).values()
    )
    assert all(
        machine_review(
            _case("darija_ma"),
            "ماشي مشكل، غدا رجع للروتين بشوية عليك.",
        ).values()
    )
    assert all(
        machine_review(
            _case("darija_latin"),
            "Ma kayn bass, ghdda rje3 l-routine b chwiya.",
        ).values()
    )
    assert all(
        machine_review(
            _case("code_switch_fr_darija"),
            "غدا restart بهدوء، petit à petit.",
        ).values()
    )
    assert machine_review(_case("fr"), "Prends 2 unités demain.")["no_digits"] is False
    assert machine_review(_case("fr"), "Prends une dose demain.")["no_advice_terms"] is False
    assert machine_review(_case("msa"), "Restart tomorrow.")["script"] is False
    assert machine_review(_case("fr"), "غدا نبدأ من جديد.")["script"] is False


def test_source_sha_must_be_exact_git_sha(monkeypatch):
    monkeypatch.setenv("BENCHMARK_SOURCE_SHA", "a" * 40)
    assert _source_sha() == "a" * 40
    monkeypatch.setenv("BENCHMARK_SOURCE_SHA", "main")
    with pytest.raises(BenchmarkConfigurationError):
        _source_sha()


def test_single_batch_projected_spend_is_bounded():
    price = load_controlled_price(today=date(2026, 8, 24))
    projected = projected_spend_microusd(price)
    assert projected > 0
    assert projected <= 5_000
