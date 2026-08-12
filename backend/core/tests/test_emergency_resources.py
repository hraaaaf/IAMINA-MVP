from datetime import date

from core.emergency_resources import (
    render_medical_emergency_contact,
    resolve_emergency_resources,
)
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


def test_renderer_uses_validated_medical_contact_for_confirmed_morocco():
    text = render_medical_emergency_contact(
        _locale(country_code="MA", confirmed=True),
        language="fr",
        today=date(2026, 7, 30),
    )

    assert "150" in text
    assert "141" not in text


def test_renderer_is_number_free_when_country_is_unconfirmed():
    text = render_medical_emergency_contact(
        _locale(country_code="MA", confirmed=False),
        language="fr",
        today=date(2026, 7, 30),
    )

    assert "150" not in text
    assert "numéro d'urgence confirmé" in text


def test_renderer_is_number_free_when_resource_is_stale():
    text = render_medical_emergency_contact(
        _locale(country_code="MA", confirmed=True),
        language="fr",
        today=date(2027, 1, 31),
    )

    assert "150" not in text
    assert "numéro d'urgence confirmé" in text
