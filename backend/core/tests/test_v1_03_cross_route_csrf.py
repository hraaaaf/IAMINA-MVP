"""V1-03 #927: real Django-client cookie CSRF matrix, no patient mutation."""

from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import Client, TestCase

from amina.vercel_session_auth import SessionAuth
from core.native_auth import issue_native_token, verify_native_token
from diabetes.api.v1.security import HybridBearerAuth


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
        token = issue_native_token(self.user)
        self.assertEqual(verify_native_token(token).pk, self.user.pk)
        native = Client(enforce_csrf_checks=True)
        seen = []
        original_bearer = HybridBearerAuth.__call__
        original_session = SessionAuth.__call__

        def observe_bearer(auth, request):
            result = original_bearer(auth, request)
            seen.append({
                "backend": "bearer",
                "header_present": bool(request.headers.get("Authorization")),
                "accepted": bool(result),
            })
            return result

        def observe_session(auth, request):
            result = original_session(auth, request)
            seen.append({"backend": "session", "accepted": bool(result)})
            return result

        with (
            patch.object(HybridBearerAuth, "__call__", observe_bearer),
            patch.object(SessionAuth, "__call__", observe_session),
        ):
            for method, path, expected in self.CASES:
                with self.subTest(method=method, path=path):
                    response = self._send(
                        native, method, path,
                        HTTP_AUTHORIZATION=f"Bearer {token}",
                    )
                    self.assertEqual(
                        response.status_code, expected,
                        msg=(
                            f"auth_header_present="
                            f"{bool(response.wsgi_request.headers.get('Authorization'))}; "
                            f"cookies={list(response.wsgi_request.COOKIES)}; "
                            f"auth_callbacks={seen[-3:]}; "
                            f"payload={response.content[:200]!r}"
                        ),
                    )

    def test_valid_native_bearer_with_session_cookie_still_needs_csrf(self):
        token = issue_native_token(self.user)
        response = self._send(
            self.browser,
            "POST",
            "/api/v1/account/consent",
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(response.status_code, 403)

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
