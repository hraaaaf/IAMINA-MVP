"""
Auth smoke tests: Firebase JWT + Ninja API.

Rewritten from Django-view tests — app migrated to Firebase JWT + Ninja API.
Original tests covered: login page render, credential validation, login-required redirects.
Equivalent API behaviour verified here via /api/v1/auth/firebase and protected routes.
"""
from unittest.mock import patch

from django.test import Client, TestCase


class LoginFlowTests(TestCase):
    """Firebase JWT auth flow replaces the Django login page."""

    def setUp(self):
        self.client = Client()

    def test_login_page_renders(self):
        """POST /api/v1/auth/firebase without id_token → 422 (endpoint live, schema enforced)."""
        resp = self.client.post(
            "/api/v1/auth/firebase",
            data={},
            content_type="application/json",
        )
        # Missing required id_token field → Ninja/Pydantic returns 422 Unprocessable Entity
        self.assertEqual(resp.status_code, 422)

    def test_login_with_valid_credentials_redirects(self):
        """Valid Firebase token → 200, user created, email returned in response body."""
        with patch("firebase_admin.auth.verify_id_token",
                   return_value={"uid": "uid-auth-valid", "email": "valid@auth.com"}):
            resp = self.client.post(
                "/api/v1/auth/firebase",
                data={"id_token": "valid-firebase-jwt"},
                content_type="application/json",
            )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["user"]["email"], "valid@auth.com")
        self.assertIn("message", data)

    def test_login_with_bad_password_stays_on_page(self):
        """Expired/invalid Firebase token → 401 (not silently accepted, not 403)."""
        with patch("firebase_admin.auth.verify_id_token",
                   side_effect=Exception("Token expired")):
            resp = self.client.post(
                "/api/v1/auth/firebase",
                data={"id_token": "bad-token"},
                content_type="application/json",
            )
        self.assertEqual(resp.status_code, 401)


class LoginRequiredTests(TestCase):
    """Anonymous requests to protected API routes must return 401, not a 302 redirect."""

    def test_dashboard_redirects_anonymous(self):
        """GET /api/v1/logs without authentication → 401."""
        resp = self.client.get("/api/v1/logs", content_type="application/json")
        self.assertEqual(resp.status_code, 401)

    def test_log_entry_redirects_anonymous(self):
        """POST /api/v1/logs without authentication → 401."""
        resp = self.client.post(
            "/api/v1/logs",
            data={"blood_sugar": 120},
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 401)

    def test_ai_summary_redirects_anonymous(self):
        """POST /api/v1/ai/summary without authentication → 401."""
        resp = self.client.post(
            "/api/v1/ai/summary",
            data={"days": 14},
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 401)


class DemoModeTests(TestCase):
    """Demo scenarios endpoint is public — no authentication required."""

    def test_demo_view_logs_user_in_and_redirects(self):
        """GET /api/v1/demo/scenarios is public and returns exactly 8 demo scenarios."""
        resp = self.client.get("/api/v1/demo/scenarios")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(len(data), 8)
