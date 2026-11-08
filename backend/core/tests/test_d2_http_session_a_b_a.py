"""Independent HTTP session A→B→A isolation for the D2 account inbox.

Exercises Django middleware + Ninja routing + CSRF, not direct view calls.
All identities and content are synthetic; no hosted patient data.
"""
from datetime import timedelta

import pytest
from django.contrib.auth.models import User
from django.test import Client
from django.utils import timezone

from core.models.d2_notification import D2Notification


@pytest.mark.django_db
def test_d2_real_http_session_a_b_a_read_write_csrf():
    a = User.objects.create_user(username="audit_d2_patient_a")
    b = User.objects.create_user(username="audit_d2_patient_b")
    now = timezone.now()
    notice = D2Notification.objects.create(
        patient=a,
        kind="event",
        code="ai_consent_given",
        event_key="a" * 64,
        created_at=now,
        expires_at=now + timedelta(days=2),
    )
    path = "/api/v1/account/notifications"
    client = Client(enforce_csrf_checks=True)

    anon = client.get(path)
    assert anon.status_code in (401, 403), (anon.status_code, anon.content[:200])

    client.force_login(a)
    first = client.get(path)
    assert first.status_code == 200, (first.status_code, first.content[:300])
    assert [row["id"] for row in first.json()["items"]] == [notice.pk]
    assert first.json()["unread_count"] == 1
    token_a = first.json()["csrf_token"]
    assert token_a

    missing_csrf = client.post(
        path + "/read-all",
        data="{}",
        content_type="application/json",
    )
    assert missing_csrf.status_code == 403
    mark_all = client.post(
        path + "/read-all",
        data="{}",
        content_type="application/json",
        HTTP_X_CSRFTOKEN=token_a,
    )
    assert mark_all.status_code == 200, (mark_all.status_code, mark_all.content[:300])
    assert mark_all.json()["updated"] == 1

    client.force_login(b)
    other = client.get(path)
    assert other.status_code == 200, (other.status_code, other.content[:300])
    assert other.json()["items"] == []
    token_b = other.json()["csrf_token"]
    assert token_b
    denied = client.put(
        path + f"/{notice.pk}/read",
        data="{}",
        content_type="application/json",
        HTTP_X_CSRFTOKEN=token_b,
    )
    assert denied.status_code == 404, (denied.status_code, denied.content[:300])
    bearer_collision = client.get(
        path,
        HTTP_AUTHORIZATION="Bearer forged-identity",
    )
    assert bearer_collision.status_code in (401, 403)

    client.force_login(a)
    again = client.get(path)
    assert again.status_code == 200
    assert [row["id"] for row in again.json()["items"]] == [notice.pk]
    assert again.json()["unread_count"] == 0
