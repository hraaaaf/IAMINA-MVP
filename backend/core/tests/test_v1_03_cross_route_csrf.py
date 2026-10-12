"""V1-03 #927: real Django-client cookie CSRF matrix, no patient mutation."""

import re

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import resolve

from core.native_auth import issue_native_token, verify_native_token
from diabetes.api.main import api


class ProtectedApiCookieCsrfTests(TestCase):
    # Each deliberately malformed payload must reach schema validation (422)
    # or a missing synthetic patient profile (404) ONLY after valid auth/CSRF.
    # No patient record or external provider is mutated in positive-path tests.
    CASES = (
        ("POST", "/api/v1/account/consent", 422),
        ("POST", "/api/v1/logs/batch", 422),
        ("PATCH", "/api/v1/profile", 404),
        ("PUT", "/api/v1/cgm/connection", 422),
    )

    def setUp(self):
        self.user = User.objects.create_user(username="csrf-matrix-synthetic")
        self.browser = Client(enforce_csrf_checks=True)
        self.browser.force_login(self.user)

    @staticmethod
    def _send(client, method, path, **headers):
        return client.generic(
            method, path, data=b"{}", content_type="application/json", **headers
        )

    def test_cookie_mutations_without_csrf_fail_before_validation(self):
        for method, path, _expected in self.CASES:
            with self.subTest(method=method, path=path):
                response = self._send(self.browser, method, path)
                self.assertEqual(response.status_code, 403)

    def test_forged_bearer_does_not_waive_cookie_csrf(self):
        for method, path, _expected in self.CASES:
            with self.subTest(method=method, path=path):
                response = self._send(
                    self.browser,
                    method,
                    path,
                    HTTP_AUTHORIZATION="Bearer invalid.synthetic.credential",
                )
                self.assertEqual(response.status_code, 403)

    def test_cookie_with_matching_csrf_reaches_endpoint_contract(self):
        secret = "a" * 32
        self.browser.cookies["csrftoken"] = secret
        for method, path, expected in self.CASES:
            with self.subTest(method=method, path=path):
                response = self._send(
                    self.browser, method, path, HTTP_X_CSRFTOKEN=secret
                )
                self.assertEqual(response.status_code, expected)

    def test_native_bearer_only_is_not_subject_to_cookie_csrf(self):
        from unittest.mock import patch
        from diabetes.api.v1.security import HybridBearerAuth

        token = issue_native_token(self.user)
        self.assertEqual(verify_native_token(token).pk, self.user.pk)
        native = Client(enforce_csrf_checks=True)
        original_auth = HybridBearerAuth.authenticate
        observed = []

        def observe_auth(instance, request, supplied_token):
            authenticated = original_auth(instance, request, supplied_token)
            observed.append({
                "token_matches": supplied_token == token,
                "authenticated": authenticated is not None,
                "cookie_present": bool(request.COOKIES.get("sessionid")),
            })
            return authenticated

        with patch.object(HybridBearerAuth, "authenticate", observe_auth):
            for method, path, expected in self.CASES:
                with self.subTest(method=method, path=path):
                    observed.clear()
                    response = self._send(
                        native,
                        method,
                        path,
                        HTTP_AUTHORIZATION=f"Bearer {token}",
                    )
                    self.assertEqual(
                        response.status_code, expected,
                        f"Bearer auth trace (no secret values): {observed!r}"
                    )

    def test_forged_bearer_without_session_cookie_is_unauthorized(self):
        native = Client(enforce_csrf_checks=True)
        for method, path, _expected in self.CASES:
            with self.subTest(method=method, path=path):
                response = self._send(
                    native,
                    method,
                    path,
                    HTTP_AUTHORIZATION="Bearer invalid.synthetic.credential",
                )
                self.assertEqual(response.status_code, 401)

    def test_valid_native_bearer_with_session_cookie_still_needs_csrf(self):
        token = issue_native_token(self.user)
        response = self._send(
            self.browser,
            "POST",
            "/api/v1/account/consent",
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(response.status_code, 403)

    def test_valid_native_bearer_with_session_cookie_and_csrf_reaches_contract(self):
        token = issue_native_token(self.user)
        secret = "b" * 32
        self.browser.cookies["csrftoken"] = secret
        for method, path, expected in self.CASES:
            with self.subTest(method=method, path=path):
                response = self._send(
                    self.browser,
                    method,
                    path,
                    HTTP_AUTHORIZATION=f"Bearer {token}",
                    HTTP_X_CSRFTOKEN=secret,
                )
                self.assertEqual(response.status_code, expected)

    def test_public_login_remains_reachable_after_session_is_created(self):
        # Regression: dashboard visual cert repeats login after receiving a
        # session cookie through a local frontend proxy origin.
        response = self._send(
            self.browser,
            "POST",
            "/api/v1/auth/login",
            HTTP_ORIGIN="http://127.0.0.1:7358",
        )
        self.assertEqual(response.status_code, 422)

    def test_cookie_safe_get_does_not_require_csrf(self):
        response = self.browser.get("/api/v1/account/consent")
        self.assertEqual(response.status_code, 200)

    def test_every_mounted_protected_unsafe_route_rejects_cookie_csrf_bypass(self):
        """Inventory routes from the live Ninja OpenAPI, not a guessed prefix.

        The middleware rejects these requests before schema/body validation or
        any endpoint side effects. Check canonical and forged Bearer headers.
        """
        schema = api.get_openapi_schema()
        methods = {"post", "put", "patch", "delete"}
        protected = [
            (method.upper(), template)
            for template, operations in schema["paths"].items()
            for method, operation in operations.items()
            if method in methods
            and any(
                "SessionAuth" in requirement
                for requirement in operation.get("security", [])
            )
        ]
        self.assertGreater(len(protected), 0, "No protected unsafe API routes found")

        for method, template in protected:
            # Synthetic URL values, never patient IDs. Resolve explicitly to
            # exclude phantom registry aliases (see #929).
            path = re.sub(r"\{[^{}]+\}", "1", template)
            with self.subTest(method=method, path=template):
                resolve(path)
                for header in ({}, {"HTTP_AUTHORIZATION": "Bearer invalid.synthetic"}):
                    response = self._send(self.browser, method, path, **header)
                    self.assertEqual(response.status_code, 403)
