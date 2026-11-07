"""W02-F08: server authority under absent/offline logout, test-first.

All identities synthetic. Real Django HTTP against ephemeral CI PostgreSQL.
The immediate replay assertion documents an unavoidable transport limitation.
The 16-minute test expresses a PROPOSED 15-minute absolute bearer window,
not a claim that an offline sign-out can revoke the backend instantly.
"""
import time
from unittest.mock import patch

import pytest
from django.contrib.auth.models import User
from django.test import Client, override_settings

from core.models import BasePatientProfile
from core.native_auth import issue_native_token


def _logs_as(bearer: str):
    return Client().get(
        "/api/v1/logs",
        HTTP_AUTHORIZATION=f"Bearer {bearer}",
    )


@pytest.mark.django_db(transaction=True)
def test_w02_f08_offline_logout_cannot_server_revoke_without_http_request():
    user = User.objects.create_user(
        username="w02-f08-offline-user",
        email="w02-f08-offline@example.invalid",
        password="Synthetic-only-Auth-F08-2026!",
    )
    bearer = issue_native_token(user)
    assert _logs_as(bearer).status_code == 200

    # The Web browser may lock A/B and refuse all local authority, but if
    # backend POST /auth/logout never arrives, the server has no new event.
    # Verify the actual residual risk, NOT an impossible 401 expectation.
    replay = _logs_as(bearer)
    assert replay.status_code == 200, replay.content[:200]
    assert BasePatientProfile.objects.get(patient=user).auth_token_version == 0


@pytest.mark.django_db(transaction=True)
def test_w02_f08_candidate_15min_absolute_bearer_limit_rejects_replay():
    user = User.objects.create_user(
        username="w02-f08-expiry-user",
        email="w02-f08-expiry@example.invalid",
        password="Synthetic-only-Auth-F08-2026!",
    )
    bearer = issue_native_token(user)
    assert _logs_as(bearer).status_code == 200

    # A stolen bearer left on disk after offline logout must not remain
    # usable for 30 days. PROPOSED upper bound: 15 minutes + tolerance.
    # Patch only the signed-token verification clock. No real waiting.
    future = time.time() + (16 * 60)
    with patch("django.core.signing.time.time", return_value=future):
        expired = _logs_as(bearer)
    assert expired.status_code == 401, expired.content[:200]


@pytest.mark.django_db(transaction=True)
@override_settings(NATIVE_AUTH_TOKEN_MAX_AGE_SECONDS=60 * 60 * 24 * 30)
def test_w02_f08_configuration_must_not_exceed_bearer_security_ceiling():
    user = User.objects.create_user(
        username="w02-f08-override-user",
        email="w02-f08-override@example.invalid",
        password="Synthetic-only-Auth-F08-2026!",
    )
    bearer = issue_native_token(user)
    assert _logs_as(bearer).status_code == 200

    # A server setting must not silently restore a 30-day replay window.
    future = time.time() + (16 * 60)
    with patch("django.core.signing.time.time", return_value=future):
        response = _logs_as(bearer)
    assert response.status_code == 401, response.content[:200]
