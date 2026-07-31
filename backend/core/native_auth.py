"""Sovereign IAMINA bearer-token issuance, verification and revocation."""

from __future__ import annotations

from dataclasses import dataclass

from django.conf import settings
from django.core import signing
from django.db import transaction

from core.models import BasePatientProfile

_TOKEN_PREFIX = "iamina."
_TOKEN_SALT = "iamina.native-auth.v1"
_DEFAULT_MAX_AGE_SECONDS = 60 * 60 * 24 * 30


class NativeTokenError(Exception):
    """Stable native-token failure without leaking signing details."""


@dataclass(frozen=True)
class NativeTokenIdentity:
    user_id: int
    version: int


def issue_native_token(user) -> str:
    """Issue a timestamped bearer bound to the profile revocation version."""
    profile, _ = BasePatientProfile.objects.get_or_create(patient=user)
    signer = signing.TimestampSigner(salt=_TOKEN_SALT)
    signed = signer.sign_object(
        {"uid": user.pk, "v": profile.auth_token_version},
        compress=True,
    )
    return _TOKEN_PREFIX + signed


def verify_native_token(token: str):
    """Resolve one active IAMINA bearer or fail closed."""
    if not isinstance(token, str) or not token.startswith(_TOKEN_PREFIX):
        raise NativeTokenError("invalid_native_token")

    signer = signing.TimestampSigner(salt=_TOKEN_SALT)
    max_age = getattr(
        settings,
        "NATIVE_AUTH_TOKEN_MAX_AGE_SECONDS",
        _DEFAULT_MAX_AGE_SECONDS,
    )
    try:
        payload = signer.unsign_object(token[len(_TOKEN_PREFIX):], max_age=max_age)
    except (signing.BadSignature, signing.SignatureExpired, TypeError, ValueError) as exc:
        raise NativeTokenError("invalid_native_token") from exc

    if not isinstance(payload, dict):
        raise NativeTokenError("invalid_native_token")
    user_id = payload.get("uid")
    version = payload.get("v")
    if not isinstance(user_id, int) or not isinstance(version, int):
        raise NativeTokenError("invalid_native_token")

    try:
        profile = BasePatientProfile.objects.select_related("patient").get(
            patient_id=user_id,
            auth_token_version=version,
            patient__is_active=True,
        )
    except BasePatientProfile.DoesNotExist as exc:
        raise NativeTokenError("revoked_or_unknown_native_token") from exc
    return profile.patient


@transaction.atomic
def revoke_native_tokens(user) -> int:
    """Revoke every outstanding bearer for one user and return the new version."""
    profile, _ = BasePatientProfile.objects.select_for_update().get_or_create(patient=user)
    profile.auth_token_version += 1
    profile.save(update_fields=["auth_token_version"])
    return profile.auth_token_version
