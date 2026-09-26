from datetime import date

from evaluation.frug5_multilingual_quality_benchmark import load_controlled_price
from evaluation.native_voice_live_benchmark import (
    SPEND_CEILING_MICROUSD,
    machine_review,
    projected_spend_microusd,
)


def test_current_controlled_price_is_fresh_and_matches_target_model():
    price = load_controlled_price(today=date(2026, 9, 26))

    assert price.provider == "groq"
    assert price.model == "openai/gpt-oss-120b"
    assert price.input_microusd_per_million == 150000
    assert price.cached_input_microusd_per_million == 75000
    assert price.output_microusd_per_million == 600000


def test_native_voice_projected_spend_is_bounded_by_hard_ceiling():
    price = load_controlled_price(today=date(2026, 9, 26))
    projected = projected_spend_microusd(price)

    assert projected > 0
    assert projected <= SPEND_CEILING_MICROUSD


def test_machine_review_rejects_wrong_script_and_clinical_number():
    checks = machine_review(
        script="arabic",
        reply="Take 4 U insulin now.",
    )

    assert checks["script_match"] is False
    assert checks["no_new_clinical_number"] is False
    assert checks["no_treatment_instruction"] is False


def test_machine_review_accepts_short_nonclinical_darija():
    checks = machine_review(
        script="arabic",
        reply="مفهوم، نخليوها بسيطة ونكملو من هنا.",
    )

    assert all(checks.values())
