"""W02-F09-B candidate Web refresh-family protocol. NOT an HTTP endpoint.

This deliberately cannot be called in the ordinary runtime: no endpoint is
registered, F09_WEB_REFRESH_ENABLED defaults to absent/False, and BOTH idle
and absolute policy integers are required. The BFF cookie, CSRF/Origin checks,
per-family access bearer binding and all UX approval are separate HUMAN gates.
Never log/serialize raw secrets or provide them to a generic API route.
"""

from __future__ import annotations

import hashlib
import hmac
import re
import secrets
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from core.models import (
    BasePatientProfile,
    WebRefreshConsumedSecret,
    WebRefreshFamily,
)

_PREFIX = "iamina-wr1."
_OPAQUE_PATTERN = re.compile(r"^iamina-wr1\.[A-Za-z0-9_-]{64}$")


class WebRefreshRejected(Exception):
    """A uniform, non-disclosing error. Never concatenate credential bytes."""


def _limits() -> tuple[int, int]:
    if getattr(settings, "F09_WEB_REFRESH_ENABLED", False) is not True:
        raise WebRefreshRejected("web_refresh_unavailable")
    idle = getattr(settings, "F09_WEB_REFRESH_IDLE_SECONDS", None)
    absolute = getattr(settings, "F09_WEB_REFRESH_ABSOLUTE_SECONDS", None)
    if (
        type(idle) is not int
        or type(absolute) is not int
        or idle <= 0
        or absolute <= 0
        or idle > absolute
    ):
        raise WebRefreshRejected("web_refresh_unavailable")
    return idle, absolute


def _digest(raw: str) -> str:
    if not isinstance(raw, str) or not _OPAQUE_PATTERN.fullmatch(raw):
        raise WebRefreshRejected("web_refresh_unavailable")
    # Domain separation and a server-owned key. Only keyed hex digests reach
    # Django/PostgreSQL; no user/clinical metadata or raw token is persisted.
    key = settings.SECRET_KEY.encode("utf-8")
    return hmac.new(
        key,
        ("iamina.f09b.webrefresh.v1|" + raw).encode("ascii"),
        hashlib.sha256,
    ).hexdigest()


def _new_secret() -> str:
    return _PREFIX + secrets.token_urlsafe(48)


@transaction.atomic
def issue_web_refresh_family(user) -> tuple[WebRefreshFamily, str]:
    """Issue an isolated candidate family; no route can invoke it yet."""
    idle, absolute = _limits()
    if not getattr(user, "pk", None):
        raise WebRefreshRejected("web_refresh_unavailable")
    try:
        profile = BasePatientProfile.objects.select_for_update().select_related(
            "patient"
        ).get(patient_id=user.pk, patient__is_active=True)
    except BasePatientProfile.DoesNotExist as exc:
        raise WebRefreshRejected("web_refresh_unavailable") from exc

    now = timezone.now()
    raw = _new_secret()
    family = WebRefreshFamily.objects.create(
        user_id=user.pk,
        auth_version=profile.auth_token_version,
        current_digest=_digest(raw),
        issued_at=now,
        last_rotated_at=now,
        idle_deadline=now + timedelta(seconds=idle),
        expires_at=now + timedelta(seconds=absolute),
    )
    return family, raw


def rotate_web_refresh_family(raw) -> str:
    """Atomically consume one secret, or revoke its family on detected replay.

    select_for_update locks the stable FAMILY row, not a candidate secret
    lookup. Both concurrent requests may identify the old digest before the
    winner commits; the loser rechecks the digest under the lock, finds the
    spent-secret tombstone, and revokes that family and its ACCOUNT-WIDE native
    bearer generation. A replay-denial decision commits before raising so it
    is never rolled back by the rejected request.
    """
    idle, absolute = _limits()
    digest = _digest(raw)
    reason = None
    replacement = None

    with transaction.atomic():
        family_id = (
            WebRefreshFamily.objects.filter(current_digest=digest)
            .values_list("pk", flat=True)
            .first()
        )
        if family_id is None:
            family_id = (
                WebRefreshConsumedSecret.objects.filter(digest=digest)
                .values_list("family_id", flat=True)
                .first()
            )
        if family_id is None:
            raise WebRefreshRejected("web_refresh_unavailable")

        family = WebRefreshFamily.objects.select_for_update().get(pk=family_id)
        # The policy clock is checked AFTER acquiring the PostgreSQL lock.
        now = timezone.now()
        replay = family.current_digest != digest
        is_spent = replay and WebRefreshConsumedSecret.objects.filter(
            family_id=family.pk, digest=digest
        ).exists()

        if family.revoke_at is not None:
            reason = "revoked"
        elif replay:
            if is_spent:
                reason = "replayed"
            else:
                reason = "invalid"
        elif (
            now < family.issued_at
            or now < family.last_rotated_at
            or now >= family.idle_deadline
            or now >= family.expires_at
            or now >= family.last_rotated_at + timedelta(seconds=idle)
            or now >= family.issued_at + timedelta(seconds=absolute)
        ):
            reason = "expired"

        # Lock the authoritative revocation generation in the same TX.
        try:
            profile = BasePatientProfile.objects.select_for_update().select_related(
                "patient"
            ).get(patient_id=family.user_id)
        except BasePatientProfile.DoesNotExist:
            profile = None
            reason = "invalid_account"

        if profile is not None and (
            not profile.patient.is_active
            or profile.auth_token_version != family.auth_version
        ):
            reason = "invalid_account"

        if reason is not None:
            if family.revoke_at is None:
                family.revoke_at = now
                family.save(update_fields=["revoke_at"])
                if reason == "replayed" and profile is not None:
                    # No per-family bearer binding is deployed yet. Until
                    # one exists, replay must revoke ALL existing native
                    # access tokens for this account, never merely the cookie.
                    profile.auth_token_version += 1
                    profile.save(update_fields=["auth_token_version"])
        else:
            # Never issue an access bearer here. A future BFF/HTTP layer must
            # independently satisfy CSRF, origin and family-bound invalidation.
            replacement = _new_secret()
            WebRefreshConsumedSecret.objects.create(
                family=family,
                digest=digest,
                consumed_at=now,
            )
            family.current_digest = _digest(replacement)
            family.last_rotated_at = now
            family.idle_deadline = min(
                now + timedelta(seconds=idle),
                family.expires_at,
                family.issued_at + timedelta(seconds=absolute),
            )
            family.save(
                update_fields=["current_digest", "last_rotated_at", "idle_deadline"]
            )

    if reason is not None or replacement is None:
        raise WebRefreshRejected("web_refresh_unavailable")
    return replacement
