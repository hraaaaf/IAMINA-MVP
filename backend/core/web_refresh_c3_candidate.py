"""W02-F09-C3: non-activated Web refresh security candidate.

This module is deliberately NOT mounted as an HTTP route. Django is the sole
patient authority. The independently verified Vercel service JWT proves a
*service*, never a patient. The signed BFF MAC proves a specific request.
The family CSRF and opaque refresh secret jointly authorize a single rotation.

No cookies, access bearer, login session or clinical data are issued here.
A real deployment also requires a reviewed BFF cookie/session adapter.
"""
from __future__ import annotations

import base64
import binascii
import hmac
import json
import re
import time
from urllib import request

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from django.conf import settings
from django.db import transaction

from core.models import WebRefreshFamily
from core.web_refresh_boundary import (
    WebRefreshBoundaryRejected,
    verify_bff_refresh_envelope,
    verify_family_csrf,
)
from core.web_refresh_protocol import (
    WebRefreshRejected,
    _digest,
    rotate_web_refresh_family,
)

_FAILURE = "web_refresh_c3_unavailable"
_OWNER_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")
_PROJECT_RE = re.compile(r"^[a-zA-Z0-9_-]{1,100}$")
_JWT_PART_RE = re.compile(r"^[A-Za-z0-9_-]{1,8192}$")


class WebRefreshC3Rejected(Exception):
    """All untrusted failures collapse to one non-disclosing error."""


def _policy():
    if getattr(settings, "F09_C3_ENABLED", False) is not True:
        raise WebRefreshC3Rejected(_FAILURE)
    owner = getattr(settings, "F09_C3_OIDC_OWNER", None)
    project = getattr(settings, "F09_C3_OIDC_PROJECT", None)
    project_id = getattr(settings, "F09_C3_OIDC_PROJECT_ID", None)
    if (
        not isinstance(owner, str) or not _OWNER_RE.fullmatch(owner)
        or not isinstance(project, str) or not _PROJECT_RE.fullmatch(project)
        or not isinstance(project_id, str)
        or not re.fullmatch(r"prj_[A-Za-z0-9]{12,80}", project_id)
    ):
        raise WebRefreshC3Rejected(_FAILURE)
    # Team-scoped issuer only. Global issuer is intentionally not enabled.
    return {
        "issuer": f"https://oidc.vercel.com/{owner}",
        "audience": f"https://vercel.com/{owner}",
        "subject": f"owner:{owner}:project:{project}:environment:preview",
        "project_id": project_id,
        "owner": owner,
        "project": project,
    }


