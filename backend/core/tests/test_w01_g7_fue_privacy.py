"""W01/G7 security/privacy FUE negatives on ephemeral PostgreSQL."""
import json

import pytest
from django.contrib.auth.models import User
from django.test import Client

from core.models import BasePatientProfile
from core.native_auth import issue_native_token


@pytest.mark.django_db
def test_g7_preview_registration_is_403_before_patient_write(monkeypatch):
    monkeypatch.setenv("IAMINA_ENV", "preview")
    monkeypatch.delenv("IAMINA_PREVIEW_ALLOW_REGISTRATION", raising=False)
    before = (User.objects.count(), BasePatientProfile.objects.count())
    response = Client().post(
        "/api/v1/auth/register",
        data=json.dumps({
            "email": "g7-unwanted@example.invalid",
            "password": "This-Synthetic-Password-Is-Long-Enough-2026!",
            "first_name": "Synthetic", "last_name": "Only",
        }),
        content_type="application/json",
    )
    assert response.status_code == 403
    assert (User.objects.count(), BasePatientProfile.objects.count()) == before


@pytest.mark.django_db
def test_g7_invalid_bearer_or_cross_patient_cookie_cannot_authorize():
    a = User.objects.create_user(username="g7-cookie-a", email="g7-a@example.invalid")
    b = User.objects.create_user(username="g7-cookie-b", email="g7-b@example.invalid")
    BasePatientProfile.objects.get_or_create(patient=a)
    BasePatientProfile.objects.get_or_create(patient=b)
    client = Client()
    client.force_login(b)
    assert client.get(
        "/api/v1/account/consent",
        HTTP_AUTHORIZATION="Bearer invalid-w01-g7",
    ).status_code == 401
    assert client.get(
        "/api/v1/account/consent",
        HTTP_AUTHORIZATION="Bearer " + issue_native_token(a),
    ).status_code == 401
    assert client.get("/api/v1/account/consent").status_code == 200


@pytest.mark.django_db
def test_g7_session_cookie_write_without_csrf_rejected(monkeypatch):
    user = User.objects.create_user(username="g7-csrf-a", email="g7-csrf-a@example.invalid")
    BasePatientProfile.objects.get_or_create(patient=user)
    # The repository-wide legacy force_login fixture short-circuits the real
    # Bearer callback for cookie sessions. Restore its production method in
    # THIS negative test; otherwise the fake callback masks CSRF protection.
    from ninja.security import HttpBearer

    from core.consent_notice import expected_notice_claim
    from diabetes.api.v1.security import FirebaseAuth

    monkeypatch.setattr(FirebaseAuth, "__call__", HttpBearer.__call__)
    client = Client(enforce_csrf_checks=True)
    client.force_login(user)
    claim = expected_notice_claim("fr")
    body = {
        "notice_version": claim.version,
        "notice_hash": claim.notice_hash,
        "locale": claim.locale,
    }
    response = client.post(
        "/api/v1/account/consent",
        data=json.dumps(body),
        content_type="application/json",
    )
    assert response.status_code == 403, response.content[:250]
    assert BasePatientProfile.objects.get(patient=user).ai_consent_given_at is None
