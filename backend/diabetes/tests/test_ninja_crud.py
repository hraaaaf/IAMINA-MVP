"""
Ninja API — CRUD logs, patient isolation, onboarding, auth coverage.
Replaces the skipped Django-view tests in test_entries, test_auth,
test_onboarding, test_sidebar, test_ui_wiring, test_monorepo_migration.

All tests use force_login() via the conftest.py FirebaseAuth patch.
"""
from datetime import date, timedelta
from decimal import Decimal
from json import loads
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.utils import timezone

from core.models import BasePatientProfile
from diabetes.models import DiabetesProfile, LogEntry

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _make_patient(username, email=""):
    email = email or f"{username}@test.com"
    user = User.objects.create_user(username=username, email=email)
    base = BasePatientProfile.objects.create(
        patient=user,
        date_of_birth=date(1985, 6, 15),
    )
    DiabetesProfile.objects.create(
        base_profile=base,
        diabetes_type="type2",
        treatment_type="oral_meds",
        target_range_low=70,
        target_range_high=180,
    )
    return user


def _log(user, bg=120):
    return LogEntry.objects.create(patient=user, blood_sugar=Decimal(bg), logged_at=timezone.now())


# ─────────────────────────────────────────────────────────────────────────────
# 1. Auth protection — every protected route returns 401 without a token
# ─────────────────────────────────────────────────────────────────────────────

class AuthProtectionTests(TestCase):
    """Unauthenticated requests must get 401 — not 200, not 403, not 404."""

    PROTECTED_ROUTES = [
        ("GET",  "/api/v1/logs"),
        ("POST", "/api/v1/logs"),
        ("GET",  "/api/v1/logs/1"),
        ("DELETE", "/api/v1/logs/1"),
        ("POST", "/api/v1/ai/summary"),
        ("POST", "/api/v1/ai/chat"),
        ("GET",  "/api/v1/profile"),
    ]

    def test_all_protected_routes_return_401(self):
        c = Client()
        for method, path in self.PROTECTED_ROUTES:
            with self.subTest(method=method, path=path):
                fn = getattr(c, method.lower())
                resp = fn(path, content_type="application/json")
                self.assertEqual(
                    resp.status_code, 401,
                    f"{method} {path} should be 401, got {resp.status_code}",
                )


# ─────────────────────────────────────────────────────────────────────────────
# 2. Log CRUD via Ninja API
# ─────────────────────────────────────────────────────────────────────────────

