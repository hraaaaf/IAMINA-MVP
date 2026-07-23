"""Narrow CSRF exemptions for API requests that cannot rely on cookie auth.

Cookie/session-authenticated API requests must remain protected by Django's
CsrfViewMiddleware. Only bearer-token requests and the Firebase token bootstrap
endpoint are exempted here.
"""


class CsrfExemptApiMiddleware:
    """Apply CSRF exemption only to non-cookie authentication flows."""

    _EXEMPT_PATHS = frozenset({"/api/v1/auth/firebase"})

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        authorization = request.META.get("HTTP_AUTHORIZATION", "")
        uses_bearer_auth = authorization.lower().startswith("bearer ")

        if uses_bearer_auth or request.path in self._EXEMPT_PATHS:
            setattr(request, "_dont_enforce_csrf_checks", True)

        return self.get_response(request)
