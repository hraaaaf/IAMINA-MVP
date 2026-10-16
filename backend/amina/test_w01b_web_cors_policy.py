"""W01-B synthetic Web CORS contract: restrict credentialed origins.

Tests only Django middleware with fake responses; no network, database,
patient data, Vercel or Neon interaction. Does not certify real deployment.
"""
from __future__ import annotations

from corsheaders.middleware import CorsMiddleware
from django.http import HttpResponse
from django.test import RequestFactory, SimpleTestCase, override_settings

from amina.middleware.vercel_csrf import (
    IAMINA_FRONTEND_DEPLOYMENT_ORIGIN_RE,
    IAMINA_FRONTEND_STABLE_ORIGIN,
)


@override_settings(
    DEBUG=False,
    CORS_ALLOW_ALL_ORIGINS=False,
    CORS_ALLOWED_ORIGINS=[IAMINA_FRONTEND_STABLE_ORIGIN],
    CORS_ALLOWED_ORIGIN_REGEXES=[IAMINA_FRONTEND_DEPLOYMENT_ORIGIN_RE.pattern],
    CORS_ALLOW_CREDENTIALS=True,
)
class WebCorsSyntheticTests(SimpleTestCase):
    deployment_origin = (
        "https://iamina-review-2mktk1kof-achraf-benmoussa-s-projects.vercel.app"
    )

    def _response(self, origin: str | None, *, preflight: bool = False):
        headers = {"HTTP_ORIGIN": origin} if origin is not None else {}
        if preflight:
            headers["HTTP_ACCESS_CONTROL_REQUEST_METHOD"] = "GET"
            request = RequestFactory().options("/api/v1/health", **headers)
        else:
            request = RequestFactory().get("/api/v1/health", **headers)
        return CorsMiddleware(lambda _: HttpResponse(status=200))(request)

    def test_exact_review_alias_can_call_web_api(self):
        response = self._response(IAMINA_FRONTEND_STABLE_ORIGIN)
        self.assertEqual(
            response.get("Access-Control-Allow-Origin"),
            IAMINA_FRONTEND_STABLE_ORIGIN,
        )
        self.assertEqual(response.get("Access-Control-Allow-Credentials"), "true")

    def test_known_project_deployment_can_call_web_api(self):
        response = self._response(self.deployment_origin)
        self.assertEqual(
            response.get("Access-Control-Allow-Origin"), self.deployment_origin
        )

    def test_unrelated_vercel_project_is_denied(self):
        response = self._response("https://unrelated-app.vercel.app")
        self.assertNotIn("Access-Control-Allow-Origin", response)
        self.assertNotIn("Access-Control-Allow-Credentials", response)

    def test_account_lookalike_is_denied(self):
        response = self._response(
            "https://iamina-review-2mktk1kof-attacker-projects.vercel.app"
        )
        self.assertNotIn("Access-Control-Allow-Origin", response)

    def test_http_downgrade_is_denied(self):
        response = self._response("http://iamina-review.vercel.app")
        self.assertNotIn("Access-Control-Allow-Origin", response)

    def test_absent_origin_gets_no_cors_credentials(self):
        response = self._response(None)
        self.assertNotIn("Access-Control-Allow-Origin", response)
        self.assertNotIn("Access-Control-Allow-Credentials", response)

    def test_allowed_preflight_is_scoped_to_review_alias(self):
        response = self._response(IAMINA_FRONTEND_STABLE_ORIGIN, preflight=True)
        self.assertEqual(
            response.get("Access-Control-Allow-Origin"),
            IAMINA_FRONTEND_STABLE_ORIGIN,
        )

    def test_attacker_preflight_is_denied(self):
        response = self._response("https://attacker.example", preflight=True)
        self.assertNotIn("Access-Control-Allow-Origin", response)
