"""Integration tests for IAmina API v1 endpoints."""

from datetime import date
from json import loads
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.utils import timezone

from core.models import BasePatientProfile
from diabetes.models import DiabetesProfile, LogEntry


def _mock_firebase(uid="test-uid-123", email=None):
    """Context manager: patches verify_id_token to return a fake decoded token."""
    return patch(
        "firebase_admin.auth.verify_id_token",
        return_value={"uid": uid, "email": email or f"{uid}@ex.com"},
    )


def create_patient(username, email):
    """Helper to create a user with a complete patient profile."""
    user = User.objects.create_user(username=username, email=email)
    base = BasePatientProfile.objects.create(
        patient=user,
        date_of_birth=date(1980, 1, 1),
    )
    DiabetesProfile.objects.create(
        base_profile=base,
        diabetes_type='type2',
        treatment_type='oral_meds',
    )
    return user


class APIAuthTestCase(TestCase):
    def setUp(self):
        self.client = Client()

    def test_firebase_auth_new_user(self):
        with _mock_firebase(uid="uid-new", email="new@ex.com"):
            response = self.client.post(
                "/api/v1/auth/firebase",
                data={"id_token": "valid-jwt", "email": "ignored@ex.com"},
                content_type="application/json",
            )
        self.assertEqual(response.status_code, 200)
        # User created with firebase uid, not the email field from request
        self.assertTrue(User.objects.filter(email="new@ex.com").exists())

    def test_firebase_auth_existing_user(self):
        create_patient("existing", "existing@ex.com")
        with _mock_firebase(uid="uid-existing", email="existing@ex.com"):
            response = self.client.post(
                "/api/v1/auth/firebase",
                data={"id_token": "valid-jwt"},
                content_type="application/json",
            )
        self.assertEqual(response.status_code, 200)

    def test_firebase_auth_invalid_token_returns_401(self):
        """Invalid/expired JWT must be rejected — not silently accepted."""
        with patch("firebase_admin.auth.verify_id_token", side_effect=Exception("token expired")):
            response = self.client.post(
                "/api/v1/auth/firebase",
                data={"id_token": "bad-token"},
                content_type="application/json",
            )
        self.assertEqual(response.status_code, 401)


class APIDemoTestCase(TestCase):
    def test_demo_scenarios(self):
        response = self.client.get("/api/v1/demo/scenarios")
        self.assertEqual(response.status_code, 200)
        data = loads(response.content)
        self.assertEqual(len(data), 8)


class APISummaryTestCase(TestCase):
    def setUp(self):
        self.user = create_patient("p1", "p1@ex.com")
        self.patient = self.user.base_profile.diabetes_profile
        self.client = Client()

    def test_summary_requires_auth(self):
        resp = self.client.post("/api/v1/ai/summary", data={"days": 21}, content_type="application/json")
        self.assertEqual(resp.status_code, 401)

    def test_summary_with_auth(self):
        self.client.force_login(self.user)
        LogEntry.objects.create(patient=self.user, blood_sugar=180, logged_at=timezone.now())
        resp = self.client.post("/api/v1/ai/summary", data={"days": 21}, content_type="application/json")
        self.assertEqual(resp.status_code, 200)


class APIChatTestCase(TestCase):
    def setUp(self):
        self.user = create_patient("p2", "p2@ex.com")
        self.patient = self.user.base_profile.diabetes_profile
        self.client = Client()

    def test_chat_requires_auth(self):
        resp = self.client.post("/api/v1/ai/chat", data={"message": "Hi"}, content_type="application/json")
        self.assertEqual(resp.status_code, 401)

    def test_chat_with_auth(self):
        self.client.force_login(self.user)
        resp = self.client.post("/api/v1/ai/chat", data={"message": "Hi"}, content_type="application/json")
        self.assertEqual(resp.status_code, 200)


