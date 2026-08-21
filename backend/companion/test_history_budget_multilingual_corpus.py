from __future__ import annotations

from math import ceil
from statistics import median
from types import SimpleNamespace

import pytest

from companion.conversation import _trim_history

_BASELINE_BUDGET = 3000
_CANDIDATE_BUDGET = 1800

# Locale-labelled synthetic fixtures test Unicode/context-window behavior only.
# They are not a substitute for native-speaker linguistic certification.
_FIXTURES = {
    "fr": (
        "Je préfère recevoir les rappels en français.",
        "ancien contexte non clinique ",
    ),
    "en": (
        "I prefer reminders in English.",
        "old non-clinical context ",
    ),
    "msa": (
        "أفضل أن تكون التذكيرات باللغة العربية الفصحى.",
        "سياق قديم غير سريري ",
    ),
    "darija_ma": (
        "بغيت التذكيرات يكونو بالدارجة المغربية.",
        "سياق قديم ماشي طبي ",
    ),
    "saudi": (
        "أبغى التذكيرات تكون باللهجة السعودية.",
        "سياق قديم مو طبي ",
    ),
    "emirati": (
        "أبا التذكيرات تكون باللهجة الإماراتية.",
        "سياق قديم مب طبي ",
    ),
    "kuwaiti": (
        "أبي التذكيرات تكون باللهجة الكويتية.",
        "سياق قديم مو طبي ",
    ),
    "qatari": (
        "أبي التذكيرات تكون باللهجة القطرية.",
        "سياق قديم مب طبي ",
    ),
    "omani": (
        "أفضل التذكيرات تكون باللهجة العُمانية.",
        "سياق قديم غير طبي ",
    ),
    "code_switch_fr_darija": (
        "بغيت reminders بالدارجة المغربية, surtout le matin.",
        "old context سياق قديم non-clinical ",
    ),
}

_EXPECTED_CHAR_COUNTS = {
    "fr": (2389, 1423),
    "en": (2337, 1385),
    "msa": (2366, 1373),
    "darija_ma": (2352, 1398),
    "saudi": (2158, 1380),
    "emirati": (2159, 1381),
    "kuwaiti": (2157, 1457),
    "qatari": (2156, 1456),
    "omani": (2255, 1442),
    "code_switch_fr_darija": (2306, 1352),
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


@pytest.mark.parametrize("locale", tuple(_FIXTURES))
def test_1800_budget_preserves_latest_anchor_across_required_locale_corpus(locale):
    anchor, filler = _FIXTURES[locale]
    turns = _history_turns(anchor, filler)

    baseline = _trim_history(turns, _BASELINE_BUDGET)
    candidate = _trim_history(turns, _CANDIDATE_BUDGET)

    assert (len(baseline), len(candidate)) == _EXPECTED_CHAR_COUNTS[locale]
    assert anchor in baseline
    assert anchor in candidate
    assert len(candidate) < len(baseline)
    assert len(candidate) <= _CANDIDATE_BUDGET


def test_expanded_corpus_has_material_character_reduction_without_token_claims():
    baseline = [counts[0] for counts in _EXPECTED_CHAR_COUNTS.values()]
    candidate = [counts[1] for counts in _EXPECTED_CHAR_COUNTS.values()]

    assert median(baseline) == 2280.5
    assert median(candidate) == 1391.5
    assert _nearest_rank(baseline, 0.95) == 2389
    assert _nearest_rank(candidate, 0.95) == 1457

    median_reduction = 1 - median(candidate) / median(baseline)
    p95_reduction = 1 - _nearest_rank(candidate, 0.95) / _nearest_rank(
        baseline, 0.95
    )
    assert median_reduction == pytest.approx(0.3898267924)
    assert p95_reduction == pytest.approx(0.3901213897)
