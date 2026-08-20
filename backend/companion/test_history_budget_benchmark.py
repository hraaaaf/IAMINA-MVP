from math import ceil
from statistics import median
from types import SimpleNamespace

import pytest

from companion.conversation import _trim_history
from companion.zero_model_router import exact_chitchat_reply

_BASELINE_BUDGET = 3000
_CANDIDATE_BUDGET = 1800

_FIXTURES = {
    "fr": (
        "Je préfère recevoir les rappels en français.",
        "ancien contexte sans autorité clinique ",
    ),
    "ar": (
        "أفضل أن تكون التذكيرات باللغة العربية.",
        "سياق قديم غير سريري ",
    ),
    "en": (
        "I prefer reminders in English.",
        "old non-clinical context ",
    ),
    "gulf": (
        "الحين أفضل التذكيرات باللهجة الخليجية.",
        "سياق قديم مو سريري ",
    ),
}

_EXPECTED_CHAR_COUNTS = {
    "fr": (2379, 1329),
    "ar": (2359, 1453),
    "en": (2337, 1385),
    "gulf": (2351, 1397),
}


def _history_turns(anchor: str, filler: str):
    turns = [
        SimpleNamespace(role="user", message=anchor),
        SimpleNamespace(role="assistant", message="Ack recent."),
    ]
    for index in range(12):
        turns.extend(
            [
                SimpleNamespace(
                    role="user",
                    message=f"{filler} #{index} " + filler * 4,
                ),
                SimpleNamespace(
                    role="assistant",
                    message=f"Old answer #{index}. " + filler * 3,
                ),
            ]
        )
    return turns


def _nearest_rank(values: list[int], percentile: float) -> int:
    ordered = sorted(values)
    return ordered[ceil(percentile * len(ordered)) - 1]


@pytest.mark.parametrize("language", ("fr", "ar", "en", "gulf"))
def test_candidate_history_budget_reduces_chars_and_preserves_latest_anchor(language):
    anchor, filler = _FIXTURES[language]
    turns = _history_turns(anchor, filler)

    baseline = _trim_history(turns, _BASELINE_BUDGET)
    candidate = _trim_history(turns, _CANDIDATE_BUDGET)

    assert (len(baseline), len(candidate)) == _EXPECTED_CHAR_COUNTS[language]
    assert anchor in baseline
    assert anchor in candidate
    assert len(candidate) < len(baseline)
    assert len(candidate) <= _CANDIDATE_BUDGET


def test_candidate_history_budget_improves_char_p50_and_p95_preflight():
    baseline = [values[0] for values in _EXPECTED_CHAR_COUNTS.values()]
    candidate = [values[1] for values in _EXPECTED_CHAR_COUNTS.values()]

    assert median(baseline) == 2355
    assert median(candidate) == 1391
    assert _nearest_rank(baseline, 0.95) == 2379
    assert _nearest_rank(candidate, 0.95) == 1453


def test_zero_model_scope_stays_exact_and_does_not_absorb_open_health_questions():
    assert exact_chitchat_reply("merci", "fr") is not None
    assert exact_chitchat_reply("Salut", "fr") is not None
    assert exact_chitchat_reply("Pourquoi ma glycémie varie après le repas ?", "fr") is None
    assert exact_chitchat_reply("ليش السكر يتغير بعد الأكل؟", "ar") is None
