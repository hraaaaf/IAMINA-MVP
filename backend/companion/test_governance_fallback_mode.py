from companion.conversation import (
    _governance_blocked_fallback,
    is_governance_blocked_reply,
)


def test_governance_fallback_is_detected_without_enabling_external_provider():
    prompt = "Que peux-tu me dire de ma première mesure ?"
    fallback = _governance_blocked_fallback(prompt, "fr")
    assert is_governance_blocked_reply(fallback, prompt, "fr")
    assert not is_governance_blocked_reply("Réponse synthétique gouvernée.", prompt, "fr")


def test_english_and_arabic_governance_fallbacks_are_detected():
    for language, prompt in (
        ("en", "What about my glucose reading?"),
        ("ar", "ما هو قياس السكر؟"),
    ):
        fallback = _governance_blocked_fallback(prompt, language)
        assert is_governance_blocked_reply(fallback, prompt, language)
