"""D2 J4/J5/J7 adversarial tests: synthetic Django users, no real patient data."""
from datetime import timedelta
from io import StringIO
from types import SimpleNamespace

import pytest
from django.contrib.auth.models import User
from django.core.management import call_command
from django.utils import timezone
from ninja.errors import HttpError
from pydantic import ValidationError

from core.api.v1.account import ConsentGrantSchema, give_consent, withdraw_consent
from core.api.v1.d2_notifications import (
    ProactivityGrant,
    delete_item,
    disable_proactivity,
    enable_proactivity,
    inbox,
    mark_all_read,
    mark_read,
)
from core.consent_notice import expected_notice_claim
from core.d2_notification_service import (
    MAX_INBOX,
    maybe_record_language_preference,
    notice_contract,
    record_verified_event,
)
from core.models import AIConsentReceipt, BasePatientProfile
from core.models.d2_notification import (
    D2Notification,
    D2NotificationPreference,
    D2ProactiveEmissionReceipt,
)
from core.models.locale import PatientLocalePreference


@pytest.fixture
def people(transactional_db, monkeypatch):
    a = User.objects.create_user(username="d2-synthetic-A")
    b = User.objects.create_user(username="d2-synthetic-B")
    monkeypatch.setattr("core.api.v1.account.record_audit", lambda *args, **kwargs: None)
    return a, b


def req(user, *, cookie=False, bearer=False):
    return SimpleNamespace(
        user=user, COOKIES={"sessionid": "synthetic"} if cookie else {},
        META={"HTTP_AUTHORIZATION": "Bearer synthetic"} if bearer else {},
    )


def enable(user, locale="fr"):
    data = notice_contract(locale)
    return enable_proactivity(req(user), ProactivityGrant(
        locale=locale,
        notice_version=data["notice_version"],
        notice_digest=data["notice_digest"],
        acknowledgment="ENABLE_D2_IN_APP_PROACTIVITY",
    ))


def grant_global_consent(user):
    claim = expected_notice_claim("fr")
    return give_consent(req(user), ConsentGrantSchema(
        notice_version=claim.version,
        notice_hash=claim.notice_hash,
        locale=claim.locale,
    ))


@pytest.mark.django_db
def test_zero_defaults_to_no_proactivity_no_fake_events(people):
    a, _ = people
    view = inbox(req(a))
    assert view["purpose"] == "d2_in_app_notifications"
    assert view["in_app_enabled"] is True
    assert view["browser_push_enabled"] is False
    assert view["proactive_opt_in"] is False
    assert view["items"] == []
    assert view["unread_count"] == 0
    assert D2NotificationPreference.objects.count() == 0
    assert D2Notification.objects.count() == 0  # GET must be read only


@pytest.mark.django_db
def test_real_consent_receipt_generates_factual_event_once_and_withdraws(people):
    a, b = people
    grant_global_consent(a)
    items = inbox(req(a))["items"]
    assert [x["code"] for x in items] == ["ai_consent_given"]
    assert inbox(req(b))["items"] == []
    grant_global_consent(a)  # idempotent same consent
    assert D2Notification.objects.filter(patient=a).count() == 1
    withdraw_consent(req(a))
    assert {x["code"] for x in inbox(req(a))["items"]} == {
        "ai_consent_given", "ai_consent_withdrawn",
    }
    assert inbox(req(b))["items"] == []
    # Account events are factual, not controlled by proactive consent.
    assert inbox(req(a))["proactive_opt_in"] is False


@pytest.mark.django_db
def test_events_cannot_be_forged_with_other_patient_receipt(people):
    a, b = people
    grant_global_consent(a)
    receipt = AIConsentReceipt.objects.get(patient=a)
    with pytest.raises(ValueError, match="Unverified"):
        record_verified_event(
            patient_id=b.pk, code="ai_consent_given",
            source="consent_receipt", source_pk=receipt.pk,
        )
    for source, code in (
        ("untrusted_web_payload", "ai_consent_given"),
        ("consent_receipt", "clinical_hypoglycemia"),
    ):
        with pytest.raises(ValueError):
            record_verified_event(
                patient_id=a.pk, code=code, source=source, source_pk=receipt.pk,
            )
    with pytest.raises(ValueError):
        record_verified_event(
            patient_id=True, code="ai_consent_given",
            source="consent_receipt", source_pk=receipt.pk,
        )
    assert D2Notification.objects.filter(patient=b).count() == 0


