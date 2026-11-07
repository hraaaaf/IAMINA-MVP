"""W02-F09: characterize Django cookie and native bearer as two authorities.

Real HTTP through Django/Ninja against isolated CI PostgreSQL; synthetic
identities only. F08 now tests a candidate absolute cookie lifetime tied to
the bearer policy. Renewal, BFF cookies and full session UX remain UNAPPROVED.
"""

from __future__ import annotations

import json
import time
from datetime import timedelta
from unittest.mock import patch

import pytest
from django.conf import settings
from django.contrib.auth.models import User
from django.middleware.csrf import get_token
from django.test import Client, RequestFactory, override_settings
from django.utils import timezone

from core.native_auth import (
    NATIVE_SESSION_ISSUED_AT_KEY,
    NativeTokenError,
    issue_native_token,
    verify_native_token,
)
from diabetes.models import LogEntry

_LOGS = "/api/v1/logs"


def _login(*, suffix: str):
    user = User.objects.create_user(
        username=f"f09-{suffix}",
        email=f"f09-{suffix}@example.invalid",
        password="Synthetic-Only-F09-2026!",
    )
    client = Client()
    response = client.post(
        "/api/v1/auth/login",
        data=json.dumps(
            {"email": user.email, "password": "Synthetic-Only-F09-2026!"}
        ),
        content_type="application/json",
    )
    assert response.status_code == 200, response.content[:200]
    bearer = response.json()["access_token"]
    assert bearer.startswith("iamina.")
    assert settings.SESSION_COOKIE_NAME in client.cookies
    assert NATIVE_SESSION_ISSUED_AT_KEY in client.session
    return client, user, bearer


@pytest.mark.django_db(transaction=True)
def test_w02_f09_native_login_creates_parallel_bearer_and_cookie_authorities():
    client, _, bearer = _login(suffix="dual")

    assert Client().get(
        _LOGS, HTTP_AUTHORIZATION=f"Bearer {bearer}"
    ).status_code == 200
    # Characterization of existing DIRECT Django API; the synthetic Preview
    # BFF strips both request Cookie and response Set-Cookie.
    assert client.get(_LOGS).status_code == 200


@pytest.mark.django_db(transaction=True)
def test_w02_f09_expired_bearer_cannot_fall_back_to_native_login_cookie():
    client, _, bearer = _login(suffix="expiry")
    assert client.get(_LOGS).status_code == 200

    # Both credentials were issued by one login. Advance BOTH independent
    # server clocks: Django signs bearer seconds with signing.time.time and
    # compares database session expiry with django.utils.timezone.now.
    # Patching only one would produce an artificial cookie-only bypass.
    now = timezone.now()
    with (
        patch("django.core.signing.time.time", return_value=time.time() + 840),
        patch("django.utils.timezone.now", return_value=now + timedelta(seconds=840)),
    ):
        assert client.get(_LOGS).status_code == 200
        assert Client().get(
            _LOGS, HTTP_AUTHORIZATION=f"Bearer {bearer}"
        ).status_code == 200

    with (
        patch("django.core.signing.time.time", return_value=time.time() + 960),
        patch("django.utils.timezone.now", return_value=now + timedelta(seconds=960)),
    ):
        expired_with_cookie = client.get(
            _LOGS, HTTP_AUTHORIZATION=f"Bearer {bearer}"
        )
        expired_bearer_only = Client().get(
            _LOGS, HTTP_AUTHORIZATION=f"Bearer {bearer}"
        )
        cookie_only = client.get(_LOGS)

    assert expired_with_cookie.status_code == 401
    assert expired_bearer_only.status_code == 401
    assert cookie_only.status_code == 401


@pytest.mark.django_db(transaction=True)
def test_w02_f08_legacy_unbounded_cookie_cannot_access_clinical_api():
    user = User.objects.create_user(
        username="f08-pre-policy-cookie",
        email="f08-pre-policy-cookie@example.invalid",
        password="Synthetic-only-F08-Legacy!",
    )
    # Simulate a still-live Django cookie from a deployment before F08.
    # Old cookies have no server-issued native-login issued-at marker.
    old = Client(enforce_csrf_checks=True)
    old.force_login(user)
    assert settings.SESSION_COOKIE_NAME in old.cookies
    assert NATIVE_SESSION_ISSUED_AT_KEY not in old.session

    assert old.get(_LOGS).status_code == 401
    assert old.get("/api/v1/auth/me").status_code == 401

    # A valid CSRF token is NOT an authorization credential and must not
    # resuscitate this 14-day legacy cookie for clinical mutation.
    csrf_request = RequestFactory().get(_LOGS)
    masked_token = get_token(csrf_request)
    old.cookies[settings.CSRF_COOKIE_NAME] = csrf_request.META["CSRF_COOKIE"]
    before_rows = LogEntry.objects.filter(patient=user).count()
    response = old.post(
        _LOGS,
        data=json.dumps({"blood_sugar": 110}),
        content_type="application/json",
        HTTP_X_CSRFTOKEN=masked_token,
    )
    assert response.status_code == 401, response.content[:200]
    assert LogEntry.objects.filter(patient=user).count() == before_rows


