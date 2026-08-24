import pytest

from companion.conversation import _deterministic_language, detect_language
from companion.narrator_prompts import get_language_label

GULF_DIALECTS = ("ar-SA", "ar-AE", "ar-KW", "ar-QA", "ar-OM")


@pytest.mark.parametrize("dialect", GULF_DIALECTS)
def test_confirmed_gulf_default_is_preserved_for_arabic_message(dialect):
    assert detect_language("اليوم ما سجلت المتابعة", dialect) == dialect


@pytest.mark.parametrize("dialect", GULF_DIALECTS)
def test_gulf_prompt_label_is_explicit_and_arabic(dialect):
    label = get_language_label(dialect)
    assert label != dialect
    assert "العربية" in label


@pytest.mark.parametrize("dialect", GULF_DIALECTS)
def test_gulf_dialect_uses_msa_for_deterministic_clinical_copy(dialect):
    assert _deterministic_language(dialect) == "ar"


def test_unconfirmed_arabic_detection_keeps_existing_darija_fallback():
    assert detect_language("اليوم ما سجلت المتابعة", "fr") == "ar-MA"


def test_unknown_non_arabic_default_is_unchanged():
    assert detect_language("hello", "fr") == "fr"


def test_moroccan_darija_stays_darija_for_deterministic_copy():
    assert _deterministic_language("ar-MA") == "ar-MA"
