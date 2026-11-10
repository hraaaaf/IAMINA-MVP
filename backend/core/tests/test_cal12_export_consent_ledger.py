"""CAL-12 synthetic-only durable consent: revocation/owner/notice/destination tests."""
from datetime import datetime, timedelta, timezone

import pytest
from django.contrib.auth.models import User

from core.cal12_export_consent_ledger import (
    CHANNEL,
    DATA_CATEGORY,
    NOTICE_VERSION,
    PURPOSE,
    REAL_PATIENT_EXPORT_ENABLED,
    Cal12FixtureConsentDenied,
    fictional_preview_ready,
    grant_fixture_consent,
    notice_digest,
    revoke_fixture_consent,
)
from core.models import (
    Cal12ExportConsentFixtureEvent,
    Cal12ExportConsentFixtureReceipt,
)
from core.native_auth import issue_native_token, revoke_native_tokens

NOW = datetime(2026, 11, 10, 10, 0, tzinfo=timezone.utc)
START = datetime(2026, 11, 1, tzinfo=timezone.utc)
END = datetime(2026, 11, 8, tzinfo=timezone.utc)


@pytest.fixture
def users(settings, db):
    settings.CAL12_SYNTHETIC_EXPORT_LEDGER_ENABLED = True
    a = User.objects.create_user(
        username="cal12-fixture-a", email="cal12-fixture-a@example.invalid"
    )
    b = User.objects.create_user(
        username="cal12-fixture-b", email="cal12-fixture-b@example.invalid"
    )
    real = User.objects.create_user(
        username="actually-real", email="actually-real@example.invalid"
    )
    return a, b, real


def grant_args(user, **overrides):
    owner = user.username.removeprefix("cal12-fixture-")
    values = {
        "bearer": issue_native_token(user),
        "owner_scope": "fixture:vault:" + owner,
        "recipient_ref": "fixture:doctor:one",
        "channel": CHANNEL,
        "destination_fixture_proof": "fixture:preview:doctor-one",
        "notice_version": NOTICE_VERSION,
        "notice_sha256": notice_digest("fr"),
        "locale": "fr",
        "purpose": PURPOSE,
        "data_category": DATA_CATEGORY,
        "period_start_utc": START,
        "period_end_utc": END,
        "granted_at_utc": NOW,
        "expires_at_utc": NOW + timedelta(minutes=10),
        "explicitly_agreed": True,
    }
    values.update(overrides)
    return values


def ready_args(receipt, grant=None, **overrides):
    values = dict(grant or grant_args(receipt.owner))
    values.pop("granted_at_utc")
    values.pop("expires_at_utc")
    values.pop("explicitly_agreed")
    values.update({
        "receipt_id": receipt.pk,
        "revision": receipt.revision,
        "now_utc": NOW + timedelta(minutes=1),
    })
    values.update(overrides)
    return values


@pytest.mark.django_db
def test_cal12_fixture_notice_matches_exact_flutter_draft_digests(users):
    expected = {
        "fr": "69857b01762f0bedb3b6bced0d256af2817f519e2f987f5991c346ef955c16f2",
        "en": "d0d3eb9a45910e4db273d353e7409d79b040ed33022c20b04d35548bffb123f8",
        "ar": "c6fa87b20eaf9cae42625008e6a539add92a3b923b2dbe871933ae833dc62a9f",
    }
    assert REAL_PATIENT_EXPORT_ENABLED is False
    for locale, digest in expected.items():
        assert notice_digest(locale) == digest
    with pytest.raises(Cal12FixtureConsentDenied):
        notice_digest("ar-MA")


@pytest.mark.django_db
def test_cal12_persisted_consent_revision_audit_and_owner_only(users):
    a, b, _ = users
    grant = grant_args(a)
    receipt = grant_fixture_consent(**grant)
    receipt.refresh_from_db()
    assert receipt.revision == 1
    assert receipt.owner_id == a.pk
    assert receipt.notice_sha256 == notice_digest("fr")
    assert receipt.recipient_ref == "fixture:doctor:one"
    assert receipt.channel == "localPreview"
    assert list(receipt.events.values_list("kind", flat=True)) == ["granted"]
    assert fictional_preview_ready(**ready_args(receipt, grant)) is True
    assert fictional_preview_ready(**ready_args(
        receipt, grant, bearer=issue_native_token(b),
        owner_scope="fixture:vault:b",
    )) is False


@pytest.mark.django_db
def test_cal12_revoke_is_immediate_persistent_and_idempotent(users):
    a, _, _ = users
    grant = grant_args(a)
    receipt = grant_fixture_consent(**grant)
    assert fictional_preview_ready(**ready_args(receipt, grant))
    assert revoke_fixture_consent(
        bearer=grant["bearer"], owner_scope=grant["owner_scope"],
        receipt_id=receipt.pk, revoked_at_utc=NOW + timedelta(minutes=2),
    )
    assert not fictional_preview_ready(**ready_args(receipt, grant))
    assert revoke_fixture_consent(
        bearer=grant["bearer"], owner_scope=grant["owner_scope"],
        receipt_id=receipt.pk, revoked_at_utc=NOW + timedelta(minutes=3),
    )
    receipt.refresh_from_db()
    assert receipt.revoked_at == NOW + timedelta(minutes=2)
    assert list(receipt.events.values_list("kind", flat=True)) == [
        "granted", "revoked",
    ]


