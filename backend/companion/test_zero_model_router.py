import pytest

from companion.output_guard import ARABIC_RE
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
    ("message", "language", "expected"),
    [
        (
            "J'ai du mal à être régulier dans mon suivi. "
            "Je commence bien puis j'oublie au bout de quelques jours.",
            "fr",
            "trois cases vides",
        ),
        (
            "Hier encore j'ai oublié. Je voudrais quelque chose de simple "
            "que je puisse vraiment tenir.",
            "fr",
            "Réduis au minimum",
        ),
        (
            "D'accord, ne me donne pas de dose. Aide-moi plutôt à préparer "
            "ce que je dois demander à mon médecin.",
            "fr",
            "Quelles informations dois-je apporter",
        ),
        (
            "Ok, je ne touche pas au traitement. Aide-moi juste à organiser "
            "un suivi très simple pour cette semaine.",
            "fr",
            "trois cases vides",
        ),
        (
            "Wakha, bghit ghir chi routine sahla bach nb9a mntadem "
            "bla nasi7a 3ilajiya.",
            "ar-MA",
            "3 cases khawyin",
        ),
    ],
)
def test_bounded_practical_turns_use_deterministic_replies(message, language, expected):
    reply = exact_chitchat_reply(message, language)
    assert reply is not None
    assert expected in reply


def test_latin_darija_practical_reply_stays_latin():
    reply = exact_chitchat_reply(
        "Wakha, bghit ghir chi routine sahla bach nb9a mntadem "
        "bla nasi7a 3ilajiya.",
        "ar-MA",
    )
    assert reply is not None
    assert not ARABIC_RE.search(reply)


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
        "Aide-moi à préparer mes doses pour mon médecin",
        "Je veux une routine d'insuline simple",
        "ok",
        "yes",
        "no",
        "d'accord",
        "",
    ],
)
def test_any_extra_or_reserved_content_fails_closed(message):
    assert exact_chitchat_reply(message, "fr") is None