class APILogsTestCase(TestCase):
    def setUp(self):
        self.user = create_patient("p3", "p3@ex.com")
        self.patient = self.user.base_profile.diabetes_profile
        self.client = Client()

    def test_logs_require_auth(self):
        resp = self.client.get("/api/v1/logs")
        self.assertEqual(resp.status_code, 401)

    def test_logs_isolation(self):
        user2 = create_patient("p4", "p4@ex.com")
        LogEntry.objects.create(patient=self.user, blood_sugar=100, logged_at=timezone.now())
        LogEntry.objects.create(patient=user2, blood_sugar=200, logged_at=timezone.now())

        self.client.force_login(self.user)
        resp = self.client.get("/api/v1/logs")
        data = loads(resp.content)
        self.assertEqual(len(data["items"]), 1)

    def test_logs_empty_list(self):
        self.client.force_login(self.user)
        resp = self.client.get("/api/v1/logs")
        self.assertEqual(resp.status_code, 200)
        data = loads(resp.content)
        self.assertEqual(len(data["items"]), 0)

    def test_logs_create(self):
        self.client.force_login(self.user)
        resp = self.client.post(
            "/api/v1/logs",
            data={"blood_sugar": 150, "meal_type": "lunch"},
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        data = loads(resp.content)
        self.assertEqual(data["blood_sugar"], 150)

    def test_logs_get_single(self):
        self.client.force_login(self.user)
        log = LogEntry.objects.create(patient=self.user, blood_sugar=160, logged_at=timezone.now())
        resp = self.client.get(f"/api/v1/logs/{log.id}")
        self.assertEqual(resp.status_code, 200)
        data = loads(resp.content)
        self.assertEqual(data["blood_sugar"], 160)

    def test_logs_delete(self):
        self.client.force_login(self.user)
        log = LogEntry.objects.create(patient=self.user, blood_sugar=170, logged_at=timezone.now())
        resp = self.client.delete(f"/api/v1/logs/{log.id}")
        self.assertEqual(resp.status_code, 204)
        self.assertFalse(LogEntry.objects.filter(id=log.id).exists())


class APISummaryEdgeCasesTestCase(TestCase):
    def setUp(self):
        self.user = create_patient("p5", "p5@ex.com")
        self.client = Client()

    def test_summary_no_logs(self):
        self.client.force_login(self.user)
        resp = self.client.post("/api/v1/ai/summary", data={"days": 21}, content_type="application/json")
        self.assertEqual(resp.status_code, 200)
        data = loads(resp.content)
        self.assertIn("insights", data)

    def test_summary_high_glucose(self):
        self.client.force_login(self.user)
        LogEntry.objects.create(patient=self.user, blood_sugar=350, logged_at=timezone.now())
        resp = self.client.post("/api/v1/ai/summary", data={"days": 21}, content_type="application/json")
        self.assertEqual(resp.status_code, 200)
        data = loads(resp.content)
        # High glucose (350 mg/dL > 180 threshold) → TAR% must be > 0
        self.assertGreater(data["kpis"]["tar_pct"], 0)

    def test_summary_low_glucose(self):
        self.client.force_login(self.user)
        LogEntry.objects.create(patient=self.user, blood_sugar=50, logged_at=timezone.now())
        resp = self.client.post("/api/v1/ai/summary", data={"days": 21}, content_type="application/json")
        self.assertEqual(resp.status_code, 200)
        data = loads(resp.content)
        # Low glucose (50 mg/dL < 70 threshold) → TBR% must be > 0
        self.assertGreater(data["kpis"]["tbr_pct"], 0)

    def test_summary_custom_days(self):
        self.client.force_login(self.user)
        LogEntry.objects.create(patient=self.user, blood_sugar=120, logged_at=timezone.now())
        resp = self.client.post("/api/v1/ai/summary", data={"days": 7}, content_type="application/json")
        self.assertEqual(resp.status_code, 200)

    def test_summary_response_structure(self):
        self.client.force_login(self.user)
        resp = self.client.post("/api/v1/ai/summary", data={"days": 21}, content_type="application/json")
        data = loads(resp.content)
        required_fields = ["insights", "kpis", "daily_averages", "generated_at", "has_sufficient_data"]
        for field in required_fields:
            self.assertIn(field, data, f"Missing field: {field}")


class APIChatEdgeCasesTestCase(TestCase):
    def setUp(self):
        self.user = create_patient("p6", "p6@ex.com")
        self.client = Client()

    def _patched_iamina_chat(self, reply):
        """Stub IAmina.chat() — avoids real LLM calls (rate limits, latency)."""
        from unittest.mock import patch
        return patch("companion.core.IAmina.chat", return_value=reply)

    def test_chat_glucose_keyword(self):
        self.client.force_login(self.user)
        with self._patched_iamina_chat("Votre glycémie est stable ce mois-ci."):
            resp = self.client.post(
                "/api/v1/ai/chat",
                data={"message": "What about my glucose?"},
                content_type="application/json",
            )
        self.assertEqual(resp.status_code, 200)
        data = loads(resp.content)
        self.assertIn("glycémie", data["reply"].lower())

    def test_chat_meal_keyword(self):
        self.client.force_login(self.user)
        with self._patched_iamina_chat("Vos repas du soir semblent impacter votre glycémie."):
            resp = self.client.post(
                "/api/v1/ai/chat",
                data={"message": "How should I handle my meals?"},
                content_type="application/json",
            )
        self.assertEqual(resp.status_code, 200)
        data = loads(resp.content)
        self.assertIn("repas", data["reply"].lower())

    def test_chat_generic_message(self):
        self.client.force_login(self.user)
        resp = self.client.post(
            "/api/v1/ai/chat",
            data={"message": "Hello!"},
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        data = loads(resp.content)
        self.assertIn("reply", data)
        self.assertIn("conversation_id", data)
        self.assertIn("timestamp", data)

    def test_chat_response_format(self):
        self.client.force_login(self.user)
        resp = self.client.post(
            "/api/v1/ai/chat",
            data={"message": "Test"},
            content_type="application/json",
        )
        data = loads(resp.content)
        self.assertIn("conversation_id", data)
        self.assertTrue(data["conversation_id"].startswith("conv-"))


class APIAuthEdgeCasesTestCase(TestCase):
    def setUp(self):
        self.client = Client()

    def test_firebase_auth_creates_profile(self):
        with _mock_firebase(uid="uid-newprofile", email="newuser@ex.com"):
            resp = self.client.post(
                "/api/v1/auth/firebase",
                data={"id_token": "valid-jwt"},
                content_type="application/json",
            )
        self.assertEqual(resp.status_code, 200)
        user = User.objects.get(email="newuser@ex.com")
        self.assertTrue(hasattr(user, "base_profile"))
        self.assertEqual(user.base_profile.firebase_uid, "uid-newprofile")

    def test_firebase_auth_response_structure(self):
        with _mock_firebase(uid="uid-struct", email="testuser@ex.com"):
            resp = self.client.post(
                "/api/v1/auth/firebase",
                data={"id_token": "valid-jwt"},
                content_type="application/json",
            )
        data = loads(resp.content)
        self.assertIn("user", data)
        self.assertIn("id", data["user"])
        self.assertIn("email", data["user"])
        self.assertIn("message", data)

    def test_firebase_auth_no_email_in_token(self):
        """Token without email field → user created with uid-based username, empty email."""
        with patch("firebase_admin.auth.verify_id_token",
                   return_value={"uid": "uid-noemail"}):  # no "email" key
            resp = self.client.post(
                "/api/v1/auth/firebase",
                data={"id_token": "valid-jwt"},
                content_type="application/json",
            )
        self.assertEqual(resp.status_code, 200)

    def test_firebase_auth_uid_is_stable_key(self):
        """Same uid + different email → same user (uid is the stable key)."""
        with _mock_firebase(uid="uid-stable", email="v1@ex.com"):
            self.client.post("/api/v1/auth/firebase",
                             data={"id_token": "jwt1"}, content_type="application/json")
        with _mock_firebase(uid="uid-stable", email="v2@ex.com"):
            self.client.post("/api/v1/auth/firebase",
                             data={"id_token": "jwt2"}, content_type="application/json")
        # Only one user for that uid
        self.assertEqual(User.objects.filter(base_profile__firebase_uid="uid-stable").count(), 1)
        # Email synced to latest
        self.assertEqual(User.objects.get(base_profile__firebase_uid="uid-stable").email, "v2@ex.com")


class APIProfileTestCase(TestCase):
    def setUp(self):
        self.user = create_patient("p7", "p7@ex.com")
        self.client = Client()

    def test_profile_requires_auth(self):
        resp = self.client.get("/api/v1/profile")
        self.assertEqual(resp.status_code, 401)

    def test_profile_get(self):
        self.client.force_login(self.user)
        resp = self.client.get("/api/v1/profile")
        self.assertEqual(resp.status_code, 200)
        data = loads(resp.content)
        self.assertIn("diabetes_type", data)


class APIResponseCodesTestCase(TestCase):
    def setUp(self):
        self.client = Client()

    def test_invalid_endpoint_404(self):
        resp = self.client.get("/api/v1/invalid/endpoint")
        self.assertEqual(resp.status_code, 404)
