"""Persistent native-auth abuse protection regression tests."""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from datetime import timezone as dt_timezone

import pytest
from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import RequestDataTooBig
from django.http import JsonResponse
from django.test import RequestFactory, override_settings

from core.middleware.auth_abuse import AuthAbuseProtectionMiddleware
from core.models import AuthAbuseBucket


def _middleware():
    return AuthAbuseProtectionMiddleware(
        lambda request: JsonResponse({"detail": "accepted"}, status=202)
    )


def _post(path: str, *, email: str, ip: str, forwarded_for: str | None = None):
    extra = {"REMOTE_ADDR": ip}
    if forwarded_for is not None:
        extra["HTTP_X_FORWARDED_FOR"] = forwarded_for
    return RequestFactory().post(
        path,
        data=json.dumps({"email": email, "password": "not-relevant"}),
        content_type="application/json",
        **extra,
    )


@pytest.mark.django_db
@override_settings(
    AUTH_ABUSE_LIMITS={
        "login_ip": {"limit": 2, "window_seconds": 60},
        "login_account": {"limit": 100, "window_seconds": 60},
    }
)
def test_repeated_login_is_rate_limited_with_typed_429():
    middleware = _middleware()
    path = "/api/v1/auth/login"

    assert middleware(_post(path, email="patient@example.test", ip="198.51.100.10")).status_code == 202
    assert middleware(_post(path, email="patient@example.test", ip="198.51.100.10")).status_code == 202
    limited = middleware(_post(path, email="patient@example.test", ip="198.51.100.10"))

    assert limited.status_code == 429
    assert json.loads(limited.content)["error"] == {
        "code": "auth_rate_limited",
        "message": "Too many authentication attempts. Try again later.",
        "retryable": True,
    }
    assert 1 <= int(limited["Retry-After"]) <= 60


@pytest.mark.django_db
@override_settings(
    AUTH_ABUSE_LIMITS={
        "login_ip": {"limit": 100, "window_seconds": 60},
        "login_account": {"limit": 1, "window_seconds": 60},
    }
)
def test_account_buckets_do_not_cross_contaminate_distinct_accounts():
    middleware = _middleware()
    path = "/api/v1/auth/login"
    ip = "198.51.100.11"

    assert middleware(_post(path, email="alice@example.test", ip=ip)).status_code == 202
    assert middleware(_post(path, email="alice@example.test", ip=ip)).status_code == 429
    assert middleware(_post(path, email="bob@example.test", ip=ip)).status_code == 202


@pytest.mark.django_db
@override_settings(
    AUTH_ABUSE_LIMITS={
        "password_reset_ip": {"limit": 100, "window_seconds": 60},
        "password_reset_account": {"limit": 1, "window_seconds": 60},
    }
)
def test_password_reset_throttle_does_not_depend_on_account_existence():
    User.objects.create_user(
        username="existing@example.test",
        email="existing@example.test",
        password="A-strong-passphrase-2026!",
    )
    middleware = _middleware()
    path = "/api/v1/auth/password/reset/request"

    for email, ip in (
        ("existing@example.test", "198.51.100.12"),
        ("missing@example.test", "198.51.100.13"),
    ):
        assert middleware(_post(path, email=email, ip=ip)).status_code == 202
        limited = middleware(_post(path, email=email, ip=ip))
        assert limited.status_code == 429
        assert json.loads(limited.content)["error"]["code"] == "auth_rate_limited"


@pytest.mark.django_db
@override_settings(
    AUTH_ABUSE_LIMITS={
        "register_ip": {"limit": 100, "window_seconds": 60},
        "register_account": {"limit": 1, "window_seconds": 60},
    }
)
def test_rate_limit_window_recovers_after_expiry(monkeypatch):
    middleware = _middleware()
    path = "/api/v1/auth/register"
    initial = datetime(2026, 9, 14, 8, 0, tzinfo=dt_timezone.utc)
    monkeypatch.setattr("core.auth_abuse.timezone.now", lambda: initial)

    assert middleware(_post(path, email="new@example.test", ip="198.51.100.14")).status_code == 202
    assert middleware(_post(path, email="new@example.test", ip="198.51.100.14")).status_code == 429

    monkeypatch.setattr(
        "core.auth_abuse.timezone.now",
        lambda: initial + timedelta(seconds=61),
    )
    assert middleware(_post(path, email="new@example.test", ip="198.51.100.14")).status_code == 202


@pytest.mark.django_db
@override_settings(
    CACHES={"default": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"}},
    AUTH_ABUSE_LIMITS={
        "register_ip": {"limit": 10, "window_seconds": 60},
        "register_account": {"limit": 10, "window_seconds": 60},
    },
)
def test_limiter_remains_effective_without_redis_and_stores_no_raw_identifiers():
    middleware = _middleware()
    raw_email = "private.patient@example.test"
    raw_ip = "198.51.100.15"
    response = middleware(
        _post("/api/v1/auth/register", email=raw_email, ip=raw_ip)
    )

    assert response.status_code == 202
    buckets = list(AuthAbuseBucket.objects.order_by("scope"))
    assert len(buckets) == 2
    for bucket in buckets:
        assert len(bucket.key_hash) == 64
        assert raw_email not in bucket.key_hash
        assert raw_ip not in bucket.key_hash
        assert bucket.count == 1


@pytest.mark.django_db
@override_settings(
    AUTH_ABUSE_LIMITS={
        "login_ip": {"limit": 1, "window_seconds": 60},
        "login_account": {"limit": 100, "window_seconds": 60},
    }
)
def test_unreadable_body_still_consumes_ip_bucket():
    class UnreadableRequest:
        method = "POST"
        path = "/api/v1/auth/login"
        META = {
            "CONTENT_LENGTH": "0",
            "CONTENT_TYPE": "application/json",
            "REMOTE_ADDR": "198.51.100.16",
        }

        @property
        def body(self):
            raise RequestDataTooBig()

    middleware = _middleware()
    assert middleware(UnreadableRequest()).status_code == 202
    second = _post(
        "/api/v1/auth/login",
        email="patient@example.test",
        ip="198.51.100.16",
    )
    assert middleware(second).status_code == 429


@pytest.mark.django_db
@override_settings(
    AUTH_ABUSE_LIMITS={
        "login_ip": {"limit": 1, "window_seconds": 60},
        "login_account": {"limit": 100, "window_seconds": 60},
    }
)
def test_vercel_forwarded_client_ip_is_the_ip_bucket_key():
    middleware = _middleware()
    path = "/api/v1/auth/login"
    first = _post(
        path,
        email="patient@example.test",
        ip="10.0.0.2",
        forwarded_for="203.0.113.20",
    )
    second = _post(
        path,
        email="other@example.test",
        ip="10.0.0.3",
        forwarded_for="203.0.113.20",
    )

    assert middleware(first).status_code == 202
    assert middleware(second).status_code == 429


def test_auth_abuse_middleware_is_enabled_in_application_stack():
    assert "core.middleware.auth_abuse.AuthAbuseProtectionMiddleware" in settings.MIDDLEWARE
