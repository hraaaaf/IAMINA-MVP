"""W02-F09-C6: UNMOUNTED Django-Ninja family Web bearer authenticator.

In contrast to the existing clinical auth chain, this candidate NEVER
authorizes via a Django session cookie, native bearer, Firebase, a BFF
service-identity header, or any other fallback. Its only source of patient
authority is an explicit short-lived C5 bearer checked on EVERY request
against the PostgreSQL refresh family and account generation.

This class is NOT added to diabetes.api.main, core.api routers, or settings.
An isolated test-only Django-Ninja URLconf exercises the actual HTTP API
protocol. Flag defaults to ABSENT/FALSE; no patient routing or access.
"""

from __future__ import annotations

from django.conf import settings
from ninja.security import HttpBearer

from core.web_refresh_c5_family_bearer import (
    WebFamilyBearerRejected,
    verify_family_bound_web_bearer,
)


class CandidateWebFamilyHttpBearer(HttpBearer):
    """Explicit Web bearer authority; no mixing with native Django cookie."""

    def authenticate(self, request, token: str):
        if getattr(settings, "F09_C6_HTTP_AUTH_ENABLED", False) is not True:
            return None

        # Do not trust direct invocations without the same bearer on the
        # actual request. Strict single Authorization field is intentional.
        if (
            not isinstance(token, str)
            or not token.startswith("iamina-web.")
            or request.META.get("HTTP_AUTHORIZATION") != "Bearer " + token
        ):
            return None

        # Explicitly forbid mixed Django session authority, even when both
        # happen to resolve to the SAME account. This keeps C6 access distinct
        # from the existing parallel cookie/native auth paths.
        if settings.SESSION_COOKIE_NAME in request.COOKIES:
            return None
        session_user = getattr(request, "user", None)
        if session_user is not None and session_user.is_authenticated:
            return None

        try:
            user = verify_family_bound_web_bearer(token)
        except WebFamilyBearerRejected:
            return None

        # Ninja uses this returned user as request.auth, not request input.
        request.user = user
        return user