@pytest.mark.django_db
def test_proactive_only_after_explicit_verified_notice_and_real_locale_provenance(people):
    a, b = people
    pa = BasePatientProfile.objects.create(patient=a)
    pb = BasePatientProfile.objects.create(patient=b)
    PatientLocalePreference.objects.create(
        profile=pa, ui_language="fr", ui_language_provenance="defaulted",
    )
    PatientLocalePreference.objects.create(
        profile=pb, ui_language="fr", ui_language_provenance="user_confirmed",
    )
    assert maybe_record_language_preference(patient_id=a.pk) is None
    view = enable(a)
    assert view["proactive_opt_in"] is True
    assert [x["code"] for x in view["items"]] == ["language_pref_available"]
    assert maybe_record_language_preference(patient_id=a.pk) is None
    assert inbox(req(b))["items"] == []
    assert enable(b)["items"] == []  # confirmed preference is not an event
    assert D2Notification.objects.filter(patient=a, kind="proactive").count() == 1
    stopped = disable_proactivity(req(a))
    assert stopped["proactive_opt_in"] is False
    assert stopped["items"] == []
    assert maybe_record_language_preference(patient_id=a.pk) is None


@pytest.mark.django_db
def test_critical_consent_survives_notification_producer_outage(people, monkeypatch):
    a, _ = people

    def simulate_notification_outage(*args, **kwargs):
        raise RuntimeError("synthetic D2 database unavailable")

    monkeypatch.setattr(
        "core.api.v1.account.record_verified_event",
        simulate_notification_outage,
    )
    result = grant_global_consent(a)
    assert result["ai_consent_given"] is True
    assert AIConsentReceipt.objects.filter(patient=a, revoked_at__isnull=True).count() == 1
    assert D2Notification.objects.filter(patient=a).count() == 0
    # Full account-consent lifecycle must also survive a notice storage outage.
    assert withdraw_consent(req(a))["ai_consent_given"] is False
    assert AIConsentReceipt.objects.filter(patient=a, revoked_at__isnull=True).count() == 0


@pytest.mark.django_db
def test_wrong_notice_version_and_extra_fields_fail_closed(people):
    a, _ = people
    notice = notice_contract("fr")
    with pytest.raises(HttpError) as exc:
        enable_proactivity(req(a), ProactivityGrant(
            locale="fr", notice_version="stale",
            notice_digest=notice["notice_digest"],
            acknowledgment="ENABLE_D2_IN_APP_PROACTIVITY",
        ))
    assert exc.value.status_code == 422
    with pytest.raises(ValidationError):
        ProactivityGrant.model_validate({
            "locale": "fr", "notice_version": notice["notice_version"],
            "notice_digest": notice["notice_digest"],
            "acknowledgment": "ENABLE_D2_IN_APP_PROACTIVITY",
            "patient_id": 9999,
        })
    assert not D2NotificationPreference.objects.exists()


@pytest.mark.django_db
def test_csrf_and_mixed_credentials_are_rejected_for_mutations(people):
    a, _ = people
    data = notice_contract("fr")
    request = ProactivityGrant(
        locale="fr", notice_version=data["notice_version"],
        notice_digest=data["notice_digest"],
        acknowledgment="ENABLE_D2_IN_APP_PROACTIVITY",
    )
    with pytest.raises(HttpError) as exc:
        enable_proactivity(req(a, cookie=True, bearer=True), request)
    assert exc.value.status_code == 403
    with pytest.raises(HttpError):
        mark_all_read(req(a, cookie=True, bearer=True))
    with pytest.raises(HttpError):
        disable_proactivity(req(a, cookie=True, bearer=True))


@pytest.mark.django_db
def test_read_mark_delete_are_patient_scoped_and_idempotent(people):
    a, b = people
    grant_global_consent(a)
    item = D2Notification.objects.get(patient=a)
    with pytest.raises(HttpError) as exc:
        mark_read(req(b), item.pk)
    assert exc.value.status_code == 404
    with pytest.raises(HttpError) as exc:
        delete_item(req(b), item.pk)
    assert exc.value.status_code == 404
    assert mark_read(req(a), item.pk)["item"]["read_at"] is not None
    assert mark_all_read(req(a))["updated"] == 0
    assert delete_item(req(a), item.pk) == {"deleted": True}
    assert inbox(req(a))["items"] == []


