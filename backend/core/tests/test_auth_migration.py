"""Regression tests for the Firebase-to-Django migration boundary."""

from types import SimpleNamespace

import pytest
from django.contrib.auth.models import User

from core.auth_migration import (
    FirebaseIdentityConflict,
    FirebaseIdentityNotLinked,
    VerifiedFirebaseIdentity,
    migrate_new_firebase_identity,
    resolve_linked_firebase_user,
)
from core.models import BasePatientProfile
from diabetes.api.v1.security import FirebaseAuth
from diabetes.models import DiabetesProfile


def _identity(uid: str = "firebase-uid", email: str = "patient@example.com"):
    return VerifiedFirebaseIdentity(uid=uid, email=email, email_verified=True)


@pytest.mark.django_db
def test_generic_bearer_resolution_never_creates_user(monkeypatch):
    authenticator = FirebaseAuth()
    monkeypatch.setattr(
        "diabetes.api.v1.security.verify_firebase_token",
        lambda token: _identity(),
    )

    request = SimpleNamespace(user=None)
    result = authenticator.authenticate(request, "verified-token")

    assert result is None
    assert User.objects.count() == 0
    assert BasePatientProfile.objects.count() == 0


@pytest.mark.django_db
def test_resolve_linked_identity_is_side_effect_free_for_profile_count():
    user = User.objects.create_user(username="linked", email="old@example.com")
    BasePatientProfile.objects.create(patient=user, firebase_uid="firebase-uid")

    resolved = resolve_linked_firebase_user(_identity())

    assert resolved.pk == user.pk
    assert User.objects.count() == 1
    assert BasePatientProfile.objects.count() == 1
    user.refresh_from_db()
    assert user.email == "patient@example.com"


@pytest.mark.django_db
def test_unlinked_identity_fails_closed():
    with pytest.raises(FirebaseIdentityNotLinked):
        resolve_linked_firebase_user(_identity())

    assert User.objects.count() == 0


@pytest.mark.django_db
def test_controlled_bridge_creates_one_identity_and_module_shell():
    first = migrate_new_firebase_identity(_identity())
    second = migrate_new_firebase_identity(_identity())

    assert first.pk == second.pk
    assert User.objects.count() == 1
    assert BasePatientProfile.objects.filter(
        patient=first,
        firebase_uid="firebase-uid",
    ).count() == 1
    assert DiabetesProfile.objects.filter(base_profile=first.base_profile).count() == 1


@pytest.mark.django_db
def test_active_django_email_is_not_silently_merged():
    existing = User.objects.create_user(
        username="existing",
        email="patient@example.com",
        password="A-strong-passphrase-2026!",
    )
    BasePatientProfile.objects.create(patient=existing)

    with pytest.raises(FirebaseIdentityConflict):
        migrate_new_firebase_identity(_identity())

    assert User.objects.count() == 1
    existing.base_profile.refresh_from_db()
    assert existing.base_profile.firebase_uid is None


@pytest.mark.django_db
def test_unique_unusable_password_legacy_shell_can_receive_verified_uid():
    legacy = User.objects.create_user(
        username="legacy-firebase-shell",
        email="patient@example.com",
    )
    profile = BasePatientProfile.objects.create(patient=legacy)

    migrated = migrate_new_firebase_identity(_identity())

    assert migrated.pk == legacy.pk
    profile.refresh_from_db()
    assert profile.firebase_uid == "firebase-uid"
    assert DiabetesProfile.objects.filter(base_profile=profile).count() == 1


@pytest.mark.django_db
def test_verified_email_conflict_blocks_linked_login():
    linked = User.objects.create_user(username="linked", email="old@example.com")
    BasePatientProfile.objects.create(patient=linked, firebase_uid="firebase-uid")
    User.objects.create_user(username="other", email="patient@example.com")

    with pytest.raises(FirebaseIdentityConflict):
        resolve_linked_firebase_user(_identity())

    linked.refresh_from_db()
    assert linked.email == "old@example.com"
