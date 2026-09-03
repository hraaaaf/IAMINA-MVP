from datetime import date

from companion.narrator_prompts import get_language_label
from evaluation.frug5_multilingual_quality_benchmark import load_controlled_price
from evaluation.frug5_product_prompt_gulf_benchmark import (
    _GULF_CASES,
    _GULF_LOCALES,
    _gpt_oss_request_tuning,
    _system_prompt,
    _user_prompt,
    projected_spend_microusd,
)
from llm.lowcost_openai_compatible import _GPT_OSS_MAX_OUTPUT_TOKENS


def test_gulf_product_prompt_uses_exact_runtime_language_labels():
    assert [case.case_id for case in _GULF_CASES] == [
        "saudi",
        "emirati",
        "kuwaiti",
        "qatari",
        "omani",
    ]
    for case in _GULF_CASES:
        code = _GULF_LOCALES[case.case_id]
        label = get_language_label(code)
        system = _system_prompt(case.case_id)
        assert label in system
        assert "تجنب الفصحى الرسمية" in label
        assert "NARRATEUR" in system
        assert "diagnostic" in system
        assert "dose" in system
        assert "n'autorise JAMAIS à inventer une action santé/comportementale" in system
        assert "activité physique, alimentation, sommeil et hydratation" in system


def test_gulf_product_user_prompt_is_synthetic_and_contains_case_message():
    for case in _GULF_CASES:
        prompt = _user_prompt(case)
        assert case.text in prompt
        assert "Aucune donnée relationnelle mémorisée" in prompt
        assert "Message du patient" in prompt


def test_gulf_product_prompt_transport_matches_runtime_gpt_oss_contract():
    tuning = _gpt_oss_request_tuning()
    assert "max_tokens" not in tuning
    assert tuning["max_completion_tokens"] == _GPT_OSS_MAX_OUTPUT_TOKENS
    assert tuning["reasoning_effort"] == "low"
    assert tuning["extra_body"] == {"reasoning_format": "hidden"}
    response_format = tuning["response_format"]
    assert response_format["type"] == "json_schema"
    assert response_format["json_schema"]["strict"] is True


def test_product_prompt_gulf_live_sample_stays_under_explicit_spend_ceiling():
    price = load_controlled_price(today=date(2026, 8, 24))
    projected = projected_spend_microusd(price)
    assert projected > 0
    assert projected <= 5_000