class LogCRUDTests(TestCase):

    def setUp(self):
        self.alice = _make_patient("alice_crud")
        self.client.force_login(self.alice)

    def test_create_log_persists(self):
        resp = self.client.post(
            "/api/v1/logs",
            data={"blood_sugar": 130, "meal_type": "lunch"},
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        data = loads(resp.content)
        self.assertEqual(data["blood_sugar"], 130.0)
        self.assertTrue(LogEntry.objects.filter(patient=self.alice, blood_sugar=130).exists())

    def test_list_logs_returns_own_entries(self):
        _log(self.alice, 110)
        _log(self.alice, 150)
        resp = self.client.get("/api/v1/logs")
        self.assertEqual(resp.status_code, 200)
        data = loads(resp.content)
        self.assertEqual(len(data["items"]), 2)

    def test_list_logs_empty(self):
        resp = self.client.get("/api/v1/logs")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(loads(resp.content)["items"], [])

    def test_get_single_log(self):
        entry = _log(self.alice, 160)
        resp = self.client.get(f"/api/v1/logs/{entry.id}")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(loads(resp.content)["blood_sugar"], 160.0)

    def test_delete_log(self):
        entry = _log(self.alice, 170)
        resp = self.client.delete(f"/api/v1/logs/{entry.id}")
        self.assertEqual(resp.status_code, 204)
        self.assertFalse(LogEntry.objects.filter(id=entry.id).exists())

    def test_blood_sugar_stored_as_float(self):
        resp = self.client.post(
            "/api/v1/logs",
            data={"blood_sugar": 95.5},
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        entry = LogEntry.objects.get(patient=self.alice, blood_sugar=Decimal("95.5"))
        self.assertEqual(entry.blood_sugar, Decimal("95.5"))


# ─────────────────────────────────────────────────────────────────────────────
# 3. Patient isolation — Alice never touches Bob's data
# ─────────────────────────────────────────────────────────────────────────────

class PatientIsolationTests(TestCase):
    """Core security invariant: patient A cannot read, delete, or list B's logs."""

    def setUp(self):
        self.alice = _make_patient("alice_iso")
        self.bob   = _make_patient("bob_iso")
        self.bob_entry = _log(self.bob, 140)

    def test_alice_list_excludes_bobs_entries(self):
        _log(self.alice, 100)
        self.client.force_login(self.alice)
        resp = self.client.get("/api/v1/logs")
        data = loads(resp.content)
        items = data["items"]
        ids = [e["id"] for e in items]
        self.assertNotIn(self.bob_entry.id, ids)
        self.assertEqual(len(items), 1)

    def test_alice_cannot_fetch_bobs_entry(self):
        self.client.force_login(self.alice)
        resp = self.client.get(f"/api/v1/logs/{self.bob_entry.id}")
        self.assertEqual(resp.status_code, 404)

    def test_alice_cannot_delete_bobs_entry(self):
        self.client.force_login(self.alice)
        resp = self.client.delete(f"/api/v1/logs/{self.bob_entry.id}")
        self.assertEqual(resp.status_code, 404)
        self.assertTrue(LogEntry.objects.filter(id=self.bob_entry.id).exists())

    def test_bobs_log_invisible_to_alice_summary(self):
        """The summary KPIs must be scoped to the requesting patient only."""
        self.client.force_login(self.alice)
        resp = self.client.post(
            "/api/v1/ai/summary",
            data={"days": 30},
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        data = loads(resp.content)
        # Alice has 0 logs — log_count must be 0 even though Bob has 1
        self.assertEqual(data["kpis"]["log_count"], 0)


# ─────────────────────────────────────────────────────────────────────────────
# 4. Offline sync batch — idempotency via client_uuid
# ─────────────────────────────────────────────────────────────────────────────

class BatchSyncTests(TestCase):

    def setUp(self):
        self.user = _make_patient("sync_user")
        self.client.force_login(self.user)

    def test_batch_creates_entries(self):
        payload = [
            {"blood_sugar": 110, "client_uuid": "11111111-1111-1111-1111-111111111111"},
            {"blood_sugar": 130, "client_uuid": "22222222-2222-2222-2222-222222222222"},
        ]
        resp = self.client.post(
            "/api/v1/logs/batch",
            data=payload,
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        data = loads(resp.content)
        self.assertEqual(len(data["synced_ids"]), 2)
        self.assertEqual(LogEntry.objects.filter(patient=self.user).count(), 2)

    def test_batch_is_idempotent(self):
        uuid = "33333333-3333-3333-3333-333333333333"
        payload = [{"blood_sugar": 120, "client_uuid": uuid}]
        self.client.post("/api/v1/logs/batch", data=payload, content_type="application/json")
        self.client.post("/api/v1/logs/batch", data=payload, content_type="application/json")
        self.assertEqual(LogEntry.objects.filter(client_uuid=uuid).count(), 1)

    def test_batch_missing_uuid_returns_error(self):
        payload = [{"blood_sugar": 120}]
        resp = self.client.post(
            "/api/v1/logs/batch",
            data=payload,
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        data = loads(resp.content)
        self.assertTrue(len(data["errors"]) > 0)


# ─────────────────────────────────────────────────────────────────────────────
# 5. Profile API
# ─────────────────────────────────────────────────────────────────────────────

class ProfileAPITests(TestCase):

    def setUp(self):
        self.user = _make_patient("profile_user")
        self.client.force_login(self.user)

    def test_get_profile_returns_correct_fields(self):
        resp = self.client.get("/api/v1/profile")
        self.assertEqual(resp.status_code, 200)
        data = loads(resp.content)
        self.assertEqual(data["diabetes_type"], "type2")
        self.assertEqual(data["treatment_type"], "oral_meds")
        self.assertIn("target_range_low", data)
        self.assertIn("target_range_high", data)

    def test_profile_scoped_to_authenticated_user(self):
        other = _make_patient("other_profile")
        other_dp = other.base_profile.diabetes_profile
        other_dp.diabetes_type = "type1"
        other_dp.save()

        self.client.force_login(self.user)
        resp = self.client.get("/api/v1/profile")
        data = loads(resp.content)
        self.assertEqual(data["diabetes_type"], "type2")


# ─────────────────────────────────────────────────────────────────────────────
# 6. Demo endpoint
# ─────────────────────────────────────────────────────────────────────────────

class DemoEndpointTests(TestCase):

    def test_scenarios_list_has_eight_entries(self):
        resp = self.client.get("/api/v1/demo/scenarios")
        self.assertEqual(resp.status_code, 200)
        data = loads(resp.content)
        self.assertEqual(len(data), 8)

    def test_each_scenario_has_required_keys(self):
        resp = self.client.get("/api/v1/demo/scenarios")
        data = loads(resp.content)
        for scenario in data:
            with self.subTest(scenario=scenario.get("id")):
                self.assertIn("id", scenario)
                self.assertIn("name", scenario)
                self.assertIn("description", scenario)


# ─────────────────────────────────────────────────────────────────────────────
# 7. Firebase auth endpoint
# ─────────────────────────────────────────────────────────────────────────────

class FirebaseAuthEndpointTests(TestCase):

    def test_new_user_is_created(self):
        with patch("firebase_admin.auth.verify_id_token",
                   return_value={"uid": "uid-ninja-new", "email": "newuser@ninja.com"}):
            resp = self.client.post(
                "/api/v1/auth/firebase",
                data={"id_token": "valid-jwt"},
                content_type="application/json",
            )
        self.assertEqual(resp.status_code, 200)
        data = loads(resp.content)
        self.assertEqual(data["user"]["email"], "newuser@ninja.com")
        self.assertIn("message", data)

    def test_existing_user_is_returned(self):
        User.objects.create_user(username="existingninja", email="existing@ninja.com")
        with patch("firebase_admin.auth.verify_id_token",
                   return_value={"uid": "uid-ninja-existing", "email": "existing@ninja.com"}):
            resp = self.client.post(
                "/api/v1/auth/firebase",
                data={"id_token": "valid-jwt"},
                content_type="application/json",
            )
        self.assertEqual(resp.status_code, 200)
        # Must not duplicate the user
        self.assertEqual(User.objects.filter(email="existing@ninja.com").count(), 1)
