"""Patient-identity redaction helpers for external AI boundaries.

The raw patient record remains linked internally. These helpers only remove
direct identifiers from transient external-egress payloads.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime

_REDACTED = "[REDACTED]"


@dataclass(frozen=True, slots=True)
class PatientIdentity:
    first_name: str | None = None
    last_name: str | None = None
    date_of_birth: date | datetime | str | None = None
    email: str | None = None
    username: str | None = None


def _nonblank(value) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _replace_exact(text: str, value: str | None) -> str:
    value = _nonblank(value)
    if not value:
        return text
    # Bound word-like identities so short names do not redact substrings.
    left = r"(?<!\w)" if value[0].isalnum() else ""
    right = r"(?!\w)" if value[-1].isalnum() else ""
    return re.sub(
        left + re.escape(value) + right,
        _REDACTED,
        text,
        flags=re.IGNORECASE,
    )


def _dob_variants(value: date | datetime | str | None) -> tuple[str, ...]:
    if value is None:
        return ()
    parsed: date | None = None
    if isinstance(value, datetime):
        parsed = value.date()
    elif isinstance(value, date):
        parsed = value
    else:
        raw = str(value).strip()
        try:
            parsed = date.fromisoformat(raw[:10])
        except ValueError:
            return (raw,) if raw else ()

    return (
        parsed.isoformat(),
        parsed.strftime("%d/%m/%Y"),
        parsed.strftime("%d-%m-%Y"),
        parsed.strftime("%d.%m.%Y"),
        parsed.strftime("%Y/%m/%d"),
    )


def redact_identity_values(text: str, identity: PatientIdentity | None) -> str:
    """Redact known direct identifiers without anonymizing clinical facts."""
    if not text or identity is None:
        return text

    result = text
    for value in (
        identity.first_name,
        identity.last_name,
        identity.email,
        identity.username,
    ):
        result = _replace_exact(result, value)
    for value in _dob_variants(identity.date_of_birth):
        result = _replace_exact(result, value)
    return result


def _current_egress_context():
    # The context variable lives in the egress boundary. Lazy import prevents
    # initialization cycles with Django models and provider modules.
    from core.ai_egress import _CURRENT_EGRESS

    return _CURRENT_EGRESS.get()


def current_patient_identity() -> PatientIdentity | None:
    """Resolve direct identity for the patient currently scoped for egress."""
    context = _current_egress_context()
    if context is None:
        return None

    # Identity redaction must not depend on an optional profile row existing.
    # The authenticated Django user remains the minimum authoritative identity
    # source; BasePatientProfile only contributes the optional date of birth.
    from django.contrib.auth import get_user_model

    from core.models import BasePatientProfile

    user_model = get_user_model()
    try:
        patient = (
            user_model.objects.only("first_name", "last_name", "email", "username")
            .get(pk=context.patient_id)
        )
    except user_model.DoesNotExist:
        return None

    date_of_birth = (
        BasePatientProfile.objects.filter(patient_id=context.patient_id)
        .values_list("date_of_birth", flat=True)
        .first()
    )
    return PatientIdentity(
        first_name=patient.first_name,
        last_name=patient.last_name,
        date_of_birth=date_of_birth,
        email=patient.email,
        username=patient.username,
    )


def redact_current_patient_identifiers(text: str) -> str:
    """Redact the current egress patient's identity, if a patient scope exists."""
    return redact_identity_values(text, current_patient_identity())


def current_patient_egress_purpose() -> str | None:
    """Return current patient egress purpose without exposing the patient id."""
    context = _current_egress_context()
    return context.purpose if context is not None else None
