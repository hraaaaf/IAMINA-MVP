"""Controlled Firebase-to-Django identity migration boundary.

Firebase is a temporary migration credential. Django ``User`` remains the
canonical internal identity. Generic bearer authentication may resolve an
already-linked identity, but it must never create or merge accounts.
"""

from __future__ import annotations

from dataclasses import dataclass

from django.contrib.auth.models import User
from django.db import transaction

from core.firebase_migration_policy import firebase_migration_enabled
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
    """Verify one Firebase token only inside an explicit migration window."""
    if not firebase_migration_enabled():
        raise FirebaseMigrationError("firebase_migration_disabled")
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
    _sync_firebase_email(user, identity)
    return user


@transaction.atomic
def migrate_new_firebase_identity(identity: VerifiedFirebaseIdentity) -> User:
    """Create or migrate one identity for a verified Firebase UID.

    An active Django password account is never merged by email. A legacy shell
    is eligible only when the email resolves to exactly one user with an
    unusable Django password. The shell may predate BasePatientProfile creation;
    the migration bridge creates the missing empty profile without inventing
    patient facts.
    """
    existing = BasePatientProfile.objects.select_related("patient").filter(
        firebase_uid=identity.uid
    ).first()
    if existing is not None:
        _sync_firebase_email(existing.patient, identity)
        return existing.patient

    legacy_shell = _resolve_legacy_firebase_shell(identity)
    if legacy_shell is not None:
        profile, _ = BasePatientProfile.objects.get_or_create(patient=legacy_shell)
        if profile.firebase_uid and profile.firebase_uid != identity.uid:
            raise FirebaseIdentityConflict("legacy_identity_already_linked")
        profile.firebase_uid = identity.uid
        profile.save(update_fields=["firebase_uid"])
        DiabetesProfile.objects.get_or_create(base_profile=profile)
        _sync_firebase_email(legacy_shell, identity)
        return legacy_shell

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


def _resolve_legacy_firebase_shell(identity: VerifiedFirebaseIdentity) -> User | None:
    """Find the unique historical Firebase-only shell eligible for UID linking."""
    if not identity.email:
        return None

    candidates = list(
        User.objects.filter(email__iexact=identity.email).order_by("id")[:2]
    )
    if len(candidates) != 1:
        return None

    candidate = candidates[0]
    if candidate.has_usable_password():
        return None
    if BasePatientProfile.objects.filter(patient=candidate).exclude(
        firebase_uid__isnull=True
    ).exclude(firebase_uid="").exists():
        return None
    return candidate


def _sync_firebase_email(user: User, identity: VerifiedFirebaseIdentity) -> None:
    """Synchronize Firebase email without weakening native-account ownership.

    Active Django password accounts require an explicitly verified provider
    email. Historical Firebase-only shells have no usable Django password, so
    the verified UID remains their sole authentication key during migration;
    their provider email may be refreshed even when an old token omits the
    ``email_verified`` claim. Email collisions always fail closed.
    """
    can_sync = identity.email_verified or not user.has_usable_password()
    if can_sync and identity.email and user.email != identity.email:
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
