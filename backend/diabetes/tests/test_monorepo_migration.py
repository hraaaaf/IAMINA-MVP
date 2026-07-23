"""
Monorepo migration integration tests — Ninja API.

Rewritten from Django-template tests (template views and AISummary model removed).
Verifies the core integration points work correctly via the Ninja API:
  - Patient data access via /api/v1/logs
  - Log creation and IAmina insights
  - JSON-only responses (no Django template HTML in API output)
  - Log entry creation replaces the old Django form
"""
import datetime
from json import loads

from django.contrib.auth.models import User
from django.test import TransactionTestCase

from core.models import BasePatientProfile
from diabetes.models import DiabetesProfile, LogEntry


class MonorepoMigrationTests(TransactionTestCase):
    """
    Consolidated integration tests for the monorepo (Flutter + Django Ninja) architecture.
    Uses TransactionTestCase for maximum database isolation.
    """

    def create_user_and_profile(self, username):
        user = User.objects.create_user(
            username=username,
            password="password123",
            email=f"{username}@test.com",
        )
        base = BasePatientProfile.objects.create(
            patient=user,
            date_of_birth=datetime.date(1990, 1, 1),
        )
        profile = DiabetesProfile.objects.create(
            base_profile=base,
            diabetes_type="type2",
            treatment_type="oral_meds",
            target_range_low=70,
            target_range_high=130,
        )
        return user, profile

    def test_dashboard_loads(self):
        """
        GET /api/v1/logs is the primary dashboard data endpoint.
        Returns 200 with a paginated JSON object {total, page, page_size, items}.
        """
        user, _ = self.create_user_and_profile("user_dashboard2")
        self.client.force_login(user)
        resp = self.client.get("/api/v1/logs")
        self.assertEqual(resp.status_code, 200)
        data = loads(resp.content)
        self.assertIsInstance(data, dict)
        self.assertIn("items", data)
        self.assertIsInstance(data["items"], list)

    def test_i_amina_activated_with_enough_logs(self):
        """
        Summary endpoint returns insights + kpis when patient has log entries.
        (Replaces the Django template + AISummary model check.)
        """
        user, _ = self.create_user_and_profile("user_amina2")
        self.client.force_login(user)

        for i in range(5):
            LogEntry.objects.create(patient=user, blood_sugar=110 + i)

        resp = self.client.post(
            "/api/v1/ai/summary",
            data={"days": 30},
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        data = loads(resp.content)
        self.assertIn("insights", data)
        self.assertIn("kpis", data)
        self.assertGreater(data["kpis"]["log_count"], 0)

    def test_base_template_integrated(self):
        """
        API responses are JSON — no Django template ('themeApp') in response body.
        Confirms the monorepo split: Flutter owns the UI, Django owns the data.
        """
        user, _ = self.create_user_and_profile("user_base2")
        self.client.force_login(user)
        resp = self.client.get("/api/v1/profile")
        self.assertEqual(resp.status_code, 200)
        data = loads(resp.content)
        self.assertIn("diabetes_type", data)
        self.assertNotIn("themeApp", resp.content.decode())

    def test_log_entry_form_loads(self):
        """
        POST /api/v1/logs creates a new entry (replaces the Django 'Nouvelle entrée' form).
        Returns 200 with the persisted entry including an assigned id.
        """
        user, _ = self.create_user_and_profile("user_form2")
        self.client.force_login(user)
        resp = self.client.post(
            "/api/v1/logs",
            data={"blood_sugar": 130, "meal_type": "lunch"},
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        data = loads(resp.content)
        self.assertIn("id", data)
        self.assertEqual(data["blood_sugar"], 130.0)
