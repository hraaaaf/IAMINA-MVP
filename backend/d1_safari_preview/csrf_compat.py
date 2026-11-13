"""D1-only handling for mobile Safari opaque Origin on same-origin fetch.

Django rejects Origin: null, even when a same-origin Safari fetch carries a
valid CSRF token. Never whitelist "null" globally. Do not relax patient routes.
"""
from __future__ import annotations

from urllib.parse import urlsplit

from django.conf import settings


_LAB_POSTS = frozenset({"/d1-research/lab/start"})
_PASSKEY_PREFIX = "/api/v1/d1-research/passkey/"


def _same_lab_referer(value: str, expected_origin: str) -> bool:
    if not value:
        return False
    try:
        parsed = urlsplit(value)
        origin = urlsplit(expected_origin)
    except ValueError:
        return False
    return (
        parsed.scheme == "https"
        and parsed.netloc == origin.netloc
        and parsed.hostname == origin.hostname
        and parsed.port is None
        and parsed.path == "/d1-research/safari/"
        and not parsed.username
        and not parsed.password
    )


class SafariNullOriginCsrfGuard:
    """Normalize Origin only with positive same-origin browser evidence.

    CSRF middleware still validates the independent token/cookie and request.
    Untrusted origins, navigation modes and cross-site Fetch Metadata fail closed.
    This adapter is exclusively installed in D1 Preview settings.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if (
            request.method == "POST"
            and request.META.get("HTTP_ORIGIN") == "null"
            and (
                request.path_info in _LAB_POSTS
                or request.path_info.startswith(_PASSKEY_PREFIX)
            )
            and getattr(settings, "D1_PASSKEY_RESEARCH_ENABLED", False) is True
            and settings.ROOT_URLCONF == "d1_safari_preview.urls"
        ):
            rp_id = getattr(settings, "D1_PASSKEY_RESEARCH_RP_ID", "")
            expected_origin = getattr(settings, "D1_PASSKEY_RESEARCH_ORIGIN", "")
            site = request.META.get("HTTP_SEC_FETCH_SITE", "").lower()
            mode = request.META.get("HTTP_SEC_FETCH_MODE", "").lower()
            referer = request.META.get("HTTP_REFERER", "")
            valid_referer = _same_lab_referer(referer, expected_origin)

            # "cross-site", "same-site" and "none" are all rejected.
            # Absent Fetch Metadata needs a trustworthy same-origin Referer.
            safe_site = site == "same-origin" or (not site and valid_referer)
            safe_mode = mode in ("", "cors", "same-origin")
            if (
                request.is_secure()
                and rp_id
                and expected_origin == "https://" + rp_id
                and request.get_host().lower() == rp_id
                and safe_site
                and safe_mode
                and (not referer or valid_referer)
            ):
                request.META["HTTP_ORIGIN"] = expected_origin
        return self.get_response(request)
