"""P0 regression tests for API CSRF and glucose-unit safety boundaries."""

import json

from django.http import JsonResponse
from django.test import RequestFactory, SimpleTestCase

from amina.middleware.csrf_exempt_api import CsrfExemptApiMiddleware
from diabetes.middleware.unit_guard import UnitGuardMiddleware


class CsrfExemptionBoundaryTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = CsrfExemptApiMiddleware(lambda request: JsonResponse({"ok": True}))

    def test_session_style_api_request_is_not_csrf_exempt(self):
        request = self.factory.post("/api/v1/account/consent", data={})

        self.middleware(request)

        self.assertFalse(
            getattr(request, "_dont_enforce_csrf_checks", False),
            "Cookie/session API requests must remain protected by CSRF middleware.",
        )

    def test_bearer_request_is_csrf_exempt(self):
        request = self.factory.post(
            "/api/v1/account/consent",
            data={},
            HTTP_AUTHORIZATION="Bearer test-token",
        )

        self.middleware(request)

        self.assertTrue(getattr(request, "_dont_enforce_csrf_checks", False))

    def test_firebase_bootstrap_is_csrf_exempt_without_session(self):
        request = self.factory.post("/api/v1/auth/firebase", data={"id_token": "x"})

        self.middleware(request)

        self.assertTrue(getattr(request, "_dont_enforce_csrf_checks", False))


class UnitGuardBoundaryTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.seen_request = None

        def downstream(request):
            self.seen_request = request
            return JsonResponse({"ok": True})

        self.middleware = UnitGuardMiddleware(downstream)

    def test_legacy_logs_path_is_guarded(self):
        request = self.factory.post("/api/v1/logs", data={})
        self.assertTrue(self.middleware._is_guarded(request))

    def test_registry_namespaced_module_path_is_guarded(self):
        request = self.factory.post("/api/v1/diabetes/logs", data={})
        self.assertTrue(self.middleware._is_guarded(request))

    def test_unrelated_api_path_is_not_guarded(self):
        request = self.factory.post("/api/v1/profile", data={})
        self.assertFalse(self.middleware._is_guarded(request))

    def test_namespaced_glucose_payload_is_normalized(self):
        request = self.factory.post(
            "/api/v1/diabetes/logs",
            data=json.dumps({"blood_sugar": 5.5, "unit": "mmol/L"}),
            content_type="application/json",
        )

        response = self.middleware(request)

        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(self.seen_request)
        normalized = json.loads(self.seen_request.body)
        self.assertEqual(normalized["blood_sugar"], 99.1)
        self.assertEqual(normalized["unit"], "mg/dL")

    def test_unexpected_normalization_error_fails_closed(self):
        request = self.factory.post(
            "/api/v1/diabetes/logs",
            data=json.dumps({"blood_sugar": "not-a-number", "unit": "mg/dL"}),
            content_type="application/json",
        )

        response = self.middleware(request)

        self.assertEqual(response.status_code, 422)
        self.assertIsNone(self.seen_request)
        payload = json.loads(response.content)
        self.assertEqual(payload["code"], "UNIT_GUARD_INTERNAL_REJECTION")
