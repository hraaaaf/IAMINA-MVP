from datetime import date
from unittest.mock import patch

from companion.conversation import chat
from evaluation.frug5_companion_benchmark import (
    BASELINE_HISTORY_BUDGET,
    CURRENT_HISTORY_BUDGET,
    SPEND_CEILING_MICROUSD,
    DeepStub,
    MemoryStub,
    _projected_spend_microusd,
    _recent_turns_stub,
    build_prompt_for_case,
    load_controlled_price,
    synthetic_history,
    validate_route_corpus,
)
from llm.base import LLMResponse, LLMUsage


class FakeLLM:
    def __init__(self):
        self.calls = 0

    def complete(self, _system, _user):
        self.calls += 1
        return LLMResponse(
            content='{"reply":"Synthetic routine reply."}',
            provider="fake",
            usage=LLMUsage(
                input_tokens=100,
                output_tokens=10,
                cached_input_tokens=0,
                total_tokens=110,
            ),
        )


def test_route_corpus_resolves_expected_without_network():
    cases = validate_route_corpus()

    assert [case.expected_route for case in cases] == [
        "zero_model",
        "zero_model",
        "safety",
        "safety",
        "llm",
        "llm",
        "llm",
        "llm",
    ]


def test_current_history_budget_builds_smaller_live_prompt_than_baseline():
    llm_cases = tuple(
        case for case in validate_route_corpus() if case.expected_route == "llm"
    )

    for case in llm_cases:
        current_system, current_user = build_prompt_for_case(
            case,
            history_budget=CURRENT_HISTORY_BUDGET,
        )
        baseline_system, baseline_user = build_prompt_for_case(
            case,
            history_budget=BASELINE_HISTORY_BUDGET,
        )

        assert current_system == baseline_system
        assert len(current_user) < len(baseline_user)


def test_full_companion_path_stubs_are_complete_without_network():
    fake = FakeLLM()
    history = synthetic_history()

    for case in validate_route_corpus():
        with patch(
            "companion.conversation._recent_turns",
            side_effect=_recent_turns_stub(history),
        ):
            reply = chat(
                case.message,
                memory=MemoryStub(),
                deep=DeepStub(),
                llm=fake,
                language=case.language,
                patient=None,
            )
        assert reply

    assert fake.calls == 4


def test_projected_spend_stays_inside_explicit_ceiling():
    price = load_controlled_price(today=date(2026, 8, 22))
    llm_cases = tuple(
        case for case in validate_route_corpus() if case.expected_route == "llm"
    )

    projected = _projected_spend_microusd(llm_cases, price)

    assert 0 < projected <= SPEND_CEILING_MICROUSD


def test_controlled_price_matches_live_candidate_and_is_current():
    price = load_controlled_price(today=date(2026, 8, 22))

    assert price.provider == "groq"
    assert price.model == "openai/gpt-oss-120b"
    assert price.input_microusd_per_million == 150_000
    assert price.cached_input_microusd_per_million == 75_000
    assert price.output_microusd_per_million == 600_000
