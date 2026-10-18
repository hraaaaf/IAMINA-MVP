"""Narrow CSRF exemptions and request-scoped AI operation identity.

Cookie/session-authenticated API requests must remain protected by Django's
CsrfViewMiddleware. Only bearer-token requests and the Firebase token bootstrap
endpoint are exempted here.
"""

import os

from django.http import JsonResponse

from core.ai_operation_identity import (
    InvalidIdempotencyKey,
    ai_operation_request_scope,
)


class CsrfExemptApiMiddleware:
    """Apply CSRF exemption only to non-cookie authentication flows."""

    _EXEMPT_PATHS = frozenset({"/api/v1/auth/firebase"})
    _STATELESS_BOOTSTRAP_PATHS = frozenset({
        "/api/v1/auth/login",
        "/api/v1/auth/register",
        "/api/v1/auth/firebase",
        "/api/v1/auth/password/reset/request",
        "/api/v1/auth/password/reset/confirm",
    })
    _PREVIEW_API_PROJECT = "prj_Pn9FnyconF3h2w9gOU74iV98kJoU"

    def _is_stateless_preview_bootstrap(self, request):
        """No ambient authority/cookies, and never on another Vercel project.

        The public custom header alone is NOT authentication; the protected
        API project must validate the workload OIDC at its Vercel edge.
        """
        return (
            os.environ.get("VERCEL_ENV") == "preview"
            and os.environ.get("VERCEL_PROJECT_ID") == self._PREVIEW_API_PROJECT
            and request.method == "POST"
            and request.path in self._STATELESS_BOOTSTRAP_PATHS
            and request.META.get("HTTP_X_IAMINA_STATELESS_BOOTSTRAP")
            == "w01-preview-v1"
            and not request.COOKIES
            and not request.META.get("HTTP_ORIGIN")
            and not request.META.get("HTTP_REFERER")
            and not request.META.get("HTTP_AUTHORIZATION")
        )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        authorization = request.META.get("HTTP_AUTHORIZATION", "")
        uses_bearer_auth = authorization.lower().startswith("bearer ")

        stateless_bootstrap = self._is_stateless_preview_bootstrap(request)
        if stateless_bootstrap:
            # No Django session is ever opened by this login/register request.
            setattr(request, "_iamina_stateless_bootstrap", True)
        if uses_bearer_auth or request.path in self._EXEMPT_PATHS or stateless_bootstrap:
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
