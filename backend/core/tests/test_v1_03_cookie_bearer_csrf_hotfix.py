"""Regression: a forged Bearer header must not waive cookie-session CSRF.

Use only synthetic accounts and invalid JSON; no real patient content or mutations.
"""
from django.contrib.auth.models import User
from django.test import Client, TestCase


class CookieBearerCsrfHotfixTests(TestCase):
    MUTATIONS = (
        ("POST", "/api/v1/logs/batch"),
        ("POST", "/api/v1/account/consent"),
        ("PATCH", "/api/v1/profile"),
        ("POST", "/api/v1/ai/chat"),
        ("POST", "/api/v1/ai/chat/stream"),
    )

    def setUp(self):
        user = User.objects.create_user(username="csrf-bearer-synthetic")
        self.browser = Client(enforce_csrf_checks=True)
        self.browser.force_login(user)

    def test_cookie_plus_spoofed_bearer_cannot_waive_csrf_on_mutations(self):
        for method, path in self.MUTATIONS:
            with self.subTest(method=method, path=path):
                response = self.browser.generic(
                    method,
                    path,
                    data=b"{}",
                    content_type="application/json",
                    HTTP_AUTHORIZATION="Bearer invalid.synthetic.token",
                )
                self.assertEqual(response.status_code, 403)

    def test_valid_cookie_csrf_reaches_sse_json_schema_instead_of_forbidden(self):
        token = "a" * 32
        self.browser.cookies["csrftoken"] = token
        response = self.browser.post(
            "/api/v1/ai/chat/stream",
            data="{}",
            content_type="application/json",
            HTTP_X_CSRFTOKEN=token,
            HTTP_AUTHORIZATION="Bearer invalid.synthetic.token",
        )
        self.assertEqual(response.status_code, 422)
