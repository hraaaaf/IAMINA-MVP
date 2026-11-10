"""CAL-12 versioned, revocable, *fictional* clinical-export consent ledger.

NO public endpoints, NO clinical records, NO generated documents, NO delivery.
Explicit setting plus fictional Django accounts required even for internal calls.
This tests the future consent lifecycle, not legal consent, verified clinicians,
or an authorization for a real patient. The future export action must check its
own bearer, consent, recipient, destination and clinical approval atomically.
"""
from __future__ import annotations

import hashlib
import re
from datetime import datetime, timedelta

from django.conf import settings
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Max

from core.models import (
    Cal12ExportConsentFixtureEvent,
    Cal12ExportConsentFixtureReceipt,
)
from core.native_auth import NativeTokenError, verify_native_token

REAL_PATIENT_EXPORT_ENABLED = False
NOTICE_VERSION = "CAL12-DRAFT-2026-11-10.1"
PURPOSE = "followUpWithClinician"
DATA_CATEGORY = "syntheticManualReadings"
CHANNEL = "localPreview"
MAX_DURATION = timedelta(minutes=15)

# Must match frontend DoctorExportDraftNoticeCatalog byte-for-byte.
_NOTICES = {
    "fr": (
        "DÉMONSTRATION UNIQUEMENT. Prévisualiser des mesures "
        "fictives pour un médecin fictif. Aucun document envoyé."
    ),
    "en": (
        "DEMONSTRATION ONLY. Preview fictional readings "
        "for a fictional doctor. No document is sent."
    ),
    "ar": (
        "للتجربة فقط. معاينة قياسات افتراضية لطبيب افتراضي. "
        "لا يتم إرسال أي مستند."
    ),
}

# Not real professional-directory evidence. Never accept actual addresses or
# a caller's assertion that a recipient has been independently verified.
_DESTINATION_FIXTURES = {
    "fixture:doctor:one": "fixture:preview:doctor-one",
    "fixture:doctor:two": "fixture:preview:doctor-two",
}
_USERNAME = re.compile(r"^cal12-fixture-[a-z0-9_-]{1,24}$")


class Cal12FixtureConsentDenied(ValueError):
    """Opaque failure; callers cannot use this as a real export permit."""


def notice_digest(locale: str) -> str:
    try:
        return hashlib.sha256(_NOTICES[locale].encode("utf-8")).hexdigest()
    except KeyError as exc:
        raise Cal12FixtureConsentDenied("unsupported_fixture_notice") from exc


def _utc(value: datetime) -> bool:
    return (
        isinstance(value, datetime)
        and value.tzinfo is not None
        and value.utcoffset() == timedelta(0)
    )


def _fixture_user(user: User) -> str:
    if (
        not getattr(settings, "CAL12_SYNTHETIC_EXPORT_LEDGER_ENABLED", False)
        or REAL_PATIENT_EXPORT_ENABLED
        or not user.is_active
        or not _USERNAME.fullmatch(user.username)
        or user.email != user.username + "@example.invalid"
    ):
        raise Cal12FixtureConsentDenied("fixture_only")
    return "fixture:vault:" + user.username.removeprefix("cal12-fixture-")


def _bearer_owner(bearer: str, owner_scope: str) -> User:
    try:
        user = verify_native_token(bearer)
    except (NativeTokenError, TypeError) as exc:
        raise Cal12FixtureConsentDenied("invalid_or_revoked_bearer") from exc
    if _fixture_user(user) != owner_scope:
        raise Cal12FixtureConsentDenied("owner_mismatch")
    return user


def _destination(recipient_ref: str, channel: str, proof: str) -> None:
    if (
        channel != CHANNEL
        or _DESTINATION_FIXTURES.get(recipient_ref) != proof
        or not proof
    ):
        raise Cal12FixtureConsentDenied("fictional_destination_not_confirmed")


