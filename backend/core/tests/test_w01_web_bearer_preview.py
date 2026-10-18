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
def test_web_password_login_under_csrf_stays_bearer_usable_without_cookie():
    """Django Ninja public login succeeds; BFF must drop server cookies."""
    user, _ = _patient("w01-web-login-csrf")
    with_cookie = Client(enforce_csrf_checks=True)
    response = with_cookie.post(
        "/api/v1/auth/login",
        data=json.dumps({
            "email": "w01-web-login-csrf@example.test",
            "password": "A-strong-passphrase-2026!",
        }),
        content_type="application/json",
    )
    # Ninja handles the anonymous login endpoint. A new CSRF exception is
    # neither needed nor safe to broaden.
    assert response.status_code == 200
    assert "sessionid" in response.cookies
    token = response.json()["access_token"]
    assert token.startswith("iamina.")

    # The BFF does not forward Set-Cookie: verify the actual bearer-only
    # Django HTTP path with a wholly separate client.
    clean_client = Client(enforce_csrf_checks=True)
    assert clean_client.get("/api/v1/auth/me").status_code == 401
    logged_in = clean_client.get("/api/v1/auth/me", **_bearer(token))
    assert logged_in.status_code == 200
    assert logged_in.json()["id"] == user.pk


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
def test_native_bearer_hard_expires_in_one_hour_even_with_legacy_30_day_setting():
    """An accidentally stale runtime setting cannot re-enable month-long access."""
    user, _ = _patient("w01-bounded-session")
    issued_at = 1_800_000_000
    with mock_patch("django.core.signing.time.time", return_value=issued_at):
        token = issue_native_token(user)

    # Reading just inside the hard cap still authenticates without cookies.
    with mock_patch("django.core.signing.time.time", return_value=issued_at + 3599):
        assert Client().get("/api/v1/auth/me", **_bearer(token)).status_code == 200

    # A 30-day legacy override cannot bypass the 1h ceiling.
    with override_settings(NATIVE_AUTH_TOKEN_MAX_AGE_SECONDS=30 * 24 * 3600):
        with mock_patch("django.core.signing.time.time", return_value=issued_at + 3601):
            with pytest.raises(NativeTokenError):
                verify_native_token(token)
            expired = Client().get("/api/v1/auth/me", **_bearer(token))
    assert expired.status_code == 401


@pytest.mark.django_db
def test_expired_bearer_requires_new_password_login_and_never_replays_old_token():
    """Controlled renewal uses password reauthentication, not a 30-day refresh secret."""
    user, _ = _patient("w01-relogin")
    another, _ = _patient("w01-other-session")
    issued_at = 1_800_000_000
    with mock_patch("django.core.signing.time.time", return_value=issued_at):
        old_token = issue_native_token(user)
        other_token = issue_native_token(another)
    with mock_patch("django.core.signing.time.time", return_value=issued_at + 3601):
        isolated = Client(enforce_csrf_checks=True)
        assert isolated.get("/api/v1/auth/me", **_bearer(old_token)).status_code == 401
        # Old Bearer alone cannot be refreshed or elevated into any patient.
        assert isolated.get("/api/v1/auth/me").status_code == 401
        assert isolated.get("/api/v1/auth/me", **_bearer(other_token)).status_code == 401
        denied = isolated.post(
            "/api/v1/auth/login",
            data=json.dumps({
                "email": "w01-relogin@example.test",
                "password": "wrong-password",
            }),
            content_type="application/json",
        )
        assert denied.status_code == 401

        login = isolated.post(
            "/api/v1/auth/login",
            data=json.dumps({
                "email": "w01-relogin@example.test",
                "password": "A-strong-passphrase-2026!",
            }),
            content_type="application/json",
        )
        assert login.status_code == 200
        replacement = login.json()["access_token"]
        assert replacement != old_token
        assert isolated.get("/api/v1/auth/me", **_bearer(replacement)).json()["id"] == user.pk
        # Deliberately new client: login session cookie cannot rescue the old bearer.
        assert Client().get("/api/v1/auth/me", **_bearer(old_token)).status_code == 401
    assert another.pk != user.pk


@pytest.mark.django_db
@pytest.mark.parametrize("invalid_age", [0, -1, "3600", None, True])
def test_native_bearer_invalid_lifetime_configuration_fails_closed(invalid_age):
    _, token = _patient("w01-ttl-invalid")
    with override_settings(NATIVE_AUTH_TOKEN_MAX_AGE_SECONDS=invalid_age):
        with pytest.raises(NativeTokenError):
            verify_native_token(token)
        response = Client().get("/api/v1/auth/me", **_bearer(token))
    assert response.status_code == 401



