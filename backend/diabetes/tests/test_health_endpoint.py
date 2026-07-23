"""
GET /api/v1/health — liveness + readiness probe tests.

Cases:
  1. Happy path  — DB ok, cache ok → 200 {"status": "ok"}
  2. DB down     — DB unreachable  → 503 {"status": "degraded"}
  3. Cache down  — cache miss      → 200 {"status": "ok"} (degraded is non-fatal)
  4. Response shape always has status/db/cache keys
"""
from unittest.mock import patch

from django.test import SimpleTestCase, TestCase


class HealthHappyPathTest(TestCase):
    """Normal operation: DB accessible, cache accessible."""

    def test_returns_200_when_db_ok(self):
        resp = self.client.get("/api/v1/health")
        self.assertEqual(resp.status_code, 200)

    def test_status_ok_when_db_ok(self):
        resp = self.client.get("/api/v1/health")
        data = resp.json()
        self.assertEqual(data["status"], "ok")

    def test_db_ok_in_response(self):
        resp = self.client.get("/api/v1/health")
        data = resp.json()
        self.assertEqual(data["db"], "ok")

    def test_response_has_all_required_keys(self):
        resp = self.client.get("/api/v1/health")
        data = resp.json()
        self.assertIn("status", data)
        self.assertIn("db",     data)
        self.assertIn("cache",  data)

    def test_method_get_only_no_body_required(self):
        # Health check must not require authentication or a request body
        resp = self.client.get("/api/v1/health")
        # Must not be 401 or 403
        self.assertNotEqual(resp.status_code, 401)
        self.assertNotEqual(resp.status_code, 403)


class HealthDbDownTest(SimpleTestCase):
    """Simulate a broken DB connection."""

    def test_returns_503_when_db_unreachable(self):
        from django.db import OperationalError
        with patch(
            "core.api.v1.health._check_db",
            return_value="error",
        ):
            resp = self.client.get("/api/v1/health")
        self.assertEqual(resp.status_code, 503)

    def test_status_degraded_when_db_down(self):
        with patch("core.api.v1.health._check_db", return_value="error"):
            resp = self.client.get("/api/v1/health")
        data = resp.json()
        self.assertEqual(data["status"], "degraded")
        self.assertEqual(data["db"],     "error")


class HealthCacheDownTest(SimpleTestCase):
    """Cache unavailable is non-fatal — overall status stays 'ok'."""

    def test_returns_200_when_only_cache_down(self):
        with patch("core.api.v1.health._check_db",    return_value="ok"), \
             patch("core.api.v1.health._check_cache", return_value="unavailable"):
            resp = self.client.get("/api/v1/health")
        self.assertEqual(resp.status_code, 200)

    def test_status_ok_when_only_cache_down(self):
        with patch("core.api.v1.health._check_db",    return_value="ok"), \
             patch("core.api.v1.health._check_cache", return_value="unavailable"):
            resp = self.client.get("/api/v1/health")
        data = resp.json()
        self.assertEqual(data["status"],  "ok")
        self.assertEqual(data["cache"],   "unavailable")

    def test_both_down_returns_503(self):
        with patch("core.api.v1.health._check_db",    return_value="error"), \
             patch("core.api.v1.health._check_cache", return_value="unavailable"):
            resp = self.client.get("/api/v1/health")
        self.assertEqual(resp.status_code, 503)
