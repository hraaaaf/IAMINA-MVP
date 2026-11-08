"""W02-F09-C7 combined candidate: one transaction for refresh+bearer+CSRF.

NEVER mounted: real frontend/api/session-refresh.js and Django URLs stay off.
BFF OIDC and one-time request nonce are verified/CONSUMED BEFORE opening
the family transaction; errors in issuance then roll back refresh rotation,
while the signed HTTP request cannot be reused. All credentials synthetic.

The signed candidate reply is returned only to an internal test caller; C7
BFF must independently verify its MAC before constructing browser headers.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import re
from datetime import timedelta

from django.conf import settings
from django.core.exceptions import DisallowedHost
from django.db import DatabaseError, connection, transaction
from django.utils import timezone

from core.models import WebRefreshFamily
from core.web_refresh_boundary import (
    WebRefreshBoundaryRejected,
    issue_family_csrf,
    verify_bff_refresh_envelope,
    verify_family_csrf,
)
from core.web_refresh_c3_candidate import (
    WebRefreshC3Rejected,
    _no_duplicate_keys,
    verify_vercel_service_identity,
)
from core.web_refresh_c4_http_candidate import (
    _API_HOST,
    _KEYS,
    _REFRESH,
    _TRANSPORT,
)
from core.web_refresh_c5_family_bearer import (
    WebFamilyBearerRejected,
    issue_family_bound_web_bearer,
)
from core.web_refresh_protocol import (
    WebRefreshRejected,
    _digest,
    _limits,
    rotate_web_refresh_family,
)

_FAIL = "web_refresh_c7_unavailable"
_RESPONSE_SCOPE = "iamina.web.c7.signed-response.v1"
_KEY_RE = re.compile(r"^[A-Za-z0-9_-]{32,128}$")

# Migration history from the current C7 source branch only. Never accept
# an out-of-tree W01/D2 history sharing 0020/0021 migration numbers. This is
# a secondary runtime fail-closed control, NOT DDL approval.
_EXPECTED_CORE_TAIL = frozenset({
    "0019_auth_abuse_bucket",
    "0020_web_refresh_candidate",
    "0021_web_refresh_transport_nonce",
})


def _compatible_runtime_lineage():
    """Read migration names only; if ledger is unavailable, reject C7."""
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT name FROM django_migrations "
                "WHERE app = %s AND name >= %s",
                ["core", "0019"],
            )
            names = [name for (name,) in cursor.fetchall()]
    except (DatabaseError, TypeError, ValueError):
        return False
    return len(names) == len(_EXPECTED_CORE_TAIL) and set(names) == _EXPECTED_CORE_TAIL



class WebRefreshC7Rejected(Exception):
    """Uniform rejection that never exposes secrets, patient or policy data."""


def _policy():
    if (
        getattr(settings, "F09_C7_ATOMIC_ENABLED", False) is not True
        or getattr(settings, "F09_C4_HTTP_ADAPTER_ENABLED", False) is not True
        or getattr(settings, "F09_C5_FAMILY_ACCESS_ENABLED", False) is not True
    ):
        raise WebRefreshC7Rejected(_FAIL)
    key = getattr(settings, "F09_C7_RESPONSE_HMAC_KEY", None)
    transport = getattr(settings, "F09_C2_BFF_HMAC_KEY", None)
    csrf = getattr(settings, "F09_C2_CSRF_HMAC_KEY", None)
    cookie_cap = getattr(settings, "F09_C7_COOKIE_MAX_AGE_SECONDS", None)
    access_cap = getattr(settings, "F09_C5_ACCESS_MAX_AGE_SECONDS", None)
    if (
        not isinstance(key, str)
        or not _KEY_RE.fullmatch(key)
        or key in (settings.SECRET_KEY, transport, csrf)
        or type(cookie_cap) is not int
        or not 1 <= cookie_cap <= 900
        or type(access_cap) is not int
        or not 1 <= access_cap <= cookie_cap
    ):
        raise WebRefreshC7Rejected(_FAIL)
    if not _compatible_runtime_lineage():
        raise WebRefreshC7Rejected(_FAIL)
    return key.encode("ascii"), cookie_cap, access_cap


def _parsed_request(request):
    expected_api_host = getattr(settings, "F09_C4_EXPECTED_API_HOST", None)
    try:
        if (
            not isinstance(expected_api_host, str)
            or not _API_HOST.fullmatch(expected_api_host)
            or request.method != "POST"
            or request.path != "/api/v1/auth/refresh"
            or request.get_host() != expected_api_host
            or request.content_type != "application/json"
            or request.META.get("HTTP_AUTHORIZATION")
            or request.META.get("HTTP_COOKIE")
        ):
            raise ValueError("invalid HTTP boundary")
        raw_body = request.body
        if not isinstance(raw_body, bytes) or not 0 < len(raw_body) <= 4096:
            raise ValueError("invalid body")
        values = json.loads(raw_body.decode("utf-8"), object_pairs_hook=_no_duplicate_keys)
        if not isinstance(values, dict) or set(values) != _KEYS:
            raise ValueError("invalid JSON keys")
        family_id = values["family_id"]
        if (
            type(family_id) is not int
            or family_id <= 0
            or not isinstance(values["raw_refresh"], str)
            or not _REFRESH.fullmatch(values["raw_refresh"])
            or any(not isinstance(values[k], str)
                   for k in ("origin", "csrf_cookie", "csrf_header"))
        ):
            raise ValueError("invalid fields")
        headers = {k: request.headers.get(k) for k in _TRANSPORT}
        return raw_body, values, headers, request.headers.get(
            "x-vercel-trusted-oidc-idp-token"
        )
    except (ValueError, TypeError, UnicodeError, DisallowedHost):
        raise WebRefreshC7Rejected(_FAIL) from None


def _response_mac(key, *, nonce, timestamp, body):
    message = "\n".join((
        _RESPONSE_SCOPE,
        "POST",
        "/api/v1/auth/refresh",
        str(timestamp),
        str(nonce),
        hashlib.sha256(body).hexdigest(),
    ))
    return "v1." + hmac.new(key, message.encode("ascii"), hashlib.sha256).hexdigest()


def execute_unmounted_atomic_refresh_bundle(request, *, _synthetic_jwks=None):
    """Return signed INTERNAL (body, headers). Never a browser HTTP response.

    A valid Vercel service JWT proves the BFF, not a patient. The signed BFF
    request nonce is consumed in its OWN committed transaction before any
    family work. Family ownership follows the DB row, MAC-bound CSRF, current
    opaque secret and account version. Rotation, C5 bearer and new CSRF live
    inside ONE PostgreSQL transaction; any post-rotation failure rolls back.
    """
    key, cookie_cap, access_cap = _policy()
    body, fields, signed_headers, oidc_token = _parsed_request(request)
    try:
        verify_vercel_service_identity(oidc_token, _synthetic_jwks=_synthetic_jwks)
        # Durable anti-replay outside the subsequent family transaction.
        verify_bff_refresh_envelope(
            headers=signed_headers, body=body,
            method="POST", path="/api/v1/auth/refresh",
        )
    except (WebRefreshC3Rejected, WebRefreshBoundaryRejected):
        raise WebRefreshC7Rejected(_FAIL) from None

    try:
        with transaction.atomic():
            family = WebRefreshFamily.objects.select_for_update().get(
                pk=fields["family_id"]
            )
            if not verify_family_csrf(
                family,
                origin=fields["origin"],
                cookie_token=fields["csrf_cookie"],
                header_token=fields["csrf_header"],
            ):
                raise WebRefreshC7Rejected(_FAIL)
            if not hmac.compare_digest(
                family.current_digest, _digest(fields["raw_refresh"])
            ):
                raise WebRefreshC7Rejected(_FAIL)

            # Nested select_for_update and atomic are SAVEPOINT operations;
            # the C7 outer transaction owns the final commit.
            replacement = rotate_web_refresh_family(fields["raw_refresh"])
            bearer = issue_family_bound_web_bearer(family.pk, replacement)
            family.refresh_from_db()
            new_csrf = issue_family_csrf(family, origin=fields["origin"])
            idle, absolute = _limits()
            now = timezone.now()
            deadlines = (
                family.idle_deadline,
                family.expires_at,
                family.last_rotated_at + timedelta(seconds=idle),
                family.issued_at + timedelta(seconds=absolute),
            )
            seconds = min(int((deadline - now).total_seconds())
                          for deadline in deadlines)
            age = min(seconds, cookie_cap)
            if age <= 0 or access_cap > age:
                raise WebRefreshC7Rejected(_FAIL)

            payload = {
                "familyId": str(family.pk),
                "refreshSecret": replacement,
                "csrfToken": new_csrf,
                "accessBearer": bearer,
                "cookieMaxAgeSeconds": age,
                "accessMaxAgeSeconds": access_cap,
            }
            response_body = json.dumps(
                payload, sort_keys=True, separators=(",", ":"),
            ).encode("ascii")

        # Signed only AFTER commit; caller must verify before browser use.
        result_headers = {
            "content-type": "application/json",
            "cache-control": "no-store",
            "x-iamina-c7-reply-proof": _response_mac(
                key,
                nonce=signed_headers["x-iamina-bff-nonce"],
                timestamp=signed_headers["x-iamina-bff-timestamp"],
                body=response_body,
            ),
        }
        return {"status": 200, "headers": result_headers, "body": response_body}
    except (
        WebRefreshFamily.DoesNotExist, WebRefreshBoundaryRejected,
        WebRefreshRejected, WebFamilyBearerRejected, ValueError, TypeError,
    ):
        raise WebRefreshC7Rejected(_FAIL) from None
