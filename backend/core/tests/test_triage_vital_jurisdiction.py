from core.locale import ResolvedLocale
from core.middleware.triage_vital import _pick_emergency_response


def _locale(*, country_code=None, confirmed=False, response_language="fr"):
    return ResolvedLocale(
        country_code=country_code,
        ui_language="fr",
        response_language=response_language,
        script_preference="latin",
        transliteration_preference="none",
        dialect=None,
        glucose_unit="mg/dL",
        timezone=None,
        country_confirmed=confirmed,
        timezone_confirmed=False,
    )


def test_confirmed_morocco_uses_registry_ambulance_number():
    payload = _pick_emergency_response(
        "glycémie 40 mg/dL",
        locale=_locale(country_code="MA", confirmed=True),
        language="fr",
    )

    assert payload["is_emergency"] is True
    assert "150" in payload["reply"]
    assert "141" not in payload["reply"]
    assert "SAMU" not in payload["reply"]


def test_unconfirmed_country_fails_closed_without_country_number():
    payload = _pick_emergency_response(
        "glycémie 40 mg/dL",
        locale=_locale(country_code="MA", confirmed=False),
        language="fr",
    )

    assert payload["is_emergency"] is True
    assert "150" not in payload["reply"]
    assert "141" not in payload["reply"]
    assert "112" not in payload["reply"]
    assert "pas de numéro d'urgence confirmé" in payload["reply"]


def test_confirmed_but_unconfigured_country_fails_closed():
    payload = _pick_emergency_response(
        "glycémie 40 mg/dL",
        locale=_locale(country_code="FR", confirmed=True),
        language="fr",
    )

    assert "150" not in payload["reply"]
    assert "112" not in payload["reply"]
    assert "pas de numéro d'urgence confirmé" in payload["reply"]


def test_darija_response_uses_same_confirmed_registry_contact():
    payload = _pick_emergency_response(
        "sukkar 40 mg/dL",
        locale=_locale(
            country_code="MA",
            confirmed=True,
            response_language="ar",
        ),
        language="ar-MA",
    )

    assert "150" in payload["reply"]
    assert "141" not in payload["reply"]