def grant_fixture_consent(
    *,
    bearer: str,
    owner_scope: str,
    recipient_ref: str,
    channel: str,
    destination_fixture_proof: str,
    notice_version: str,
    notice_sha256: str,
    locale: str,
    purpose: str,
    data_category: str,
    period_start_utc: datetime,
    period_end_utc: datetime,
    granted_at_utc: datetime,
    expires_at_utc: datetime,
    explicitly_agreed: bool,
) -> Cal12ExportConsentFixtureReceipt:
    """Persist ONE new fictional grant; supersede all previous active grants."""
    user = _bearer_owner(bearer, owner_scope)
    _destination(recipient_ref, channel, destination_fixture_proof)
    if (
        not explicitly_agreed
        or notice_version != NOTICE_VERSION
        or notice_sha256 != notice_digest(locale)
        or purpose != PURPOSE
        or data_category != DATA_CATEGORY
    ):
        raise Cal12FixtureConsentDenied("notice_or_purpose_invalid")
    values = (
        period_start_utc,
        period_end_utc,
        granted_at_utc,
        expires_at_utc,
    )
    if not all(_utc(value) for value in values):
        raise Cal12FixtureConsentDenied("utc_required")
    if (
        period_start_utc > period_end_utc
        or granted_at_utc >= expires_at_utc
        or expires_at_utc - granted_at_utc > MAX_DURATION
    ):
        raise Cal12FixtureConsentDenied("window_invalid")

    with transaction.atomic():
        # Serialise per owner on PostgreSQL, avoiding two active revisions.
        User.objects.select_for_update().get(pk=user.pk)
        # Check revocation again under the owner lock.
        _bearer_owner(bearer, owner_scope)
        active = Cal12ExportConsentFixtureReceipt.objects.select_for_update().filter(
            owner=user,
            revoked_at__isnull=True,
        )
        for previous in active:
            previous.revoked_at = granted_at_utc
            previous.save(update_fields=["revoked_at"])
            Cal12ExportConsentFixtureEvent.objects.create(
                receipt=previous,
                kind="superseded",
                occurred_at=granted_at_utc,
            )
        highest = (
            Cal12ExportConsentFixtureReceipt.objects.filter(owner=user).aggregate(
                max_revision=Max("revision")
            )["max_revision"]
            or 0
        )
        receipt = Cal12ExportConsentFixtureReceipt.objects.create(
            owner=user,
            revision=highest + 1,
            native_auth_version=user.base_profile.auth_token_version,
            notice_version=notice_version,
            notice_sha256=notice_sha256,
            notice_locale=locale,
            purpose=purpose,
            data_category=data_category,
            recipient_ref=recipient_ref,
            channel=channel,
            period_start_utc=period_start_utc,
            period_end_utc=period_end_utc,
            recipient_confirmed_at=granted_at_utc,
            granted_at=granted_at_utc,
            expires_at=expires_at_utc,
        )
        Cal12ExportConsentFixtureEvent.objects.create(
            receipt=receipt, kind="granted", occurred_at=granted_at_utc
        )
        return receipt


def revoke_fixture_consent(
    *,
    bearer: str,
    owner_scope: str,
    receipt_id: int,
    revoked_at_utc: datetime,
) -> bool:
    """Revoke only own fictional grant. Retrying never duplicates an event."""
    user = _bearer_owner(bearer, owner_scope)
    if not _utc(revoked_at_utc):
        raise Cal12FixtureConsentDenied("utc_required")
    with transaction.atomic():
        User.objects.select_for_update().get(pk=user.pk)
        _bearer_owner(bearer, owner_scope)
        receipt = Cal12ExportConsentFixtureReceipt.objects.select_for_update().filter(
            owner=user, pk=receipt_id
        ).first()
        if receipt is None:
            return False
        if receipt.revoked_at is not None:
            return True
        receipt.revoked_at = revoked_at_utc
        receipt.save(update_fields=["revoked_at"])
        Cal12ExportConsentFixtureEvent.objects.create(
            receipt=receipt, kind="revoked", occurred_at=revoked_at_utc
        )
        return True


def fictional_preview_ready(
    *,
    bearer: str,
    owner_scope: str,
    receipt_id: int,
    revision: int,
    recipient_ref: str,
    channel: str,
    destination_fixture_proof: str,
    notice_version: str,
    notice_sha256: str,
    locale: str,
    purpose: str,
    data_category: str,
    period_start_utc: datetime,
    period_end_utc: datetime,
    now_utc: datetime,
) -> bool:
    """Read-only negative gate, NOT an export permit, capability or token."""
    try:
        user = _bearer_owner(bearer, owner_scope)
        _destination(recipient_ref, channel, destination_fixture_proof)
        if not _utc(now_utc) or not _utc(period_start_utc) or not _utc(period_end_utc):
            return False
        receipt = Cal12ExportConsentFixtureReceipt.objects.filter(
            owner=user, pk=receipt_id
        ).first()
        if receipt is None or receipt.revoked_at is not None:
            return False
        if (
            receipt.native_auth_version != user.base_profile.auth_token_version
            or receipt.revision != revision
            or receipt.revision != (
                Cal12ExportConsentFixtureReceipt.objects.filter(owner=user).aggregate(
                    max_revision=Max("revision")
                )["max_revision"]
            )
            or receipt.notice_version != notice_version
            or receipt.notice_version != NOTICE_VERSION
            or receipt.notice_sha256 != notice_sha256
            or receipt.notice_sha256 != notice_digest(locale)
            or receipt.notice_locale != locale
            or receipt.purpose != purpose
            or receipt.purpose != PURPOSE
            or receipt.data_category != data_category
            or receipt.data_category != DATA_CATEGORY
            or receipt.recipient_ref != recipient_ref
            or receipt.channel != channel
            or receipt.channel != CHANNEL
            or receipt.period_start_utc != period_start_utc
            or receipt.period_end_utc != period_end_utc
            or receipt.period_start_utc > receipt.period_end_utc
            or not _utc(receipt.granted_at)
            or not _utc(receipt.expires_at)
            or not _utc(receipt.recipient_confirmed_at)
            or receipt.granted_at > now_utc
            or now_utc >= receipt.expires_at
            or receipt.expires_at - receipt.granted_at > MAX_DURATION
            or receipt.recipient_confirmed_at > now_utc
            or receipt.recipient_confirmed_at < receipt.granted_at
        ):
            return False
        return True
    except Cal12FixtureConsentDenied:
        return False
