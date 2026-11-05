"""W01 synthetic PostgreSQL HTTP proof: bearer logout and patient ownership.

Runs only in GitHub Actions ephemeral PG16. No Vercel, Neon or real patient data.
"""
import json

import pytest
from django.contrib.auth.models import User
from django.test import Client
from django.utils import timezone
from ninja.operation import Operation

from amina.vercel_session_auth import SessionAuth
from core.models import BasePatientProfile
from core.native_auth import issue_native_token, verify_native_token
from diabetes.api.v1.security import HybridBearerAuth
from diabetes.models import LogEntry


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
def test_w01_every_logs_operation_explicitly_requires_bearer_or_session():
    from diabetes.api.v1.logs import router as logs_router

    operations = [
        op for view in logs_router.path_operations.values()
        for op in view.operations
    ]
    assert len(operations) == 6
    for op in operations:
        names = [type(callback).__name__ for callback in (op.auth_callbacks or [])]
        assert names == ["HybridBearerAuth", "SessionAuth"], names

@pytest.mark.django_db(transaction=True)
def test_w01_http_logout_revokes_bearer_without_cookie_and_keeps_b_private(monkeypatch):
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
    # Diagnose the operation that actually answers the HTTP request; no
    # auth headers, bearer values, or patient data may enter CI logs.
    observed_callbacks = []
    original_run_authentication = Operation._run_authentication

    def trace_operation(self, request):
        observed_callbacks.append(
            (self.path, [type(cb).__name__ for cb in self.auth_callbacks])
        )
        return original_run_authentication(self, request)

    monkeypatch.setattr(Operation, "_run_authentication", trace_operation)
    # Preserve each callback's exact behavior, observing only boolean success
    # and exception class, never tokens or session/cookie values.
    outcomes = []
    original_bearer_call = HybridBearerAuth.__call__
    original_session_call = SessionAuth.__call__

    def trace_bearer(self, request):
        try:
            # Only metadata booleans, no credentials: determine whether Ninja's
            # HttpBearer sees the correct scheme and actual native credential.
            header = request.headers.get("Authorization") or ""
            shape = (
                bool(header),
                header.lower().startswith("bearer "),
                self.header,
                self.openapi_scheme,
                header.partition(" ")[2].startswith("iamina."),
                header.partition(" ")[2] in (token_a, token_b),
            )
            value = original_bearer_call(self, request)
            outcomes.append(("bearer", bool(value), shape))
            return value
        except Exception as exc:
            outcomes.append(("bearer_error", type(exc).__name__))
            raise

    def trace_session(self, request):
        try:
            value = original_session_call(self, request)
            outcomes.append(("session", bool(value), "Authorization" in request.headers))
            return value
        except Exception as exc:
            outcomes.append(("session_error", type(exc).__name__))
            raise

    monkeypatch.setattr(HybridBearerAuth, "__call__", trace_bearer)
    monkeypatch.setattr(SessionAuth, "__call__", trace_session)

    # Verify token inside Ninja's callback context without logging any
    # credential, patient data, header or user identity beyond synthetic IDs.
    seen_native = []
    original_authenticate = HybridBearerAuth.authenticate

    def trace_native_authenticate(self, request, candidate):
        try:
            verified = verify_native_token(candidate).pk
        except Exception as exc:
            verified = type(exc).__name__
        try:
            principal = original_authenticate(self, request, candidate)
        except Exception as exc:
            seen_native.append((verified, type(exc).__name__))
            raise
        seen_native.append((verified, principal.pk if principal else None))
        return principal

    monkeypatch.setattr(HybridBearerAuth, "authenticate", trace_native_authenticate)
    only_a = _as(token_a, "get", "/api/v1/logs")
    only_b = _as(token_b, "get", "/api/v1/logs")
    print("W01_HTTP_AUTH_OPERATIONS", observed_callbacks)
    print("W01_HTTP_AUTH_CALLBACK_OUTCOMES", outcomes)
    print("W01_NATIVE_VERIFY_IN_CALLBACK", seen_native)
    assert observed_callbacks, "No Ninja operation performed authentication"
    assert "HTTP_AUTHORIZATION" in only_a.wsgi_request.META
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
