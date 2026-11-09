"""D2 J7 FUE: real Django HTTP session paths with synthetic identities only.

No live patient, external provider, Vercel deployment, or production database.
These tests exercise HTTP routing/middleware, not Flutter-rendered browser UI.
"""
import json
from datetime import timedelta

import pytest
from django.contrib.auth.models import User
from django.test import Client
from django.utils import timezone

from core.consent_notice import expected_notice_claim
from core.models import AIConsentReceipt, BasePatientProfile
from core.models.d2_notification import (
    D2Notification,
    D2ProactiveEmissionReceipt,
)
from core.models.locale import PatientLocalePreference

ROOT = "/api/v1/account/notifications"


def send(client, method, url, *, payload=None, csrf=None):
    kwargs = {}
    if payload is not None:
        kwargs.update(data=json.dumps(payload), content_type="application/json")
    if csrf is not None:
        kwargs["HTTP_X_CSRFTOKEN"] = csrf
    return getattr(client, method)(url, **kwargs)


def create_notice(patient, key, *, expires_at=None):
    now = timezone.now()
    return D2Notification.objects.create(
        patient=patient, kind="event", code="ai_consent_given",
        event_key=key * 64, created_at=now,
        expires_at=expires_at or (now + timedelta(days=2)),
    )


@pytest.mark.django_db
def test_fue_01_http_identity_switch_read_delete_csrf_a_b_a():
    a = User.objects.create_user(username="fue_d2_user_a")
    b = User.objects.create_user(username="fue_d2_user_b")
    a_notice = create_notice(a, "a")
    b_notice = create_notice(b, "b")
    client = Client(enforce_csrf_checks=True)
    assert client.get(ROOT).status_code in (401, 403)

    client.force_login(a)
    a_first = client.get(ROOT)
    assert a_first.status_code == 200
    assert [r["id"] for r in a_first.json()["items"]] == [a_notice.pk]
    assert a_first.json()["unread_count"] == 1
    assert a_first.json()["proactive_opt_in"] is False
    assert a_first.json()["browser_push_enabled"] is False
    a_token = a_first.json()["csrf_token"]
    assert send(client, "put", f"{ROOT}/{a_notice.pk}/read", payload={}).status_code == 403
    assert send(client, "put", f"{ROOT}/{a_notice.pk}/read", payload={}, csrf=a_token).status_code == 200
    assert client.get(ROOT).json()["unread_count"] == 0

    client.force_login(b)
    b_first = client.get(ROOT)
    assert b_first.status_code == 200
    assert [r["id"] for r in b_first.json()["items"]] == [b_notice.pk]
    b_token = b_first.json()["csrf_token"]
    assert send(client, "put", f"{ROOT}/{a_notice.pk}/read", payload={}, csrf=b_token).status_code == 404
    assert send(client, "delete", f"{ROOT}/{a_notice.pk}", csrf=b_token).status_code == 404
    assert send(client, "post", f"{ROOT}/read-all", payload={}, csrf=b_token).json()["updated"] == 1
    assert D2Notification.objects.get(pk=a_notice.pk).read_at is not None
    assert client.get(ROOT, HTTP_AUTHORIZATION="Bearer forged").status_code in (401, 403)

    client.force_login(a)
    a_again = client.get(ROOT)
    assert [r["id"] for r in a_again.json()["items"]] == [a_notice.pk]
    assert a_again.json()["unread_count"] == 0
    a_token = a_again.json()["csrf_token"]
    assert send(client, "delete", f"{ROOT}/{a_notice.pk}", csrf=a_token).status_code == 200
    assert client.get(ROOT).json()["items"] == []
    client.force_login(b)
    assert [r["id"] for r in client.get(ROOT).json()["items"]] == [b_notice.pk]


