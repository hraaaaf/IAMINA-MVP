import pytest

from core.safety_corpora import (
    CORPUS_REVIEWS,
    HIGH_SEVERITY_VARIANT_CASES,
    all_safety_corpus_cases,
    native_review_complete,
)
from core.triage_classification import classify


@pytest.mark.parametrize(
    "case",
    all_safety_corpus_cases(),
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
    darija_cases = [case for case in all_safety_corpus_cases() if case.locale == "ar-MA"]
    assert {case.channel for case in darija_cases} == {"text", "voice_transcript"}
    assert {case.input_form for case in darija_cases} == {
        "arabic_script",
        "latin_transliteration",
        "mixed_language",
    }


def test_high_severity_exact_variants_are_never_empty():
    assert HIGH_SEVERITY_VARIANT_CASES
    assert all(
        case.review_scope == "high_severity_exact_variant"
        for case in HIGH_SEVERITY_VARIANT_CASES
    )
