"""W02-F09: characterize Django cookie and native bearer as two authorities.

Real HTTP through Django/Ninja against isolated CI PostgreSQL; synthetic
identities only. The cookie-only acceptance is a KNOWN OPEN SECURITY/UX
POLICY GAP, not an approved W02 session design or hosted BFF assertion.
"""

from __future__ import annotations

import json
import time
from unittest.mock import patch

import pytest
from django.conf import settings
from django.contrib.auth.models import User
from django.test import Client

from core.native_auth import issue_native_token
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
def test_w02_f09_expired_bearer_does_not_fall_back_to_django_cookie():
    client, _, bearer = _login(suffix="expiry")
    assert client.get(_LOGS).status_code == 200

    # F08 15m is ONLY a candidate. The Django cookie has a separate
    # SESSION_COOKIE_AGE of 14 days and no proved shared expiry/revocation.
    with patch("django.core.signing.time.time", return_value=time.time() + 960):
        expired_with_cookie = client.get(
            _LOGS, HTTP_AUTHORIZATION=f"Bearer {bearer}"
        )
        expired_bearer_only = Client().get(
            _LOGS, HTTP_AUTHORIZATION=f"Bearer {bearer}"
        )
        cookie_only = client.get(_LOGS)

    assert expired_with_cookie.status_code == 401
    assert expired_bearer_only.status_code == 401
    # CURRENT BEHAVIOR / SECURITY GAP: not a claim of safe W02 policy.
    assert cookie_only.status_code == 200


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
@pytest.mark.xfail(
    strict=True,
    reason=(
        "W02-F09 security policy UNDECIDED: direct Django cookie-only "
        "clinical API survives the candidate 15-minute bearer expiry"
    ),
)
def test_w02_f09_proposed_cookie_only_session_ceiling_is_not_yet_enforced():
    client, _, _ = _login(suffix="policy-gap")
    # This RED oracle is intentionally XFAIL until a SECURITY/UX owner chooses
    # cookie-only disablement or another SERVER-ENFORCED session limit.
    # It must never be presented as passing F09 acceptance.
    with patch("django.core.signing.time.time", return_value=time.time() + 960):
        result = client.get(_LOGS)

    assert result.status_code == 401, result.content[:200]
