from datetime import date

from core.emergency_resources import resolve_emergency_resources
from core.locale import ResolvedLocale


def _locale(*, country_code=None, confirmed=False):
    return ResolvedLocale(
        country_code=country_code,
        ui_language="fr",
        response_language="fr",
        script_preference="latin",
        transliteration_preference="none",
        dialect=None,
        glucose_unit="mg/dL",
        timezone=None,
        country_confirmed=confirmed,
        timezone_confirmed=False,
    )


def test_unconfirmed_country_cannot_select_country_resources():
    result = resolve_emergency_resources(
        _locale(country_code="MA", confirmed=False),
        today=date(2026, 7, 30),
    )

    assert result.country_specific is False
    assert result.contacts == ()
    assert result.safe_message_code == "country_unconfirmed"


def test_confirmed_morocco_selects_versioned_resources():
    result = resolve_emergency_resources(
        _locale(country_code="MA", confirmed=True),
        today=date(2026, 7, 30),
    )

    assert result.country_specific is True
    assert result.country_code == "MA"
    assert [(item.service, item.number) for item in result.contacts] == [
        ("ambulance", "150"),
        ("fire", "150"),
        ("police", "190"),
        ("gendarmerie", "177"),
    ]
    assert result.source_reference is not None
    assert result.verified_on == date(2026, 7, 30)


def test_unknown_confirmed_country_fails_closed():
    result = resolve_emergency_resources(
        _locale(country_code="ZZ", confirmed=True),
        today=date(2026, 7, 30),
    )

    assert result.country_specific is False
    assert result.safe_message_code == "country_not_configured"


def test_stale_resource_fails_closed():
    result = resolve_emergency_resources(
        _locale(country_code="MA", confirmed=True),
        today=date(2027, 1, 31),
    )

    assert result.country_specific is False
    assert result.contacts == ()
    assert result.safe_message_code == "country_resource_stale"
