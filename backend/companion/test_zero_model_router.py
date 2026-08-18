import pytest

from companion.zero_model_router import exact_chitchat_reply


@pytest.mark.parametrize(
    ("message", "language"),
    [
        ("Bonjour", "fr"),
        ("merci beaucoup!", "fr"),
        ("Hello", "en"),
        ("thank you", "en"),
        ("salam", "ar-MA"),
        ("chokran", "ar-MA"),
        ("سلام", "ar-MA"),
        ("شكرا", "ar"),
    ],
)
def test_exact_non_clinical_turns_are_eligible(message, language):
    assert exact_chitchat_reply(message, language)


@pytest.mark.parametrize(
    "message",
    [
        "merci glycémie 40",
        "bonjour je tremble",
        "salam 42",
        "thank you, my glucose is low",
        "شكرا السكر 40",
        "hello I took insulin",
        "merci mais je vais tomber",
        "",
    ],
)
def test_any_extra_or_clinical_content_fails_closed(message):
    assert exact_chitchat_reply(message, "fr") is None