@pytest.mark.django_db(transaction=True)
def test_w02_f08_invalid_native_session_provenance_fails_closed():
    client, _, _ = _login(suffix="malformed-expiry")
    session = client.session
    session[NATIVE_SESSION_ISSUED_AT_KEY] = "not-a-verified-login-timestamp"
    session.save()
    assert client.get(_LOGS).status_code == 401


@pytest.mark.django_db(transaction=True)
def test_w02_f08_native_login_policy_shortened_after_issuance_still_denies():
    client, _, _ = _login(suffix="policy-shortened-later")
    now = timezone.now()
    with (
        override_settings(NATIVE_AUTH_TOKEN_MAX_AGE_SECONDS=3 * 60),
        patch("django.utils.timezone.now", return_value=now + timedelta(seconds=240)),
    ):
        # Original cookie would still be valid for 900 seconds if F08 only
        # set expiry once; the live policy must also enforce a new shorter cap.
        response = client.get(_LOGS)
    assert response.status_code == 401, response.content[:200]


@pytest.mark.django_db(transaction=True)
def test_w02_f08_native_cookie_expiry_does_not_slide_on_session_save():
    client, _, _ = _login(suffix="absolute-not-sliding")
    now = timezone.now()
    with patch("django.utils.timezone.now", return_value=now + timedelta(seconds=840)):
        assert client.get(_LOGS).status_code == 200
        session = client.session
        session["test_only_session_touch"] = "synthetic"
        session.save()
    with patch("django.utils.timezone.now", return_value=now + timedelta(seconds=960)):
        assert client.get(_LOGS).status_code == 401


@pytest.mark.django_db(transaction=True)
def test_w02_f09_invalid_bearer_and_conflicting_cookie_fail_closed():
    client, _, bearer = _login(suffix="cookie-a")
    other = User.objects.create_user(
        username="f09-cookie-b",
        email="f09-cookie-b@example.invalid",
        password="Synthetic-Only-F09-2026!",
    )
    other_bearer = issue_native_token(other)

    assert client.get(
        _LOGS, HTTP_AUTHORIZATION=f"Bearer {bearer}corrupted"
    ).status_code == 401
    assert client.get(
        _LOGS, HTTP_AUTHORIZATION=f"Bearer {other_bearer}"
    ).status_code == 401
    assert client.get(
        _LOGS, HTTP_AUTHORIZATION=f"Bearer {bearer}"
    ).status_code == 200


@pytest.mark.django_db(transaction=True)
def test_w02_f09_anonymous_write_without_cookie_still_returns_401():
    strict = Client(enforce_csrf_checks=True)
    original_rows = LogEntry.objects.count()
    response = strict.post(
        _LOGS,
        data=json.dumps({"blood_sugar": 109}),
        content_type="application/json",
    )
    assert response.status_code == 401, response.content[:200]
    assert LogEntry.objects.count() == original_rows


@pytest.mark.django_db(transaction=True)
def test_w02_f09_cookie_only_clinical_write_without_csrf_is_forbidden():
    client, user, _ = _login(suffix="csrf")
    strict = Client(enforce_csrf_checks=True)
    strict.cookies.update(client.cookies)

    # Valid payload is vital. A 422 for malformed body might precede auth
    # and would NOT prove that the server blocks cross-site clinical writes.
    baseline = LogEntry.objects.filter(patient=user).count()
    response = strict.post(
        _LOGS,
        data=json.dumps({"blood_sugar": 110}),
        content_type="application/json",
    )
    assert response.status_code == 403, response.content[:200]
    assert LogEntry.objects.filter(patient=user).count() == baseline


@pytest.mark.django_db(transaction=True)
def test_w02_f09_valid_csrf_preserves_authorized_cookie_only_write():
    client, user, _ = _login(suffix="csrf-valid")
    strict = Client(enforce_csrf_checks=True)
    strict.cookies.update(client.cookies)
    csrf_request = RequestFactory().get(_LOGS)
    masked_token = get_token(csrf_request)
    strict.cookies[settings.CSRF_COOKIE_NAME] = csrf_request.META["CSRF_COOKIE"]

    before_count = LogEntry.objects.filter(patient=user).count()
    response = strict.post(
        _LOGS,
        data=json.dumps({"blood_sugar": 111}),
        content_type="application/json",
        HTTP_X_CSRFTOKEN=masked_token,
    )
    assert response.status_code == 200, response.content[:200]
    assert LogEntry.objects.filter(patient=user).count() == before_count + 1


