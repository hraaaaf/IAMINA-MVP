"""W01 synthetic PostgreSQL HTTP proof: bearer logout and patient ownership.

Runs only in GitHub Actions ephemeral PG16. No Vercel, Neon or real patient data.
"""
import json

import pytest
from django.contrib.auth.models import User
from django.test import Client
from django.utils import timezone

from core.models import BasePatientProfile
from core.native_auth import issue_native_token, verify_native_token
from diabetes.models import LogEntry
from diabetes.api.v1.security import firebase_auth_backend


def _login(user, password):
    response = Client().post(
        "/api/v1/auth/login",
        data=json.dumps({"email": user.email, "password": password}),
        content_type="application/json",
    )
    assert response.status_code == 200, response.content[:250]
    payload = response.json()
    assert payload["user"]["id"] == user.pk
    return payload["access_token"]


def _as(token, method, path, body=None):
    client = Client()  # Deliberately no Django session cookie.
    kwargs = {"HTTP_AUTHORIZATION": f"Bearer {token}"}
    if body is not None:
        kwargs["data"] = json.dumps(body)
        kwargs["content_type"] = "application/json"
    return getattr(client, method)(path, **kwargs)


@pytest.mark.django_db
def test_w01_http_logout_revokes_bearer_without_cookie_and_keeps_b_private():
    password = "Synthetic-Strong-Passphrase-W01-2026!"
    a = User.objects.create_user(
        username="w01-http-a", email="w01-http-a@example.invalid", password=password
    )
    b = User.objects.create_user(
        username="w01-http-b", email="w01-http-b@example.invalid", password=password
    )
    token_a = _login(a, password)
    token_b = _login(b, password)
    first_a = LogEntry.objects.create(
        patient=a, blood_sugar=112, logged_at=timezone.now()
    )
    first_b = LogEntry.objects.create(
        patient=b, blood_sugar=191, logged_at=timezone.now()
    )

    # Verify a freshly-issued bearer before testing the HTTP adapter.
    assert verify_native_token(token_a).pk == a.pk
    assert verify_native_token(token_b).pk == b.pk
    only_a = _as(token_a, "get", "/api/v1/logs")
    only_b = _as(token_b, "get", "/api/v1/logs")
    assert "HTTP_AUTHORIZATION" in only_a.wsgi_request.META
    # Diagnostic split (not a bypass): distinguish token verification,
    # HttpBearer header extraction, and Ninja router dispatch. Never emit tokens.
    direct = firebase_auth_backend.authenticate(only_a.wsgi_request, token_a)
    assert direct is not None and direct.pk == a.pk, "HybridBearerAuth.authenticate rejected valid A"
    callback = firebase_auth_backend(only_a.wsgi_request)
    assert callback is not None and callback.pk == a.pk, "HttpBearer.__call__ did not extract header"
    assert only_a.status_code == 200, only_a.content[:250]
    assert only_b.status_code == 200, only_b.content[:250]
    assert [item["id"] for item in only_a.json()["items"]] == [first_a.pk]
    assert [item["id"] for item in only_b.json()["items"]] == [first_b.pk]

    assert _as(token_b, "get", f"/api/v1/logs/{first_a.pk}").status_code == 404
    assert _as(
        token_b, "patch", f"/api/v1/logs/{first_a.pk}", {"blood_sugar": 450}
    ).status_code == 404
    assert _as(token_b, "delete", f"/api/v1/logs/{first_a.pk}").status_code == 404
    first_a.refresh_from_db()
    assert first_a.blood_sugar == 112

    # The W01 cross-project Web proxy sends Authorization, never cookies.
    logged_out = _as(token_a, "post", "/api/v1/auth/logout")
    assert logged_out.status_code == 200, logged_out.content[:250]
    assert BasePatientProfile.objects.get(patient=a).auth_token_version == 1
    assert BasePatientProfile.objects.get(patient=b).auth_token_version == 0
    assert _as(token_a, "get", "/api/v1/logs").status_code == 401
    assert _as(token_b, "get", "/api/v1/logs").status_code == 200

    # A may re-enrol with a new bearer; it never inherits B's clinical data.
    fresh_a = _login(a, password)
    assert _as(fresh_a, "get", f"/api/v1/logs/{first_a.pk}").status_code == 200
    assert _as(fresh_a, "get", f"/api/v1/logs/{first_b.pk}").status_code == 404

    assert _as(token_b, "post", "/api/v1/auth/logout").status_code == 200
    assert BasePatientProfile.objects.get(patient=b).auth_token_version == 1
    assert _as(token_b, "get", "/api/v1/logs").status_code == 401
    assert _as(fresh_a, "get", "/api/v1/logs").status_code == 200


@pytest.mark.django_db
def test_w01_logout_invalid_or_conflicting_bearer_fails_closed():
    a = User.objects.create_user(username="w01-guard-a", email="guard-a@example.invalid")
    b = User.objects.create_user(username="w01-guard-b", email="guard-b@example.invalid")
    bearer_a = issue_native_token(a)
    # The test fixture for B must explicitly create B's profile; force_login
    # creates a Django session but must not fabricate an IAMINA patient.
    BasePatientProfile.objects.get_or_create(patient=b)

    bad = _as(bearer_a + "tampered", "post", "/api/v1/auth/logout")
    assert bad.status_code == 401
    assert BasePatientProfile.objects.get(patient=a).auth_token_version == 0

    # A cookie for B must never revoke A's bearer or B's account.
    mixed = Client()
    mixed.force_login(b)
    conflict = mixed.post(
        "/api/v1/auth/logout", HTTP_AUTHORIZATION=f"Bearer {bearer_a}"
    )
    assert conflict.status_code == 401
    assert BasePatientProfile.objects.get(patient=a).auth_token_version == 0
    assert BasePatientProfile.objects.get(patient=b).auth_token_version == 0

    # Preserve a legitimate legacy cookie-only logout.
    cookie_only = mixed.post("/api/v1/auth/logout")
    assert cookie_only.status_code == 200
    assert BasePatientProfile.objects.get(patient=b).auth_token_version == 1
