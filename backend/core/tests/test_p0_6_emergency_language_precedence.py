from core.emergency_response import compose_emergency_response
from core.input_safety import URGENT, InputSafetyDecision
from core.locale import ResolvedLocale


def test_confirmed_response_language_beats_unrelated_dialect_value():
    locale = ResolvedLocale(
        country_code="MA",
        ui_language="fr",
        response_language="fr",
        script_preference="latin",
        transliteration_preference="none",
        dialect="ar-MA",
        glucose_unit="mg/dL",
        timezone=None,
        country_confirmed=True,
        timezone_confirmed=False,
    )

    response = compose_emergency_response(
        InputSafetyDecision(URGENT, "glycemic_emergency"),
        locale=locale,
        message="glycémie 35",
    )

    assert response.reply_language == "fr"
    assert "SITUATION D'URGENCE" in response.reply
    assert "150" in response.reply
