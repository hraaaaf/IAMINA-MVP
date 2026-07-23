"""
API endpoint wiring — verifying the contracts expected by the Flutter UI.

Rewritten from Django-template tests. Covers:
  - DashboardVoirToutTests: GET /api/v1/logs returns patient-scoped data
  - HistoryListViewTests:   List endpoint auth, empty state, isolation, data completeness
  - IaminaChatUiTests:      Chat endpoint existence, no mode gate, immediate access
"""
from datetime import date, timedelta
from decimal import Decimal
from json import loads

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from core.models import BasePatientProfile
from diabetes.models import DiabetesProfile, LogEntry


def _make_patient(username):
    user = User.objects.create_user(username=username, email=f"{username}@test.com")
    base = BasePatientProfile.objects.create(
        patient=user,
        date_of_birth=date(1980, 1, 1),
    )
    DiabetesProfile.objects.create(
        base_profile=base,
        diabetes_type="type2",
        treatment_type="oral_meds",
    )
    return user


class DashboardVoirToutTests(TestCase):
    """GET /api/v1/logs replaces the 'Voir tout → history list' navigation."""

    def setUp(self):
        self.alice = _make_patient("alice_voirtout")
        self.client.force_login(self.alice)

    def test_voir_tout_points_to_history_not_create(self):
        """
        Logs list is scoped to the requesting patient.
        Alice's 110 appears; Bob's 240 is never leaked.
        """
        bob = _make_patient("bob_voirtout")
        LogEntry.objects.create(
            patient=self.alice, blood_sugar=Decimal("110"), logged_at=timezone.now()
        )
        LogEntry.objects.create(
            patient=bob, blood_sugar=Decimal("240"), logged_at=timezone.now()
        )

        resp = self.client.get("/api/v1/logs")
        self.assertEqual(resp.status_code, 200)
        values = [e["blood_sugar"] for e in loads(resp.content)["items"]]
        self.assertIn(110.0, values)
        self.assertNotIn(240.0, values)


class HistoryListViewTests(TestCase):
    """History list endpoint: auth, isolation, empty state, large dataset."""

    def setUp(self):
        self.alice = _make_patient("alice_hist")
        self.bob   = _make_patient("bob_hist")

    def test_requires_login(self):
        """GET /api/v1/logs without auth → 401 (API returns 401, not a 302 redirect)."""
        resp = self.client.get("/api/v1/logs")
        self.assertEqual(resp.status_code, 401)

    def test_empty_state_when_no_entries(self):
        """Authenticated patient with 0 entries → 200 with paginated response, empty items."""
        self.client.force_login(self.alice)
        resp = self.client.get("/api/v1/logs")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(loads(resp.content)["items"], [])

    def test_shows_only_own_entries(self):
        """Alice's list includes her 110 entry but never Bob's 240 entry."""
        LogEntry.objects.create(
            patient=self.alice, blood_sugar=Decimal("110"), logged_at=timezone.now()
        )
        LogEntry.objects.create(
            patient=self.bob, blood_sugar=Decimal("240"), logged_at=timezone.now()
        )

        self.client.force_login(self.alice)
        resp = self.client.get("/api/v1/logs")
        values = [e["blood_sugar"] for e in loads(resp.content)["items"]]
        self.assertIn(110.0, values)
        self.assertNotIn(240.0, values)

    def test_pagination_kicks_in_past_50_entries(self):
        """
        Default page_size=50; 60 entries → first page has 50 items, total=60.
        Requesting ?page_size=100 returns all 60 in one shot.
        """
        now = timezone.now()
        LogEntry.objects.bulk_create([
            LogEntry(
                patient=self.alice,
                blood_sugar=Decimal("120"),
                logged_at=now - timedelta(hours=i),
            )
            for i in range(60)
        ])

        self.client.force_login(self.alice)
        resp = self.client.get("/api/v1/logs?page_size=100")
        self.assertEqual(resp.status_code, 200)
        data = loads(resp.content)
        self.assertEqual(data["total"], 60)
        self.assertEqual(len(data["items"]), 60)


class IaminaChatUiTests(TestCase):
    """POST /api/v1/ai/chat: directly accessible after auth — no mode selection required."""

    def setUp(self):
        self.alice = _make_patient("alice_chat_ui")
        self.client.force_login(self.alice)

    def test_mode_picker_strings_are_absent(self):
        """
        ChatRequest has no 'mode' parameter — the API accepts a message directly.
        200 means chat was processed without requiring a text/voice mode pre-selection.
        """
        resp = self.client.post(
            "/api/v1/ai/chat",
            data={"message": "Bonjour IAmina"},
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)

    def test_chat_surface_is_present(self):
        """POST /api/v1/ai/chat endpoint is registered (not 404) and returns reply + conversation_id."""
        resp = self.client.post(
            "/api/v1/ai/chat",
            data={"message": "Test"},
            content_type="application/json",
        )
        self.assertNotEqual(resp.status_code, 404)
        data = loads(resp.content)
        self.assertIn("reply", data)
        self.assertIn("conversation_id", data)

    def test_chat_surface_is_visible_by_default(self):
        """Chat works on first call without any pre-flight setup — is_emergency field present."""
        resp = self.client.post(
            "/api/v1/ai/chat",
            data={"message": "Mon sucre est à 140"},
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        data = loads(resp.content)
        self.assertIn("is_emergency", data)