def _no_duplicate_keys(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            raise ValueError("duplicate JSON key")
        out[key] = value
    return out


def _decode(part, limit=8192):
    if not isinstance(part, str) or len(part) > limit or not _JWT_PART_RE.fullmatch(part):
        raise ValueError("bad encoded part")
    # Only canonical base64url, not flexible/ambiguous encodings.
    raw = base64.urlsafe_b64decode(part + "=" * ((-len(part)) % 4))
    if base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=") != part:
        raise ValueError("non-canonical")
    return raw


class _NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _pinned_vercel_jwks(issuer):
    """Read only Vercel team issuer JWKS. No caller URL or redirected host."""
    url = issuer + "/.well-known/jwks"
    opener = request.build_opener(_NoRedirect)
    with opener.open(request.Request(url, headers={"Accept": "application/json"}), timeout=3) as res:
        if res.status != 200 or res.headers.get_content_type() != "application/json":
            raise ValueError("bad key response")
        data = res.read(65537)
        if len(data) > 65536:
            raise ValueError("large key response")
        return json.loads(data.decode("utf-8"), object_pairs_hook=_no_duplicate_keys)


def verify_vercel_service_identity(token, *, _synthetic_jwks=None, _now=None):
    """Verify RS256 JWT with team-scoped Vercel JWKS AND exact service claims.

    _synthetic_jwks is test-only, forbidden without explicit synthetic setting.
    Never expose this override through a request parameter or public handler.
    """
    policy = _policy()
    try:
        if not isinstance(token, str) or len(token) > 10000:
            raise ValueError("JWT unavailable")
        parts = token.split(".")
        if len(parts) != 3:
            raise ValueError("JWT segments")
        header = json.loads(_decode(parts[0], 2048), object_pairs_hook=_no_duplicate_keys)
        claims = json.loads(_decode(parts[1], 4096), object_pairs_hook=_no_duplicate_keys)
        signature = _decode(parts[2], 2048)
        if not isinstance(header, dict) or not isinstance(claims, dict):
            raise ValueError("JWT structure")
        kid = header.get("kid")
        if (
            header.get("alg") != "RS256" or header.get("typ") != "JWT"
            or not isinstance(kid, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", kid)
            or "jku" in header or "jwk" in header or "x5u" in header
        ):
            raise ValueError("JWT algorithm/header")
        if _synthetic_jwks is not None:
            if getattr(settings, "F09_C3_SYNTHETIC_JWKS_ALLOWED", False) is not True:
                raise ValueError("untrusted key source")
            jwks = _synthetic_jwks
        else:
            jwks = _pinned_vercel_jwks(policy["issuer"])
        if not isinstance(jwks, dict) or not isinstance(jwks.get("keys"), list):
            raise ValueError("JWKS structure")
        matching = [k for k in jwks["keys"] if isinstance(k, dict) and k.get("kid") == kid]
        if len(matching) != 1:
            raise ValueError("unknown or duplicate signing key")
        jwk = matching[0]
        if (jwk.get("kty") != "RSA" or jwk.get("alg", "RS256") != "RS256"
                or jwk.get("use", "sig") != "sig"):
            raise ValueError("unsupported key")
        n = int.from_bytes(_decode(jwk["n"], 1024), "big")
        e = int.from_bytes(_decode(jwk["e"], 16), "big")
        if not 2048 <= n.bit_length() <= 4096 or e != 65537:
            raise ValueError("weak or unexpected key")
        rsa.RSAPublicNumbers(e, n).public_key().verify(
            signature, (parts[0] + "." + parts[1]).encode("ascii"),
            padding.PKCS1v15(), hashes.SHA256(),
        )
        now = int(time.time()) if _now is None else int(_now)
        issued, not_before, expires = (claims.get(k) for k in ("iat", "nbf", "exp"))
        if (
            type(issued) is not int or type(not_before) is not int
            or type(expires) is not int or issued > now + 30
            or not_before > now + 30 or expires <= now
            or issued > not_before + 30 or not_before > expires
            or expires - issued > 3660 or now - issued > 3660
        ):
            raise ValueError("JWT time")
        if (
            claims.get("iss") != policy["issuer"]
            or claims.get("aud") != policy["audience"]
            or claims.get("sub") != policy["subject"]
            or claims.get("owner") != policy["owner"]
            or claims.get("project") != policy["project"]
            or claims.get("project_id") != policy["project_id"]
            or claims.get("environment") != "preview"
        ):
            raise ValueError("JWT service claims")
        return True
    except (ValueError, TypeError, KeyError, IndexError, OverflowError,
            InvalidSignature, binascii.Error, OSError):
        raise WebRefreshC3Rejected(_FAILURE) from None


def rotate_web_refresh_c3_candidate(*, oidc_token, signed_headers, signed_body,
                                    family_id, raw_refresh_secret, origin,
                                    cookie_csrf, header_csrf,
                                    _synthetic_jwks=None):
    """One synthetic, guarded family rotation; NEVER an HTTP authenticator.

    Checks service identity, unique BFF request nonce, then locks the family
    across the CSRF/refresh rotation. The nonce is durably spent EVEN when
    patient-family authorization fails. No access bearer is minted.
    """
    _policy()
    verify_vercel_service_identity(oidc_token, _synthetic_jwks=_synthetic_jwks)
    if type(family_id) is not int or family_id <= 0:
        raise WebRefreshC3Rejected(_FAILURE)
    try:
        # Intentionally outside the family transaction: a failed CSRF or
        # stale family must NOT allow reusing a valid transport envelope.
        verify_bff_refresh_envelope(
            headers=signed_headers, body=signed_body,
            method="POST", path="/api/v1/auth/refresh",
        )
    except WebRefreshBoundaryRejected:
        raise WebRefreshC3Rejected(_FAILURE) from None

    result = None
    try:
        with transaction.atomic():
            family = WebRefreshFamily.objects.select_for_update().get(pk=family_id)
            if not verify_family_csrf(
                family, origin=origin,
                cookie_token=cookie_csrf, header_token=header_csrf,
            ):
                raise WebRefreshC3Rejected(_FAILURE)
            if not hmac.compare_digest(family.current_digest, _digest(raw_refresh_secret)):
                raise WebRefreshC3Rejected(_FAILURE)
            try:
                # Uses nested atomic with same family lock; profile-version and
                # absolute/idle gates are retained from F09-B.
                result = rotate_web_refresh_family(raw_refresh_secret)
            except WebRefreshRejected:
                # Allow F09-B's revocation to COMMIT rather than rolling back
                # account-wide replay invalidation in the outer transaction.
                result = None
    except (WebRefreshFamily.DoesNotExist, WebRefreshRejected):
        raise WebRefreshC3Rejected(_FAILURE) from None
    if result is None:
        raise WebRefreshC3Rejected(_FAILURE)
    return result
