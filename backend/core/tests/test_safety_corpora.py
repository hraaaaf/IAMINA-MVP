import pytest

from core.safety_corpora import (
    CORPUS_REVIEWS,
    GLYCEMIC_EMERGENCY_CASES,
    native_review_complete,
)
from core.triage_classification import classify


@pytest.mark.parametrize(
    "case",
    GLYCEMIC_EMERGENCY_CASES,
    ids=lambda case: case.case_id,
)
def test_glycemic_emergency_corpus_has_deterministic_parity(case):
    assert classify(case.text) is case.expected


def test_all_baseline_locales_have_review_records():
    assert {review.locale for review in CORPUS_REVIEWS} == {
        "fr",
        "ar",
        "en",
        "ar-MA",
    }


def test_native_review_cannot_be_inferred_from_automated_tests():
    assert all(not native_review_complete(locale) for locale in ("fr", "ar", "en", "ar-MA"))


def test_darija_corpus_covers_text_voice_script_and_transliteration():
    darija_cases = [case for case in GLYCEMIC_EMERGENCY_CASES if case.locale == "ar-MA"]
    assert {case.channel for case in darija_cases} == {"text", "voice_transcript"}
    assert {case.input_form for case in darija_cases} == {
        "arabic_script",
        "latin_transliteration",
        "mixed_language",
    }
