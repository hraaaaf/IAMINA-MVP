import pytest

from companion.zero_model_router import exact_chitchat_reply


@pytest.mark.parametrize(
    ("message", "language"),
    [
        ("Salut", "fr"),
        ("merci beaucoup!", "fr"),
        ("Au revoir", "fr"),
        ("Hello", "en"),
        ("thank you", "en"),
        ("Goodbye", "en"),
        ("salam", "ar-MA"),
        ("chokran", "ar-MA"),
        ("bslama", "ar-MA"),
        ("سلام", "ar-MA"),
        ("شكرا", "ar"),
        ("مع السلامة", "ar"),
    ],
)
def test_exact_non_clinical_turns_are_eligible(message, language):
    assert exact_chitchat_reply(message, language)


@pytest.mark.parametrize(
    "message",
    [
        "Bonjour",
        "merci glycémie 40",
        "bonjour je tremble",
        "salam 42",
        "thank you, my glucose is low",
        "شكرا السكر 40",
        "hello I took insulin",
        "merci mais je vais tomber",
        "au revoir glycémie 40",
        "goodbye I took insulin",
        "مع السلامة السكر 40",
        "bslama 42",
        "bonjour merci",
        "salam chokran",
        "ok",
        "yes",
        "no",
        "d'accord",
        "",
    ],
)
def test_any_extra_or_reserved_content_fails_closed(message):
    assert exact_chitchat_reply(message, "fr") is None
