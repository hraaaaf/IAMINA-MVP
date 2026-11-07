"""W02-F09-C4 isolated HTTP-request adapter. NEVER mounted as a Django route.

The live Vercel Web refresh handler remains a permanent 404. This parser
accepts ONLY a body assembled and signed by the dedicated BFF, then delegates
to C3's independently verified service JWT and PostgreSQL-locked family CSRF
and refresh rotation. It does not emit headers, access bearer or cookies.

No clinical identity is trusted from family_id, Origin, or the JWT alone.
Only signed service+request+opaque family secret+current family CSRF together
can rotate a candidate family. Feature flag is absent/False by default.
"""

from __future__ import annotations

import json
import re

from django.conf import settings

from core.web_refresh_c3_candidate import (
    WebRefreshC3Rejected,
    _no_duplicate_keys,
    rotate_web_refresh_c3_candidate,
)

_FAIL = "web_refresh_c4_unavailable"
_API_HOST = re.compile(r"^[a-z0-9-]+\.vercel\.app$")
_REFRESH = re.compile(r"^iamina-wr1\.[A-Za-z0-9_-]{64}$")
_KEYS = frozenset(
    {"family_id", "raw_refresh", "origin", "csrf_cookie", "csrf_header"}
)
_TRANSPORT = (
    "x-iamina-bff-timestamp",
    "x-iamina-bff-nonce",
    "x-iamina-bff-origin",
    "x-iamina-bff-proof",
)


class WebRefreshC4Rejected(Exception):
    """One non-sensitive refusal for all candidate adapter failures."""


def execute_unmounted_web_refresh(request, *, _synthetic_jwks=None):
    """Return an opaque replacement to a *server-only* test caller.

    WARNING: this is an isolated internal function, not an HTTP handler.
    Callers MUST NEVER return the result in JSON, logs or a generic API.
    A future cookie+bearer response must be a separately approved contract.
    """
    if getattr(settings, "F09_C4_HTTP_ADAPTER_ENABLED", False) is not True:
        raise WebRefreshC4Rejected(_FAIL)

    expected_api_host = getattr(settings, "F09_C4_EXPECTED_API_HOST", None)
    if not isinstance(expected_api_host, str) or not _API_HOST.fullmatch(
        expected_api_host
    ):
        raise WebRefreshC4Rejected(_FAIL)

    try:
        if (
            request.method != "POST"
            or request.path != "/api/v1/auth/refresh"
            or request.get_host() != expected_api_host
            or request.content_type != "application/json"
            or request.META.get("HTTP_AUTHORIZATION")
            or request.META.get("HTTP_COOKIE")
        ):
            raise ValueError("unexpected HTTP request")
        body = request.body
        if not isinstance(body, bytes) or not 0 < len(body) <= 4096:
            raise ValueError("invalid payload length")

        values = json.loads(body.decode("utf-8"), object_pairs_hook=_no_duplicate_keys)
        if not isinstance(values, dict) or set(values) != _KEYS:
            raise ValueError("unexpected fields")
        family_id = values["family_id"]
        refresh = values["raw_refresh"]
        if (
            type(family_id) is not int
            or family_id <= 0
            or not isinstance(refresh, str)
            or not _REFRESH.fullmatch(refresh)
            or not isinstance(values["origin"], str)
            or not isinstance(values["csrf_cookie"], str)
            or not isinstance(values["csrf_header"], str)
        ):
            raise ValueError("invalid signed data types")
        headers = {name: request.headers.get(name) for name in _TRANSPORT}
        oidc = request.headers.get("x-vercel-trusted-oidc-idp-token")
        return rotate_web_refresh_c3_candidate(
            oidc_token=oidc,
            signed_headers=headers,
            signed_body=body,
            family_id=family_id,
            raw_refresh_secret=refresh,
            origin=values["origin"],
            cookie_csrf=values["csrf_cookie"],
            header_csrf=values["csrf_header"],
            _synthetic_jwks=_synthetic_jwks,
        )
    except (ValueError, UnicodeError, TypeError, WebRefreshC3Rejected):
        raise WebRefreshC4Rejected(_FAIL) from None
