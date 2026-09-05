import pytest

from evaluation import live_companion_locale_probe as probe


@pytest.mark.parametrize(
    ("locale", "reply"),
    [
        ("fr", "Le soir après le dîner, garde ce format très simple."),
        ("en", "In the evening after dinner, keep it very simple."),
        ("ar", "في المساء بعد العشاء، خله بسيطًا."),
        ("ar-MA", "بالليل من بعد العشا، خليها بسيطة."),
        ("ar-SA", "بالليل بعد العشاء، خلها بسيطة."),
        ("ar-AE", "بالليل عقب العشا، خلها بسيطة."),
        ("ar-KW", "بالليل عقب العشا، خلها بسيطة."),
        ("ar-QA", "بالليل عقب العشا، خلها بسيطة."),
        ("ar-OM", "بالليل بعد العشا، خلها بسيطة."),
    ],
)
def test_evening_anchor_covers_every_certification_locale(locale, reply):
    assert probe._contains_evening_anchor(locale, reply)


def test_meta_recap_detects_false_fr_summary():
    reply = (
        "Tu as demandé de préparer quatre questions à poser à ton médecin, "
        "et maintenant tu souhaites un résumé de cet accord en une phrase simple."
    )
    assert probe._is_meta_recap("fr", reply)


def test_real_fr_recap_is_not_meta_summary():
    reply = (
        "On garde quelque chose de très simple le soir après le dîner, "
        "et tu prépares les quatre questions pour ton médecin sans changer de dose."
    )
    assert not probe._is_meta_recap("fr", reply)
    assert probe._contains_evening_anchor("fr", reply)


def test_normalization_exposes_verbatim_repeat_despite_case_and_spacing():
    assert probe._normalized("  Même   réponse ") == probe._normalized("même réponse")