@pytest.mark.django_db
def test_proactive_budget_two_per_rolling_week_and_one_per_day(people):
    a, _ = people
    profile = BasePatientProfile.objects.create(patient=a)
    PatientLocalePreference.objects.create(profile=profile)
    enable(a)
    D2Notification.objects.filter(patient=a).delete()
    D2ProactiveEmissionReceipt.objects.filter(patient=a).delete()
    now = timezone.now()
    D2ProactiveEmissionReceipt.objects.create(
        patient=a, event_key="b" * 64,
        emitted_at=now - timedelta(hours=2),
    )
    assert maybe_record_language_preference(patient_id=a.pk) is None
    D2ProactiveEmissionReceipt.objects.filter(patient=a).update(
        emitted_at=now - timedelta(days=2),
    )
    assert maybe_record_language_preference(patient_id=a.pk) is not None
    D2Notification.objects.filter(patient=a).delete()
    D2ProactiveEmissionReceipt.objects.filter(patient=a).update(
        emitted_at=now - timedelta(days=2),
    )
    assert maybe_record_language_preference(patient_id=a.pk) is None  # 2/week


@pytest.mark.django_db
def test_expired_items_hidden_without_fake_physical_purge_claim(people):
    a, _ = people
    D2Notification.objects.create(
        patient=a, event_key="c" * 64, kind="event",
        code="ai_consent_given",
        created_at=timezone.now() - timedelta(days=9),
        expires_at=timezone.now() - timedelta(days=2),
    )
    assert inbox(req(a))["items"] == []
    assert D2Notification.objects.filter(patient=a).count() == 1


@pytest.mark.django_db
def test_expired_physical_purge_is_manual_bounded_and_dry_by_default(people):
    a, _ = people
    now = timezone.now()
    D2Notification.objects.bulk_create([
        D2Notification(
            patient=a, event_key=f"{i + 10:064x}", kind="event",
            code="ai_consent_given",
            created_at=now - timedelta(days=10),
            expires_at=now - timedelta(days=2),
        )
        for i in range(3)
    ])
    output = StringIO()
    call_command("purge_d2_notifications", stdout=output)
    assert "DRY_RUN" in output.getvalue()
    assert D2Notification.objects.count() == 3
    output = StringIO()
    call_command("purge_d2_notifications", apply=True, limit=2, stdout=output)
    assert "deleted=2" in output.getvalue()
    assert D2Notification.objects.count() == 1


@pytest.mark.django_db
def test_emission_receipt_purge_is_bounded_and_dry_by_default(people):
    a, _ = people
    now = timezone.now()
    D2ProactiveEmissionReceipt.objects.bulk_create([
        D2ProactiveEmissionReceipt(
            patient=a, event_key=f"{i + 100:064x}",
            emitted_at=now - timedelta(days=9),
        )
        for i in range(3)
    ])
    stdout = StringIO()
    call_command("purge_d2_notifications", stdout=stdout)
    assert "receipts_expired=3" in stdout.getvalue()
    assert D2ProactiveEmissionReceipt.objects.count() == 3

    stdout = StringIO()
    call_command("purge_d2_notifications", apply=True, limit=2, stdout=stdout)
    assert "receipts_deleted=2" in stdout.getvalue()
    assert D2ProactiveEmissionReceipt.objects.count() == 1


def test_no_phi_or_free_text_columns():
    names = {field.name for field in D2Notification._meta.fields}
    assert {"event_key", "code", "kind", "patient", "created_at", "expires_at", "read_at"} <= names
    assert not {"message", "medical_data", "blood_glucose", "body", "free_text"} & names


@pytest.mark.django_db
def test_unread_count_is_bounded_by_server_inbox_limit(people):
    a, _ = people
    now = timezone.now()
    D2Notification.objects.bulk_create([
        D2Notification(
            patient=a, event_key=f"{i:064x}", kind="event",
            code="ai_consent_given", created_at=now,
            expires_at=now + timedelta(days=1),
        )
        for i in range(MAX_INBOX + 5)
    ])
    view = inbox(req(a))
    assert len(view["items"]) == MAX_INBOX
    assert view["unread_count"] == MAX_INBOX