@pytest.mark.django_db(transaction=True)
def test_w02_f09_valid_csrf_but_hostile_origin_still_blocks_write():
    client, user, _ = _login(suffix="csrf-origin")
    strict = Client(enforce_csrf_checks=True)
    strict.cookies.update(client.cookies)
    csrf_request = RequestFactory().get(_LOGS)
    masked_token = get_token(csrf_request)
    strict.cookies[settings.CSRF_COOKIE_NAME] = csrf_request.META["CSRF_COOKIE"]

    before_count = LogEntry.objects.filter(patient=user).count()
    response = strict.post(
        _LOGS,
        data=json.dumps({"blood_sugar": 112}),
        content_type="application/json",
        HTTP_X_CSRFTOKEN=masked_token,
        HTTP_ORIGIN="https://attacker.example",
    )
    assert response.status_code == 403, response.content[:200]
    assert LogEntry.objects.filter(patient=user).count() == before_count


@pytest.mark.django_db(transaction=True)
def test_w02_f09_bearer_only_write_does_not_require_browser_csrf():
    _, user, bearer = _login(suffix="bearer-write")
    strict = Client(enforce_csrf_checks=True)

    before_count = LogEntry.objects.filter(patient=user).count()
    response = strict.post(
        _LOGS,
        data=json.dumps({"blood_sugar": 113}),
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {bearer}",
    )
    assert response.status_code == 200, response.content[:200]
    assert LogEntry.objects.filter(patient=user).count() == before_count + 1


@pytest.mark.django_db(transaction=True)
def test_w02_f09_cookie_only_logout_without_csrf_does_not_revoke_bearer():
    client, user, bearer = _login(suffix="logout-csrf")
    strict = Client(enforce_csrf_checks=True)
    strict.cookies.update(client.cookies)

    response = strict.post("/api/v1/auth/logout")
    assert response.status_code == 403, response.content[:200]
    # A forged browser POST must not revoke every native bearer for the
    # same account via a cookie-only public Ninja auth route.
    assert verify_native_token(bearer).pk == user.pk


@pytest.mark.django_db(transaction=True)
def test_w02_f09_cookie_only_logout_with_valid_csrf_revokes_bearer():
    client, _, bearer = _login(suffix="logout-csrf-valid")
    strict = Client(enforce_csrf_checks=True)
    strict.cookies.update(client.cookies)
    csrf_request = RequestFactory().get("/api/v1/auth/logout")
    masked_token = get_token(csrf_request)
    strict.cookies[settings.CSRF_COOKIE_NAME] = csrf_request.META["CSRF_COOKIE"]

    response = strict.post(
        "/api/v1/auth/logout",
        HTTP_X_CSRFTOKEN=masked_token,
    )
    assert response.status_code == 200, response.content[:200]
    with pytest.raises(NativeTokenError):
        verify_native_token(bearer)


@pytest.mark.django_db(transaction=True)
def test_w02_f08_native_cookie_ceiling_is_enforced_on_direct_django():
    client, _, _ = _login(suffix="cookie-ceiling")
    # The old F09 strict-XFAIL documented a 14-day cookie bypass; the
    # candidate fix now requires Django's REAL session-expiry clock to
    # advance too. No bearer header, no refresh token, no cookie fallback.
    now = timezone.now()
    with patch("django.utils.timezone.now", return_value=now + timedelta(seconds=960)):
        result = client.get(_LOGS)
    assert result.status_code == 401, result.content[:200]


@pytest.mark.django_db(transaction=True)
@override_settings(NATIVE_AUTH_TOKEN_MAX_AGE_SECONDS=3 * 60)
def test_w02_f08_shorter_bearer_policy_also_shortens_native_session_cookie():
    client, _, bearer = _login(suffix="shorter-policy")
    now = timezone.now()
    with (
        patch("django.core.signing.time.time", return_value=time.time() + 240),
        patch("django.utils.timezone.now", return_value=now + timedelta(seconds=240)),
    ):
        # A shorter configured bearer age cannot leave the browser cookie
        # active until the unconditional 15-minute upper ceiling.
        assert client.get(_LOGS).status_code == 401
        assert Client().get(
            _LOGS, HTTP_AUTHORIZATION=f"Bearer {bearer}"
        ).status_code == 401