@pytest.mark.django_db
def test_browser_session_and_forged_bearer_cannot_bypass_csrf_or_revoke_token():
    """A bogus Authorization header cannot turn a session into CSRF-free auth."""
    user, live_token = _patient("w01-dual-auth-cookie")
    client = Client(enforce_csrf_checks=True)
    client.force_login(user)
    assert client.get("/api/v1/auth/me").status_code == 200

    # A forged bearer must not authorize SessionAuth's fallback via a CSRF
    # exemption. No cross-site request should be able to revoke this account.
    denied = client.post(
        "/api/v1/auth/logout",
        **_bearer("iamina.synthetic-invalid-token"),
    )
    assert denied.status_code == 403
    assert verify_native_token(live_token).pk == user.pk
    user.base_profile.refresh_from_db()
    assert user.base_profile.auth_token_version == 0

    # A valid Bearer is an explicit credential and may authenticate before
    # SessionAuth fallback. Only a rejected Bearer must never downgrade into
    # a CSRF-free ambient session.
    # A clean, cookie-free Bearer still revokes successfully.
    isolated = Client(enforce_csrf_checks=True)
    permitted = isolated.post("/api/v1/auth/logout", **_bearer(live_token))
    assert permitted.status_code == 200
    with pytest.raises(NativeTokenError):
        verify_native_token(live_token)


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
        # Without IAMINA Bearer, Django can reject a mutation at the CSRF
        # boundary (403) before its auth boundary (401). Both are fail-closed.
        anonymous_write = client.patch(
            "/api/v1/profile",
            data=json.dumps({"preferred_language": "ar"}),
            content_type="application/json",
        )
        assert anonymous_write.status_code in (401, 403)
        # Status alone is insufficient: prove that the denied write did not
        # change either account's clinical profile in the same client.
        a_after_denial = client.get("/api/v1/profile", **_bearer(a_token))
        b_after_denial = client.get("/api/v1/profile", **_bearer(b_token))
        assert a_after_denial.status_code == 200
        assert b_after_denial.status_code == 200
        assert a_after_denial.json()["preferred_language"] == "fr"
        assert b_after_denial.json()["preferred_language"] == "ar"


@pytest.mark.django_db
def test_bearer_a_b_a_clinical_logs_resource_scope():
    """Real HTTP routes must block read, patch and delete across patients."""
    from diabetes.models import LogEntry

    a, token_a = _patient("w01-log-a")
    b, token_b = _patient("w01-log-b")
    a_log = LogEntry.objects.create(patient=a, blood_sugar=111, source="demo")
    b_log = LogEntry.objects.create(patient=b, blood_sugar=222, source="demo")

    # The shared test configuration patches HybridBearerAuth for session tests.
    # Exercise the real HttpBearer header parser for this isolated clinical case.
    with mock_patch.object(HybridBearerAuth, "__call__", HttpBearer.__call__):
        client = Client(enforce_csrf_checks=True)
        for token, owned, foreign in (
            (token_a, a_log, b_log),
            (token_b, b_log, a_log),
            (token_a, a_log, b_log),
        ):
            own_list = client.get("/api/v1/logs", **_bearer(token))
            assert own_list.status_code == 200
            assert own_list.json()["total"] == 1
            assert [row["id"] for row in own_list.json()["items"]] == [owned.pk]

            own_detail = client.get(f"/api/v1/logs/{owned.pk}", **_bearer(token))
            assert own_detail.status_code == 200
            assert own_detail.json()["id"] == owned.pk
            assert client.get(
                f"/api/v1/logs/{foreign.pk}", **_bearer(token)
            ).status_code == 404

            denied_patch = client.patch(
                f"/api/v1/logs/{foreign.pk}",
                data=json.dumps({"blood_sugar": 333}),
                content_type="application/json",
                **_bearer(token),
            )
            assert denied_patch.status_code == 404
            denied_delete = client.delete(
                f"/api/v1/logs/{foreign.pk}", **_bearer(token)
            )
            assert denied_delete.status_code == 404

        # Denied mutations cannot alter or remove either medical record.
        a_log.refresh_from_db()
        b_log.refresh_from_db()
        assert float(a_log.blood_sugar) == 111
        assert float(b_log.blood_sugar) == 222
        assert LogEntry.objects.filter(pk__in=[a_log.pk, b_log.pk]).count() == 2

        anonymous = client.get("/api/v1/logs")
        assert anonymous.status_code in (401, 403)
        assert "blood_sugar" not in anonymous.content.decode()