@pytest.mark.django_db
def test_cal12_new_grant_supersedes_old_revisions(users):
    a, _, _ = users
    grant = grant_args(a)
    first = grant_fixture_consent(**grant)
    second = grant_fixture_consent(**grant)
    assert (first.revision, second.revision) == (1, 2)
    first.refresh_from_db()
    assert first.revoked_at == NOW
    assert list(first.events.values_list("kind", flat=True)) == [
        "granted", "superseded",
    ]
    assert not fictional_preview_ready(**ready_args(first, grant))
    assert fictional_preview_ready(**ready_args(second, grant))
    assert Cal12ExportConsentFixtureReceipt.objects.filter(
        owner=a, revoked_at__isnull=True,
    ).count() == 1


@pytest.mark.django_db
def test_cal12_bearer_revocation_denies_before_and_after_grant(users):
    a, _, _ = users
    grant = grant_args(a)
    receipt = grant_fixture_consent(**grant)
    revoke_native_tokens(a)
    assert not fictional_preview_ready(**ready_args(receipt, grant))
    with pytest.raises(Cal12FixtureConsentDenied):
        grant_fixture_consent(**grant)
    fresh = issue_native_token(a)
    assert fictional_preview_ready(**ready_args(
        receipt, grant, bearer=fresh,
    )) is True


@pytest.mark.django_db
def test_cal12_wrong_account_cannot_revoke_or_read_another(users):
    a, b, _ = users
    grant = grant_args(a)
    receipt = grant_fixture_consent(**grant)
    assert revoke_fixture_consent(
        bearer=issue_native_token(b), owner_scope="fixture:vault:b",
        receipt_id=receipt.pk, revoked_at_utc=NOW + timedelta(minutes=1),
    ) is False
    assert not fictional_preview_ready(**ready_args(
        receipt, grant, owner_scope="fixture:vault:b",
    ))
    assert fictional_preview_ready(**ready_args(receipt, grant))


@pytest.mark.django_db
def test_cal12_wrong_destination_channel_or_scope_never_accepted(users):
    a, _, _ = users
    grant = grant_args(a)
    receipt = grant_fixture_consent(**grant)
    negative = (
        {"recipient_ref": "fixture:doctor:two"},
        {"recipient_ref": "doctor@clinic.example"},
        {"channel": "secureRecipientDelivery"},
        {"destination_fixture_proof": "fixture:preview:doctor-two"},
        {"owner_scope": "fixture:vault:b"},
        {"purpose": "advertising"},
        {"data_category": "clinicalMeasurements"},
    )
    for changed in negative:
        assert not fictional_preview_ready(**ready_args(
            receipt, grant, **changed,
        ))
        with pytest.raises(Cal12FixtureConsentDenied):
            grant_fixture_consent(**grant_args(a, **changed))


@pytest.mark.django_db
def test_cal12_changed_notice_locale_windows_and_expiry_deny(users):
    a, _, _ = users
    grant = grant_args(a)
    receipt = grant_fixture_consent(**grant)
    for changed in (
        {"notice_version": "OLD"},
        {"notice_sha256": "0" * 64},
        {"locale": "ar"},
        {"period_end_utc": START},
        {"now_utc": NOW + timedelta(minutes=10)},
        {"now_utc": NOW - timedelta(seconds=1)},
        {"now_utc": datetime(2026, 11, 10, 10)},
        {"revision": receipt.revision + 1},
    ):
        assert not fictional_preview_ready(**ready_args(
            receipt, grant, **changed,
        ))


@pytest.mark.django_db
def test_cal12_reject_invalid_grants_no_partial_record_or_audit(users):
    a, _, _ = users
    valid = grant_args(a)
    for changed in (
        {"explicitly_agreed": False},
        {"notice_version": "unapproved"},
        {"notice_sha256": "a" * 64},
        {"expires_at_utc": NOW + timedelta(minutes=16)},
        {"expires_at_utc": NOW},
        {"period_end_utc": START - timedelta(days=1)},
        {"granted_at_utc": datetime(2026, 11, 10, 10)},
    ):
        with pytest.raises(Cal12FixtureConsentDenied):
            grant_fixture_consent(**grant_args(a, **changed))
    assert Cal12ExportConsentFixtureReceipt.objects.count() == 0
    assert Cal12ExportConsentFixtureEvent.objects.count() == 0


@pytest.mark.django_db
def test_cal12_external_non_fixture_user_and_disabled_gate_denied(users, settings):
    _, _, real = users
    with pytest.raises(Cal12FixtureConsentDenied, match="fixture_only"):
        grant_fixture_consent(**grant_args(real))
    a = users[0]
    settings.CAL12_SYNTHETIC_EXPORT_LEDGER_ENABLED = False
    with pytest.raises(Cal12FixtureConsentDenied, match="fixture_only"):
        grant_fixture_consent(**grant_args(a))
    assert Cal12ExportConsentFixtureReceipt.objects.count() == 0


@pytest.mark.django_db
def test_cal12_account_erasure_cascades_receipts_and_fixture_events(users):
    a, _, _ = users
    receipt = grant_fixture_consent(**grant_args(a))
    assert Cal12ExportConsentFixtureEvent.objects.filter(receipt=receipt).count() == 1
    a.delete()
    assert Cal12ExportConsentFixtureReceipt.objects.count() == 0
    assert Cal12ExportConsentFixtureEvent.objects.count() == 0
