"""Narrow CSRF exemptions and request-scoped AI operation identity.

Cookie/session-authenticated API requests must remain protected by Django's
CsrfViewMiddleware. Only bearer-token requests and the Firebase token bootstrap
endpoint are exempted here.
"""

from django.conf import settings
from django.http import JsonResponse

from core.ai_operation_identity import (
    InvalidIdempotencyKey,
    ai_operation_request_scope,
)


class CsrfExemptApiMiddleware:
    """Apply CSRF exemption only to non-cookie authentication flows."""

    _EXEMPT_PATHS = frozenset({"/api/v1/auth/firebase"})

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        authorization = request.META.get("HTTP_AUTHORIZATION", "")
        uses_bearer_auth = authorization.lower().startswith("bearer ")
        has_session_cookie = bool(
            request.COOKIES.get(settings.SESSION_COOKIE_NAME)
        )

        # An Authorization header cannot waive CSRF while a session cookie
        # exists. The bearer exemption is for cookie-less native clients only.
        if (uses_bearer_auth and not has_session_cookie) or (
            request.path in self._EXEMPT_PATHS
        ):
            setattr(request, "_dont_enforce_csrf_checks", True)

        try:
            with ai_operation_request_scope(
                request.META.get("HTTP_IDEMPOTENCY_KEY")
            ):
                return self.get_response(request)
        except InvalidIdempotencyKey:
            return JsonResponse(
                {
                    "error": {
                        "code": "invalid_idempotency_key",
                        "message": "Invalid Idempotency-Key header.",
                    }
                },
                status=400,
            )
