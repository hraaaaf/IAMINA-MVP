"""W02-F09-C2 DRAFT cryptographic contracts, NEVER mounted as an HTTP API.

The synthetic C1 refresh handler remains unconditional 404. A validated HMAC
request attests to an authorized BFF *server* only, NOT a patient identity.
Future activation additionally needs independent Vercel OIDC service identity,
signed origin/CSRF matched to a locked refresh family, its single-use secret,
consent/UX policy and security sign-off. Do not supply Django SECRET_KEY to BFF.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import re
import secrets
import time
from datetime import timedelta

from django.conf import settings
from django.db import IntegrityError, transaction
from django.utils import timezone

from core.models import (
    BasePatientProfile,
    WebRefreshFamily,
    WebRefreshTransportNonce,
)

_KEY_RE = re.compile(r"^[A-Za-z0-9_-]{32,128}$")
_ORIGIN_RE = re.compile(r"^https://[a-z0-9-]+\.vercel\.app$")
_NONCE_RE = re.compile(r"^[A-Za-z0-9_-]{43}$")
_PROOF_RE = re.compile(r"^v1\.[0-9a-f]{64}$")
_CSRF_RE = re.compile(r"^c2\.([0-9]{10})\.([A-Za-z0-9_-]{24})\.([0-9a-f]{64})$")
_FRESH_MAX_SKEW_SECONDS = 30
_CANONICAL_PATH = "/api/v1/auth/refresh"
_TRANSPORT_SCOPE = "iamina.web.refresh.bff.v1"
_CSRF_SCOPE = "iamina.web.refresh.csrf.v1"
_UNAVAILABLE = "web_refresh_boundary_unavailable"


class WebRefreshBoundaryRejected(Exception):
    """Uniform fail-closed rejection. Never reveal a credential or digest."""


def _config() -> tuple[bytes, bytes, str, int]:
    if getattr(settings, "F09_C2_BOUNDARY_ENABLED", False) is not True:
        raise WebRefreshBoundaryRejected(_UNAVAILABLE)
    transport = getattr(settings, "F09_C2_BFF_HMAC_KEY", None)
    csrf = getattr(settings, "F09_C2_CSRF_HMAC_KEY", None)
    origin = getattr(settings, "F09_C2_EXPECTED_WEB_ORIGIN", None)
    ttl = getattr(settings, "F09_C2_CSRF_TTL_SECONDS", None)
    if (
        not isinstance(transport, str)
        or not _KEY_RE.fullmatch(transport)
        or not isinstance(csrf, str)
        or not _KEY_RE.fullmatch(csrf)
        or transport == csrf
        or transport == settings.SECRET_KEY
        or csrf == settings.SECRET_KEY
        or not isinstance(origin, str)
        or not _ORIGIN_RE.fullmatch(origin)
        or type(ttl) is not int
        or not 1 <= ttl <= 300
    ):
        raise WebRefreshBoundaryRejected(_UNAVAILABLE)
    return transport.encode("ascii"), csrf.encode("ascii"), origin, ttl


def _valid_nonce(value) -> bool:
    if not isinstance(value, str) or not _NONCE_RE.fullmatch(value):
        return False
    try:
        raw = base64.urlsafe_b64decode(value + "=")
    except (ValueError, base64.binascii.Error):
        return False
    return len(raw) == 32 and base64.urlsafe_b64encode(raw).decode().rstrip("=") == value


def verify_bff_refresh_envelope(*, headers, body, method, path) -> bool:
    """Verify distinct BFF MAC, exact endpoint/body/Origin, and burn nonce once.

    The timestamp is bounded to ±30s. Nonces are unique in PostgreSQL and
    stored only as HMAC digests. A rejected or replayed request never reuses a
    nonce. No patient identity or refresh token is processed here.
    """
    key, _, expected_origin, _ = _config()
    if method != "POST" or path != _CANONICAL_PATH:
        raise WebRefreshBoundaryRejected(_UNAVAILABLE)
    if not isinstance(headers, dict) or not isinstance(body, bytes) or len(body) > 4096:
        raise WebRefreshBoundaryRejected(_UNAVAILABLE)

    origin = headers.get("x-iamina-bff-origin")
    ts_text = headers.get("x-iamina-bff-timestamp")
    nonce = headers.get("x-iamina-bff-nonce")
    proof = headers.get("x-iamina-bff-proof")
    if (
        origin != expected_origin
        or not isinstance(ts_text, str)
        or not re.fullmatch(r"[1-9][0-9]{9}", ts_text)
        or not _valid_nonce(nonce)
        or not isinstance(proof, str)
        or not _PROOF_RE.fullmatch(proof)
    ):
        raise WebRefreshBoundaryRejected(_UNAVAILABLE)

    ts = int(ts_text)
    if abs(time.time() - ts) > _FRESH_MAX_SKEW_SECONDS:
        raise WebRefreshBoundaryRejected(_UNAVAILABLE)

    canonical = "\n".join((
        _TRANSPORT_SCOPE,
        method,
        path,
        ts_text,
        nonce,
        origin,
        hashlib.sha256(body).hexdigest(),
    ))
    expected = hmac.new(
        key, canonical.encode("utf-8"), hashlib.sha256
    ).hexdigest()
    if not hmac.compare_digest(proof[3:], expected):
        raise WebRefreshBoundaryRejected(_UNAVAILABLE)

    digest = hmac.new(
        key, ("iamina.web.refresh.nonce.v1|" + nonce).encode("ascii"), hashlib.sha256
    ).hexdigest()
    now = timezone.now()
    try:
        # Isolated atomic block: a uniqueness violation rolls back only the
        # attempted insert; no patient or refresh-family state is mutated.
        with transaction.atomic():
            WebRefreshTransportNonce.objects.create(
                nonce_digest=digest,
                seen_at=now,
                expires_at=now + timedelta(seconds=2 * _FRESH_MAX_SKEW_SECONDS + 5),
            )
    except IntegrityError as exc:
        raise WebRefreshBoundaryRejected(_UNAVAILABLE) from exc
    return True


def _current_family(family, now):
    if not isinstance(family, WebRefreshFamily) or not family.pk:
        return None
    try:
        persisted = WebRefreshFamily.objects.get(pk=family.pk)
    except WebRefreshFamily.DoesNotExist:
        return None
    if (
        persisted.revoke_at is not None
        or now < persisted.issued_at
        or now >= persisted.idle_deadline
        or now >= persisted.expires_at
        or not BasePatientProfile.objects.filter(
            patient_id=persisted.user_id,
            auth_token_version=persisted.auth_version,
            patient__is_active=True,
        ).exists()
    ):
        return None
    return persisted


def _csrf_mac(key: bytes, family: WebRefreshFamily, origin: str, ts: str, nonce: str):
    canonical = "\n".join((
        _CSRF_SCOPE, str(family.pk), family.current_digest, origin, ts, nonce,
    ))
    return hmac.new(key, canonical.encode("utf-8"), hashlib.sha256).hexdigest()


def issue_family_csrf(family, *, origin: str) -> str:
    """Sign a browser-readable CSRF proof bound to one ACTIVE family rotation.

    This never exposes raw refresh secrets. Browser cookie/header equality
    alone is insecure; Django must verify THIS independent family-keyed MAC.
    """
    _, key, expected_origin, _ = _config()
    if origin != expected_origin:
        raise WebRefreshBoundaryRejected(_UNAVAILABLE)
    now = timezone.now()
    stored = _current_family(family, now)
    if stored is None:
        raise WebRefreshBoundaryRejected(_UNAVAILABLE)
    ts = str(int(now.timestamp()))
    nonce = secrets.token_urlsafe(18)
    mac = _csrf_mac(key, stored, origin, ts, nonce)
    return f"c2.{ts}.{nonce}.{mac}"


def verify_family_csrf(family, *, origin, cookie_token, header_token) -> bool:
    """Fail closed on key, policy, account, origin, rotation or time mismatch."""
    try:
        _, key, expected_origin, ttl = _config()
    except WebRefreshBoundaryRejected:
        return False
    if (
        origin != expected_origin
        or not isinstance(cookie_token, str)
        or not isinstance(header_token, str)
        or len(cookie_token) > 256
        or len(header_token) > 256
        or not hmac.compare_digest(cookie_token, header_token)
    ):
        return False

    match = _CSRF_RE.fullmatch(header_token)
    if match is None:
        return False
    ts_text, nonce, mac = match.groups()
    now = timezone.now()
    if not 0 <= now.timestamp() - int(ts_text) <= ttl:
        return False
    stored = _current_family(family, now)
    if stored is None:
        return False
    expected_mac = _csrf_mac(key, stored, origin, ts_text, nonce)
    return hmac.compare_digest(mac, expected_mac)
