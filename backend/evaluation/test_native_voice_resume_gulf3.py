from datetime import date

from evaluation.native_voice_batched_benchmark import (
    _select_scenarios,
    projected_spend_microusd,
)
from evaluation.native_voice_live_benchmark import (
    SPEND_CEILING_MICROUSD,
    load_native_voice_price,
)


def test_resume_selects_only_remaining_gulf_scenarios():
    selected = _select_scenarios(("kuwaiti", "qatari", "omani"))

    assert tuple(s.scenario_id for s in selected) == ("kuwaiti", "qatari", "omani")
    assert sum(len(s.turns) for s in selected) == 30


def test_resume_projected_spend_is_bounded():
    selected = _select_scenarios(("kuwaiti", "qatari", "omani"))
    price = load_native_voice_price(today=date(2026, 9, 26))
    projected = projected_spend_microusd(price, scenarios=selected)

    assert projected > 0
    assert projected <= SPEND_CEILING_MICROUSD


def test_resume_rejects_unknown_scenario():
    try:
        _select_scenarios(("unknown",))
    except RuntimeError as exc:
        assert "unknown scenario ids" in str(exc)
    else:
        raise AssertionError("unknown scenario must fail closed")
