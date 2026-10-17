"""W01 Web Preview contract: native Bearer identity and logout, without session cookies.

Synthetic identities only. Django integration tests do NOT certify hosted SSO,
Vercel OIDC Trusted Sources, browser behaviour, or all patient-resource isolation.
"""
import json
from unittest.mock import patch as mock_patch

import pytest
from django.contrib.auth.models import User
from django.test import Client, override_settings
from ninja.security import HttpBearer

from core.models import BasePatientProfile
from core.native_auth import NativeTokenError, issue_native_token, verify_native_token
from diabetes.api.v1.security import HybridBearerAuth


def _patient(name: str):
    user = User.objects.create_user(
        username=name,
        email=f"{name}@example.test",
        password="A-strong-passphrase-2026!",
    )
    BasePatientProfile.objects.create(patient=user)
    return user, issue_native_token(user)


def _bearer(token: str) -> dict:
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


@pytest.mark.django_db
def test_login_issues_native_bearer_consumable_without_session_cookie():
    _patient("w01-login")
    response = Client().post(
        "/api/v1/auth/login",
        data=json.dumps({
            "email": "w01-login@example.test",
            "password": "A-strong-passphrase-2026!",
        }),
        content_type="application/json",
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    assert token.startswith("iamina.")

    # Deliberately use a new client: login's Django session cookie is absent.
    bare = Client().get("/api/v1/auth/me", **_bearer(token))
    assert bare.status_code == 200
    assert bare.json()["id"] == response.json()["user"]["id"]


@pytest.mark.django_db
def test_bearer_only_a_b_a_identity_isolation_and_no_credential_denial():
    a, a_token = _patient("w01-patient-a")
    b, b_token = _patient("w01-patient-b")
    client = Client()
    for token, expected in ((a_token, a.pk), (b_token, b.pk), (a_token, a.pk)):
        result = client.get("/api/v1/auth/me", **_bearer(token))
        assert result.status_code == 200
        assert result.json()["id"] == expected
    assert client.get("/api/v1/auth/me").status_code == 401
    assert client.get(
        "/api/v1/auth/me",
        **_bearer(a_token + "tampered"),
    ).status_code == 401


@pytest.mark.django_db
def test_bearer_logout_revokes_token_and_prevents_replay():
    user, token = _patient("w01-logout")
    isolated = Client(enforce_csrf_checks=True)
    response = isolated.post("/api/v1/auth/logout", **_bearer(token))
    assert response.status_code == 200
    assert response.json()["detail"] == "Signed out"
    with pytest.raises(NativeTokenError):
        verify_native_token(token)
    assert isolated.get("/api/v1/auth/me", **_bearer(token)).status_code == 401
    user.base_profile.refresh_from_db()
    assert user.base_profile.auth_token_version == 1


@pytest.mark.django_db
def test_expired_bearer_is_denied_without_falling_back_to_session():
    _, token = _patient("w01-expired")
    with override_settings(NATIVE_AUTH_TOKEN_MAX_AGE_SECONDS=-1):
        response = Client().get("/api/v1/auth/me", **_bearer(token))
    assert response.status_code == 401


@pytest.mark.django_db
def test_existing_django_session_still_reads_identity_but_logout_requires_csrf():
    user, token = _patient("w01-session")
    session_client = Client(enforce_csrf_checks=True)
    session_client.force_login(user)
    response = session_client.get("/api/v1/auth/me")
    assert response.status_code == 200
    assert response.json()["id"] == user.pk
    denied = session_client.post("/api/v1/auth/logout")
    assert denied.status_code == 403
    assert verify_native_token(token).pk == user.pk


@pytest.mark.django_db
def test_sensitive_auth_operations_no_longer_accept_anonymous_requests():
    client = Client()
    assert client.get("/api/v1/auth/me").status_code == 401
    for method, path, payload in (
        ("post", "/api/v1/auth/logout", {}),
        ("post", "/api/v1/auth/password", {"new_password": "passphrase"}),
        ("post", "/api/v1/auth/firebase/link", {"id_token": "fake"}),
        ("delete", "/api/v1/auth/firebase/link", None),
    ):
        args = {"content_type": "application/json"}
        if payload is not None:
            args["data"] = json.dumps(payload)
        response = getattr(client, method)(path, **args)
        assert response.status_code in (401, 403), (method, path, response.status_code)

@pytest.mark.django_db
def test_bearer_a_b_a_profile_read_write_stays_patient_scoped():
    """Medical profile mutations must not jump between two Bearer identities."""
    from diabetes.models import DiabetesProfile

    a, a_token = _patient("w01-clinical-a")
    b, b_token = _patient("w01-clinical-b")
    DiabetesProfile.objects.get_or_create(base_profile=a.base_profile)
    DiabetesProfile.objects.get_or_create(base_profile=b.base_profile)

    # backend/conftest.py intentionally patches the global HybridBearerAuth
    # adapter to support legacy force_login tests. Restore the real Ninja
    # HttpBearer parser ONLY for this explicit Bearer A/B integration case.
    with mock_patch.object(HybridBearerAuth, "__call__", HttpBearer.__call__):
        client = Client(enforce_csrf_checks=True)
        a_write = client.patch(
            "/api/v1/profile",
            data=json.dumps({"preferred_language": "fr"}),
            content_type="application/json",
            **_bearer(a_token),
        )
        assert a_write.status_code == 200
        assert a_write.json()["preferred_language"] == "fr"

        # Same HTTP client, but only B's Bearer now authorizes this operation.
        b_read = client.get("/api/v1/profile", **_bearer(b_token))
        assert b_read.status_code == 200
        assert b_read.json()["preferred_language"] != "fr"

        b_write = client.patch(
            "/api/v1/profile",
            data=json.dumps({"preferred_language": "ar"}),
            content_type="application/json",
            **_bearer(b_token),
        )
        assert b_write.status_code == 200
        assert b_write.json()["preferred_language"] == "ar"

        a_again = client.get("/api/v1/profile", **_bearer(a_token))
        assert a_again.status_code == 200
        assert a_again.json()["preferred_language"] == "fr"
        assert client.get("/api/v1/profile").status_code == 401
        assert client.patch(
            "/api/v1/profile",
            data=json.dumps({"preferred_language": "ar"}),
            content_type="application/json",
        ).status_code == 401
