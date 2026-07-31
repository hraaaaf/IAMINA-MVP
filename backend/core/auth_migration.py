"""Controlled Firebase-to-Django identity migration boundary.

Firebase is a temporary migration credential. Django ``User`` remains the
canonical internal identity. Generic bearer authentication may resolve an
already-linked identity, but it must never create or merge accounts.
"""

from __future__ import annotations

from dataclasses import dataclass

from django.contrib.auth.models import User
from django.db import transaction

from core.models import BasePatientProfile
from diabetes.models import DiabetesProfile


class FirebaseMigrationError(Exception):
    """Stable migration failure without token or provider details."""


class FirebaseIdentityNotLinked(FirebaseMigrationError):
    """The verified Firebase UID is not linked to a Django identity."""


class FirebaseIdentityConflict(FirebaseMigrationError):
    """The credential conflicts with an existing identity relationship."""


@dataclass(frozen=True)
class VerifiedFirebaseIdentity:
    uid: str
    email: str
    email_verified: bool


def verify_firebase_token(id_token: str) -> VerifiedFirebaseIdentity:
    """Verify one Firebase token and return a minimized immutable identity."""
    if not isinstance(id_token, str) or not id_token.strip():
        raise FirebaseMigrationError("invalid_firebase_credential")

    try:
        from firebase_admin import auth as firebase_auth

        decoded = firebase_auth.verify_id_token(id_token, check_revoked=True)
    except Exception as exc:
        raise FirebaseMigrationError("invalid_firebase_credential") from exc

    uid = decoded.get("uid")
    if not isinstance(uid, str) or not uid.strip():
        raise FirebaseMigrationError("invalid_firebase_credential")

    email = decoded.get("email")
    return VerifiedFirebaseIdentity(
        uid=uid.strip(),
        email=email.strip().lower() if isinstance(email, str) else "",
        email_verified=decoded.get("email_verified") is True,
    )


def resolve_linked_firebase_user(identity: VerifiedFirebaseIdentity) -> User:
    """Resolve an existing UID link; never create or merge an account."""
    try:
        profile = BasePatientProfile.objects.select_related("patient").get(
            firebase_uid=identity.uid
        )
    except BasePatientProfile.DoesNotExist as exc:
        raise FirebaseIdentityNotLinked("firebase_identity_not_linked") from exc

    user = profile.patient
    _sync_verified_email(user, identity)
    return user


@transaction.atomic
def migrate_new_firebase_identity(identity: VerifiedFirebaseIdentity) -> User:
    """Create one Django identity for a previously unseen verified Firebase UID.

    Existing email matches are deliberately not merged. A user who already has
    a Django account must authenticate through that account before an explicit
    link flow can be introduced.
    """
    existing = BasePatientProfile.objects.select_related("patient").filter(
        firebase_uid=identity.uid
    ).first()
    if existing is not None:
        _sync_verified_email(existing.patient, identity)
        return existing.patient

    if identity.email and User.objects.filter(email__iexact=identity.email).exists():
        raise FirebaseIdentityConflict("existing_django_account_requires_explicit_link")

    username = _unique_username(_username_seed(identity))
    user = User.objects.create_user(username=username, email=identity.email)
    base = BasePatientProfile.objects.create(
        patient=user,
        firebase_uid=identity.uid,
    )
    DiabetesProfile.objects.create(base_profile=base)
    return user


def _sync_verified_email(user: User, identity: VerifiedFirebaseIdentity) -> None:
    """Synchronize only a provider-verified email on an already-linked account."""
    if identity.email_verified and identity.email and user.email != identity.email:
        if User.objects.exclude(pk=user.pk).filter(email__iexact=identity.email).exists():
            raise FirebaseIdentityConflict("verified_email_conflicts_with_django_account")
        user.email = identity.email
        user.save(update_fields=["email"])


def _username_seed(identity: VerifiedFirebaseIdentity) -> str:
    if identity.email:
        local = identity.email.split("@", maxsplit=1)[0]
        if local:
            return local[:120]
    return f"firebase_{identity.uid[:32]}"


def _unique_username(base: str) -> str:
    candidate = base
    suffix = 1
    while User.objects.filter(username=candidate).exists():
        candidate = f"{base[:140]}_{suffix}"
        suffix += 1
    return candidate
