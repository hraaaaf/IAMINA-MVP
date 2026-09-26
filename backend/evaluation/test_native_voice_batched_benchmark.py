from datetime import date

from evaluation.native_voice_batched_benchmark import (
    MAX_OUTPUT_TOKENS_PER_SCENARIO,
    machine_review,
    projected_spend_microusd,
    strict_response_format,
)
from evaluation.native_voice_live_benchmark import (
    SPEND_CEILING_MICROUSD,
    load_native_voice_price,
)
from evaluation.native_voice_shadow_benchmark import SCENARIOS


def test_batched_strategy_reduces_provider_calls_tenfold():
    assert len(SCENARIOS) == 7
    assert sum(len(s.turns) for s in SCENARIOS) == 70


def test_batched_projected_spend_stays_under_existing_hard_ceiling():
    price = load_native_voice_price(today=date(2026, 9, 26))
    projected = projected_spend_microusd(price)

    assert projected > 0
    assert projected <= SPEND_CEILING_MICROUSD


def test_structured_output_requires_exact_reply_count():
    scenario = SCENARIOS[0]
    turn_ids = tuple(turn.turn_id for turn in scenario.turns)
    schema = strict_response_format(turn_ids)
    items = schema["json_schema"]["schema"]["properties"]["replies"]

    assert items["minItems"] == 10
    assert items["maxItems"] == 10
    assert MAX_OUTPUT_TOKENS_PER_SCENARIO == 1200


def test_machine_review_keeps_same_safety_shape():
    checks = machine_review(
        script="arabic",
        reply="مفهوم، نكملو بهدوء من نفس النقطة.",
    )

    assert all(checks.values())
