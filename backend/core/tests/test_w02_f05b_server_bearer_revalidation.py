"""W02-F05B RED-first: server authority for stored native-bearer revalidation.

Synthetic HTTP clients and users; no patient data or real credentials.
A cached bearer MUST NOT be treated as authenticated without an authoritative
server check, because a failed local fence write and token deletion can leave
valid-looking bytes persisted after user-initiated sign-out.
"""

import pytest
from django.contrib.auth.models import User
from django.test import Client

from core.native_auth import issue_native_token


def _bearer_request(token):
    # Fresh cookie-less client models browser restart with persisted bearer.
    return Client().get("/api/v1/auth/me", HTTP_AUTHORIZATION=f"Bearer {token}")


@pytest.mark.django_db(transaction=True)
def test_w02_f05b_native_me_accepts_valid_bearer_then_rejects_revoked_bearer():
    user = User.objects.create_user(
        username="f05b-patient-a",
        email="f05b-a@example.invalid",
        password="F05B-Synthetic-Secure-2026!",
    )
    token = issue_native_token(user)

    # Current /auth/me is mounted on a public router and does not resolve
    # Authorization, so this assertion should be RED before the server fix.
    good = _bearer_request(token)
    assert good.status_code == 200, good.content[:200]
    assert good.json()["id"] == user.pk

    logged_out = Client().post(
        "/api/v1/auth/logout",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )
    assert logged_out.status_code == 200, logged_out.content[:200]

    rejected = _bearer_request(token)
    assert rejected.status_code == 401, rejected.content[:200]
    # A post-logout bearer MUST never come back with a patient identifier.
    assert "id" not in rejected.json()


@pytest.mark.django_db(transaction=True)
def test_w02_f05b_native_me_never_accepts_conflicting_cookie_identity():
    a = User.objects.create_user(username="f05b-a")
    b = User.objects.create_user(username="f05b-b")
    token_a = issue_native_token(a)

    session = Client()
    session.force_login(b)
    conflicting = session.get(
        "/api/v1/auth/me",
        HTTP_AUTHORIZATION=f"Bearer {token_a}",
    )
    assert conflicting.status_code == 401, conflicting.content[:200]

    tampered = _bearer_request(token_a + "-tamper")
    assert tampered.status_code == 401, tampered.content[:200]
