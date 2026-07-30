"""Versioned country emergency-resource registry.

Country-specific resources are returned only for an explicitly confirmed country.
Missing, unknown or stale entries fail closed to the generic emergency path.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from core.locale import ResolvedLocale


@dataclass(frozen=True)
class EmergencyContact:
    service: str
    number: str


@dataclass(frozen=True)
class EmergencyResourcePolicy:
    country_code: str
    contacts: tuple[EmergencyContact, ...]
    source_owner: str
    source_reference: str
    verified_on: date
    review_due_on: date
    registry_owner: str


@dataclass(frozen=True)
class ResolvedEmergencyResources:
    country_code: str | None
    contacts: tuple[EmergencyContact, ...]
    country_specific: bool
    safe_message_code: str
    source_reference: str | None
    verified_on: date | None


_REGISTRY: dict[str, EmergencyResourcePolicy] = {
    "MA": EmergencyResourcePolicy(
        country_code="MA",
        contacts=(
            EmergencyContact(service="ambulance", number="150"),
            EmergencyContact(service="fire", number="150"),
            EmergencyContact(service="police", number="190"),
            EmergencyContact(service="gendarmerie", number="177"),
        ),
        source_owner="UK Foreign, Commonwealth & Development Office",
        source_reference="GOV.UK Morocco travel advice — Getting help",
        verified_on=date(2026, 7, 30),
        review_due_on=date(2027, 1, 30),
        registry_owner="IAmina Safety & Compliance",
    ),
}


def resolve_emergency_resources(
    locale: ResolvedLocale,
    *,
    today: date | None = None,
) -> ResolvedEmergencyResources:
    """Return country resources only when country is confirmed and policy is current."""
    current_date = today or date.today()
    if not locale.country_confirmed or locale.country_code is None:
        return _generic("country_unconfirmed")

    policy = _REGISTRY.get(locale.country_code)
    if policy is None:
        return _generic("country_not_configured")
    if current_date > policy.review_due_on:
        return _generic("country_resource_stale")

    return ResolvedEmergencyResources(
        country_code=policy.country_code,
        contacts=policy.contacts,
        country_specific=True,
        safe_message_code="country_emergency_resources",
        source_reference=policy.source_reference,
        verified_on=policy.verified_on,
    )


def _generic(reason: str) -> ResolvedEmergencyResources:
    return ResolvedEmergencyResources(
        country_code=None,
        contacts=(),
        country_specific=False,
        safe_message_code=reason,
        source_reference=None,
        verified_on=None,
    )
