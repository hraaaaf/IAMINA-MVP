"""G3 security: no patient access once a durable erasure intent exists.

These tests use only synthetic SQLite/PostgreSQL ORM records and local Django
Client. No live Firebase, Neon, Vercel or actual account deletion.
"""
import json

import pytest
from django.contrib.auth.models import User
from django.test import Client

from core.auth_migration import (
    FirebaseMigrationError,
    VerifiedFirebaseIdentity,
    migrate_new_firebase_identity,
    resolve_linked_firebase_user,
)
from core.models import BasePatientProfile
from core.models.erasure_attempt import ErasureAttempt
from core.native_auth import NativeTokenError, issue_native_token, verify_native_token


def _user(label):
    user = User.objects.create_user(
        username=f"g3-lock-{label}",
        email=f"g3-lock-{label}@example.invalid",
        password="SyntheticOnlyPass!2026",
    )
    BasePatientProfile.objects.create(
        patient=user, firebase_uid=f"synthetic-uid-{label}"
    )
    return user, issue_native_token(user)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "state",
    [
        ErasureAttempt.State.PENDING,
        ErasureAttempt.State.IN_PROGRESS,
        ErasureAttempt.State.REVIEW_REQUIRED,
        ErasureAttempt.State.COMPLETED,
    ],
)
def test_erasure_claim_denies_native_bearer_session_login_and_new_token(state):
    held, token = _user(state)
    other, other_token = _user("unrelated")
    client = Client()
    assert client.get(
        "/api/v1/auth/me", HTTP_AUTHORIZATION=f"Bearer {token}"
    ).status_code == 200

    ErasureAttempt.objects.create(
        patient_id_snapshot=held.pk,
        firebase_uid_snapshot=f"synthetic-uid-{state}",
        state=state,
    )

    with pytest.raises(NativeTokenError, match="revoked_or_unknown_native_token"):
        verify_native_token(token)
    with pytest.raises(NativeTokenError, match="revoked_or_unknown_native_token"):
        issue_native_token(held)

    isolated = Client()
    assert isolated.get(
        "/api/v1/auth/me", HTTP_AUTHORIZATION=f"Bearer {token}"
    ).status_code == 401
    isolated.force_login(held)
    assert isolated.get("/api/v1/auth/me").status_code == 401

    login_response = Client().post(
        "/api/v1/auth/login",
        data=json.dumps({
            "email": held.email,
            "password": "SyntheticOnlyPass!2026",
        }),
        content_type="application/json",
    )
    assert login_response.status_code == 403
    assert "access_token" not in login_response.content.decode()
    assert "sessionid" not in login_response.cookies

    # The lock must not accidentally impact patient B.
    assert Client().get(
        "/api/v1/auth/me", HTTP_AUTHORIZATION=f"Bearer {other_token}"
    ).status_code == 200
    assert Client().get("/api/v1/auth/me").status_code == 401
    assert User.objects.filter(pk=held.pk).exists()
    assert User.objects.filter(pk=other.pk).exists()


@pytest.mark.django_db
def test_linked_firebase_migration_cannot_modify_blocked_patient():
    user, _ = _user("firebase")
    ErasureAttempt.objects.create(
        patient_id_snapshot=user.pk,
        firebase_uid_snapshot="synthetic-uid-firebase",
        state=ErasureAttempt.State.IN_PROGRESS,
    )
    verified = VerifiedFirebaseIdentity(
        uid="synthetic-uid-firebase",
        email="changed-synthetic-email@example.invalid",
        email_verified=True,
    )
    with pytest.raises(FirebaseMigrationError, match="erasure_in_progress"):
        resolve_linked_firebase_user(verified)
    with pytest.raises(FirebaseMigrationError, match="erasure_in_progress"):
        migrate_new_firebase_identity(verified)
    user.refresh_from_db()
    assert user.email == "g3-lock-firebase@example.invalid"
