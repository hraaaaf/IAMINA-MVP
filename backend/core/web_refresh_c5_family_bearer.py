"""W02-F09-C5: candidate family-bound Web access bearer. NEVER HTTP mounted.

Separate token namespace: "iamina-web." CANNOT be authenticated by the
existing sovereign-native "iamina." bearer verifier. No clinical API can accept
it until a separately reviewed auth adapter explicitly opts in.

The caller must hold the CURRENT opaque family secret to mint a bearer.
Validation checks family-level revocation, owner, native auth generation,
idle/absolute windows and short access TTL against PostgreSQL on EVERY call.
Logout revokes ONE family, leaving sibling families alive. No actual cookies,
refresh HTTP, browser sessions, logging, or patient data are exposed.
"""
from __future__ import annotations

import hmac
from datetime import timedelta

from django.conf import settings
from django.core import signing
from django.db import transaction
from django.utils import timezone

from core.models import BasePatientProfile, WebRefreshFamily
from core.native_auth import NativeTokenError, native_token_max_age_seconds
from core.web_refresh_protocol import WebRefreshRejected, _digest, _limits

_PREFIX = "iamina-web."
_SALT = "iamina.w02.f09c5.family-access.v1"
_UNAVAILABLE = "web_family_access_unavailable"


class WebFamilyBearerRejected(Exception):
    """Uniform denial that never includes an opaque secret or bearer."""


def _enabled_limits():
    if getattr(settings, "F09_C5_FAMILY_ACCESS_ENABLED", False) is not True:
        raise WebFamilyBearerRejected(_UNAVAILABLE)
    try:
        idle, absolute = _limits()
        native_cap = native_token_max_age_seconds()
    except (WebRefreshRejected, NativeTokenError):
        raise WebFamilyBearerRejected(_UNAVAILABLE) from None
    requested = getattr(settings, "F09_C5_ACCESS_MAX_AGE_SECONDS", None)
    if type(requested) is not int or not 0 < requested <= native_cap:
        raise WebFamilyBearerRejected(_UNAVAILABLE)
    return idle, absolute, requested


def _claims(token: str, max_age: int) -> tuple[int, int, int]:
    if not isinstance(token, str) or not token.startswith(_PREFIX) or len(token) > 2048:
        raise WebFamilyBearerRejected(_UNAVAILABLE)
    try:
        payload = signing.TimestampSigner(salt=_SALT).unsign_object(
            token[len(_PREFIX):], max_age=max_age,
        )
    except (signing.BadSignature, signing.SignatureExpired, TypeError, ValueError):
        raise WebFamilyBearerRejected(_UNAVAILABLE) from None
    if (
        not isinstance(payload, dict)
        or set(payload) != {"uid", "fid", "av"}
        or any(type(payload.get(name)) is not int or payload[name] <= 0
               for name in ("uid", "fid"))
        or type(payload["av"]) is not int or payload["av"] < 0
    ):
        raise WebFamilyBearerRejected(_UNAVAILABLE)
    return payload["uid"], payload["fid"], payload["av"]


def _live_family(family, profile, now, idle, absolute) -> bool:
    return bool(
        profile is not None
        and profile.patient.is_active
        and family.user_id == profile.patient_id
        and family.auth_version == profile.auth_token_version
        and family.revoke_at is None
        and family.issued_at <= now
        and family.last_rotated_at <= now
        and now < family.idle_deadline
        and now < family.expires_at
        and now < family.last_rotated_at + timedelta(seconds=idle)
        and now < family.issued_at + timedelta(seconds=absolute)
    )


@transaction.atomic
def issue_family_bound_web_bearer(family_id, raw_current_refresh) -> str:
    """Test-only issuance after a verified session rotation or family creation.

    A caller with only a guessed family ID cannot mint access. This function
    is UNMOUNTED; future transport MUST prove OIDC/HMAC/Origin/CSRF first.
    """
    idle, absolute, _ = _enabled_limits()
    if type(family_id) is not int or family_id <= 0:
        raise WebFamilyBearerRejected(_UNAVAILABLE)
    try:
        digest = _digest(raw_current_refresh)
        family = WebRefreshFamily.objects.select_for_update().get(pk=family_id)
        profile = BasePatientProfile.objects.select_for_update().select_related(
            "patient"
        ).get(patient_id=family.user_id)
    except (WebRefreshRejected, WebRefreshFamily.DoesNotExist,
            BasePatientProfile.DoesNotExist):
        raise WebFamilyBearerRejected(_UNAVAILABLE) from None
    now = timezone.now()
    if (
        not _live_family(family, profile, now, idle, absolute)
        or not hmac.compare_digest(digest, family.current_digest)
    ):
        raise WebFamilyBearerRejected(_UNAVAILABLE)
    signed = signing.TimestampSigner(salt=_SALT).sign_object(
        {"uid": profile.patient_id, "fid": family.pk,
         "av": profile.auth_token_version},
        compress=True,
    )
    return _PREFIX + signed


def verify_family_bound_web_bearer(token):
    """Resolve user only while BOTH token and owning family remain active.

    There is deliberately no fallback to Django SessionAuth, Firebase or
    account-wide native bearers. Clinical routes must not import this module.
    """
    idle, absolute, max_age = _enabled_limits()
    user_id, family_id, version = _claims(token, max_age)
    try:
        family = WebRefreshFamily.objects.get(pk=family_id, user_id=user_id)
        profile = BasePatientProfile.objects.select_related("patient").get(
            patient_id=user_id, auth_token_version=version,
        )
    except (WebRefreshFamily.DoesNotExist, BasePatientProfile.DoesNotExist):
        raise WebFamilyBearerRejected(_UNAVAILABLE) from None
    if not _live_family(family, profile, timezone.now(), idle, absolute):
        raise WebFamilyBearerRejected(_UNAVAILABLE)
    return profile.patient


@transaction.atomic
def revoke_one_web_family_using_bearer(token) -> None:
    """One-device logout; PostgreSQL lock serializes against issuer/rotation.

    Once revoked, every candidate bearer on this family is invalid, while a
    sibling family with unchanged account generation remains active.
    """
    idle, absolute, max_age = _enabled_limits()
    user_id, family_id, version = _claims(token, max_age)
    try:
        family = WebRefreshFamily.objects.select_for_update().get(
            pk=family_id, user_id=user_id,
        )
        profile = BasePatientProfile.objects.select_for_update().select_related(
            "patient"
        ).get(patient_id=user_id, auth_token_version=version)
    except (WebRefreshFamily.DoesNotExist, BasePatientProfile.DoesNotExist):
        raise WebFamilyBearerRejected(_UNAVAILABLE) from None
    now = timezone.now()
    if not _live_family(family, profile, now, idle, absolute):
        raise WebFamilyBearerRejected(_UNAVAILABLE)
    family.revoke_at = now
    family.save(update_fields=["revoke_at"])