@pytest.mark.django_db
def test_fue_02_optin_fr_en_ar_off_on_dedup_and_forbid_spoof():
    a = User.objects.create_user(username="fue_d2_optin_a")
    b = User.objects.create_user(username="fue_d2_optin_b")
    profile = BasePatientProfile.objects.create(patient=a)
    PatientLocalePreference.objects.create(
        profile=profile, ui_language="fr", ui_language_provenance="defaulted",
    )
    client = Client(enforce_csrf_checks=True)
    client.force_login(a)
    for locale in ("fr", "en", "ar"):
        response = client.get(ROOT, {"locale": locale})
        assert response.status_code == 200
        assert response.json()["consent"]["locale"] == locale
        assert response.json()["items"] == []
    first = client.get(ROOT, {"locale": "ar"}).json()
    token = first["csrf_token"]
    grant = dict(
        locale="ar", notice_version=first["consent"]["notice_version"],
        notice_digest=first["consent"]["notice_digest"],
        acknowledgment="ENABLE_D2_IN_APP_PROACTIVITY",
    )
    assert send(client, "put", ROOT + "/proactivity", payload=grant).status_code == 403
    assert send(client, "put", ROOT + "/proactivity",
                payload={**grant, "notice_version": "stale"}, csrf=token).status_code == 422
    assert send(client, "put", ROOT + "/proactivity",
                payload={**grant, "patient_id": b.pk}, csrf=token).status_code == 422

    on = send(client, "put", ROOT + "/proactivity", payload=grant, csrf=token)
    assert on.status_code == 200, (on.status_code, on.content[:250])
    assert on.json()["proactive_opt_in"] is True
    assert [x["code"] for x in on.json()["items"]] == ["language_pref_available"]
    assert D2ProactiveEmissionReceipt.objects.filter(patient=a).count() == 1
    off = send(client, "delete", ROOT + "/proactivity", csrf=token)
    assert off.status_code == 200
    assert off.json()["proactive_opt_in"] is False
    assert off.json()["items"] == []
    assert D2Notification.objects.filter(patient=a, kind="proactive").count() == 0
    assert D2ProactiveEmissionReceipt.objects.filter(patient=a).count() == 1

    client.logout()
    client.force_login(a)
    token = client.get(ROOT).json()["csrf_token"]
    again = send(client, "put", ROOT + "/proactivity", payload=grant, csrf=token)
    assert again.status_code == 200
    assert again.json()["proactive_opt_in"] is True
    assert again.json()["items"] == []
    assert D2ProactiveEmissionReceipt.objects.filter(patient=a).count() == 1
    client.force_login(b)
    assert client.get(ROOT).json()["items"] == []
    assert client.get(ROOT).json()["proactive_opt_in"] is False


@pytest.mark.django_db(transaction=True)
def test_fue_03_real_account_consent_http_emits_factual_events(monkeypatch):
    # on_commit callbacks must actually execute, hence transaction=True.
    monkeypatch.setattr("core.api.v1.account.record_audit", lambda *args, **kw: None)
    a = User.objects.create_user(username="fue_d2_consent_a")
    b = User.objects.create_user(username="fue_d2_consent_b")
    client = Client(enforce_csrf_checks=True)
    client.force_login(a)
    assert client.get(ROOT).json()["items"] == []
    claim = expected_notice_claim("fr")
    csrf = client.get(ROOT).json()["csrf_token"]
    body = {
        "notice_version": claim.version,
        "notice_hash": claim.notice_hash,
        "locale": claim.locale,
    }
    grant = send(client, "post", "/api/v1/account/consent", payload=body, csrf=csrf)
    assert grant.status_code == 200, (grant.status_code, grant.content[:250])
    assert grant.json()["ai_consent_given"] is True
    assert [x["code"] for x in client.get(ROOT).json()["items"]] == ["ai_consent_given"]
    assert AIConsentReceipt.objects.filter(patient=a, revoked_at__isnull=True).count() == 1
    withdrawn = send(client, "delete", "/api/v1/account/consent", csrf=csrf)
    assert withdrawn.status_code == 200, (withdrawn.status_code, withdrawn.content[:250])
    assert withdrawn.json()["ai_consent_given"] is False
    assert {x["code"] for x in client.get(ROOT).json()["items"]} == {
        "ai_consent_given", "ai_consent_withdrawn",
    }
    client.force_login(b)
    assert client.get(ROOT).json()["items"] == []
