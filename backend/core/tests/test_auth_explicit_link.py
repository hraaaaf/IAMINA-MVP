"""Explicit Firebase link and rollback safety tests."""

from types import SimpleNamespace

import pytest
from django.contrib.auth.models import AnonymousUser, User
from ninja.errors import HttpError

from core.api.v1.auth import (
    FirebaseAuthRequest,
    link_firebase_identity,
    unlink_firebase_identity,
)
from core.auth_migration import VerifiedFirebaseIdentity
from core.models import BasePatientProfile


def _request(user):
    return SimpleNamespace(user=user)


def _identity(uid="firebase-explicit", email="patient@example.test", verified=True):
    return VerifiedFirebaseIdentity(uid=uid, email=email, email_verified=verified)


def test_link_requires_authenticated_django_identity():
    with pytest.raises(HttpError) as exc:
        link_firebase_identity(
            _request(AnonymousUser()),
            FirebaseAuthRequest(id_token="token"),
        )
    assert exc.value.status_code == 401


@pytest.mark.django_db
def test_explicit_link_attaches_uid_to_current_user(monkeypatch):
    user = User.objects.create_user(
        username="native",
        email="patient@example.test",
        password="A-strong-passphrase-2026!",
    )
    profile = BasePatientProfile.objects.create(patient=user)
    monkeypatch.setattr(
        "core.api.v1.auth.verify_firebase_token",
        lambda token: _identity(),
    )

    result = link_firebase_identity(
        _request(user),
        FirebaseAuthRequest(id_token="token"),
    )

    profile.refresh_from_db()
    assert result == {"detail": "Firebase identity linked"}
    assert profile.firebase_uid == "firebase-explicit"


@pytest.mark.django_db
def test_explicit_link_rejects_unverified_or_mismatched_email(monkeypatch):
    user = User.objects.create_user(
        username="native",
        email="patient@example.test",
        password="A-strong-passphrase-2026!",
    )
    BasePatientProfile.objects.create(patient=user)

    monkeypatch.setattr(
        "core.api.v1.auth.verify_firebase_token",
        lambda token: _identity(verified=False),
    )
    with pytest.raises(HttpError) as unverified:
        link_firebase_identity(_request(user), FirebaseAuthRequest(id_token="token"))
    assert unverified.value.status_code == 409

    monkeypatch.setattr(
        "core.api.v1.auth.verify_firebase_token",
        lambda token: _identity(email="other@example.test"),
    )
    with pytest.raises(HttpError) as mismatch:
        link_firebase_identity(_request(user), FirebaseAuthRequest(id_token="token"))
    assert mismatch.value.status_code == 409


@pytest.mark.django_db
def test_explicit_link_cannot_steal_uid_from_another_user(monkeypatch):
    owner = User.objects.create_user(username="owner")
    BasePatientProfile.objects.create(patient=owner, firebase_uid="firebase-explicit")
    claimant = User.objects.create_user(
        username="claimant",
        email="patient@example.test",
        password="A-strong-passphrase-2026!",
    )
    BasePatientProfile.objects.create(patient=claimant)
    monkeypatch.setattr(
        "core.api.v1.auth.verify_firebase_token",
        lambda token: _identity(),
    )

    with pytest.raises(HttpError) as exc:
        link_firebase_identity(
            _request(claimant),
            FirebaseAuthRequest(id_token="token"),
        )
    assert exc.value.status_code == 409
    claimant.base_profile.refresh_from_db()
    assert claimant.base_profile.firebase_uid is None


@pytest.mark.django_db
def test_unlink_requires_usable_native_password():
    firebase_only = User.objects.create_user(username="firebase-only")
    profile = BasePatientProfile.objects.create(
        patient=firebase_only,
        firebase_uid="firebase-explicit",
    )

    with pytest.raises(HttpError) as exc:
        unlink_firebase_identity(_request(firebase_only))
    assert exc.value.status_code == 409
    profile.refresh_from_db()
    assert profile.firebase_uid == "firebase-explicit"


@pytest.mark.django_db
def test_unlink_is_idempotent_after_native_password_exists():
    user = User.objects.create_user(
        username="native",
        password="A-strong-passphrase-2026!",
    )
    profile = BasePatientProfile.objects.create(
        patient=user,
        firebase_uid="firebase-explicit",
    )

    assert unlink_firebase_identity(_request(user)) == {
        "detail": "Firebase identity unlinked"
    }
    assert unlink_firebase_identity(_request(user)) == {
        "detail": "Firebase identity unlinked"
    }
    profile.refresh_from_db()
    assert profile.firebase_uid is None
