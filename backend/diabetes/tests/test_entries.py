"""
LogEntry CRUD + patient isolation — Ninja API.

Rewritten from Django-view tests. Covers:
  - CRUD operations via /api/v1/logs/* endpoints
  - Blood-sugar range validation enforced at the API boundary (ge=30, le=600 mg/dL)
  - Patient isolation: Alice never sees, edits, or deletes Bob's data.
"""
from datetime import date
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
        date_of_birth=date(1985, 6, 15),
    )
    DiabetesProfile.objects.create(
        base_profile=base,
        diabetes_type="type2",
        treatment_type="oral_meds",
    )
    return user


class LogEntryCRUDTests(TestCase):

    def setUp(self):
        self.alice = _make_patient("alice_entries")
        self.client.force_login(self.alice)

    def test_create_entry_persists_and_redirects(self):
        """POST /api/v1/logs → 200, entry persisted, blood_sugar echoed back."""
        resp = self.client.post(
            "/api/v1/logs",
            data={"blood_sugar": 120, "meal_type": "lunch"},
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        data = loads(resp.content)
        self.assertEqual(data["blood_sugar"], 120.0)
        self.assertTrue(
            LogEntry.objects.filter(patient=self.alice, blood_sugar=120).exists()
        )

    def test_blood_sugar_below_30_rejected(self):
        """blood_sugar=25 is below the API minimum (30 mg/dL) → 422, no entry saved."""
        resp = self.client.post(
            "/api/v1/logs",
            data={"blood_sugar": 25},
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 422)
        self.assertEqual(LogEntry.objects.filter(patient=self.alice).count(), 0)

    def test_blood_sugar_above_600_rejected(self):
        """blood_sugar=700 exceeds the API maximum (600 mg/dL) → 422, no entry saved."""
        resp = self.client.post(
            "/api/v1/logs",
            data={"blood_sugar": 700},
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 422)
        self.assertEqual(LogEntry.objects.filter(patient=self.alice).count(), 0)

    def test_edit_entry_updates_value(self):
        """PATCH /api/v1/logs/{id} → 200, blood_sugar updated in DB."""
        entry = LogEntry.objects.create(
            patient=self.alice,
            blood_sugar=Decimal("100"),
            logged_at=timezone.now(),
        )
        resp = self.client.patch(
            f"/api/v1/logs/{entry.id}",
            data={"blood_sugar": 155},
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(loads(resp.content)["blood_sugar"], 155.0)
        entry.refresh_from_db()
        self.assertEqual(entry.blood_sugar, Decimal("155"))

    def test_delete_entry_removes_row(self):
        """DELETE /api/v1/logs/{id} → 204 No Content, row gone from DB."""
        entry = LogEntry.objects.create(
            patient=self.alice,
            blood_sugar=Decimal("100"),
            logged_at=timezone.now(),
        )
        resp = self.client.delete(f"/api/v1/logs/{entry.id}")
        self.assertEqual(resp.status_code, 204)
        self.assertFalse(LogEntry.objects.filter(id=entry.id).exists())


class LogListPaginationTests(TestCase):
    """GET /logs returns paginated JSON: {total, page, page_size, items}."""

    def setUp(self):
        self.alice = _make_patient("alice_pag")
        self.client.force_login(self.alice)
        for i in range(5):
            LogEntry.objects.create(
                patient=self.alice,
                blood_sugar=Decimal(str(100 + i)),
                logged_at=timezone.now(),
            )

    def test_default_returns_all_items_and_metadata(self):
        resp = self.client.get("/api/v1/logs")
        self.assertEqual(resp.status_code, 200)
        data = loads(resp.content)
        self.assertEqual(data["total"], 5)
        self.assertEqual(data["page"], 1)
        self.assertEqual(len(data["items"]), 5)

    def test_page_size_limits_items(self):
        resp = self.client.get("/api/v1/logs?page=1&page_size=2")
        self.assertEqual(resp.status_code, 200)
        data = loads(resp.content)
        self.assertEqual(data["total"], 5)
        self.assertEqual(data["page_size"], 2)
        self.assertEqual(len(data["items"]), 2)

    def test_second_page_returns_remaining_items(self):
        resp = self.client.get("/api/v1/logs?page=2&page_size=2")
        data = loads(resp.content)
        self.assertEqual(len(data["items"]), 2)

    def test_page_beyond_total_returns_empty_items(self):
        resp = self.client.get("/api/v1/logs?page=99&page_size=10")
        data = loads(resp.content)
        self.assertEqual(data["total"], 5)
        self.assertEqual(len(data["items"]), 0)

    def test_page_size_clamped_to_200(self):
        resp = self.client.get("/api/v1/logs?page_size=999")
        data = loads(resp.content)
        self.assertLessEqual(data["page_size"], 200)


class PatientIsolationTests(TestCase):
    """Patient A must never view, edit, or delete patient B's data."""

    def setUp(self):
        self.alice = _make_patient("alice_iso2")
        self.bob   = _make_patient("bob_iso2")
        self.bob_entry = LogEntry.objects.create(
            patient=self.bob,
            blood_sugar=Decimal("140"),
            logged_at=timezone.now(),
        )

    def test_alice_cannot_view_bobs_confirmation(self):
        """GET /api/v1/logs/{bob_entry_id} as Alice → 404."""
        self.client.force_login(self.alice)
        resp = self.client.get(f"/api/v1/logs/{self.bob_entry.id}")
        self.assertEqual(resp.status_code, 404)

    def test_alice_cannot_edit_bobs_entry(self):
        """PATCH /api/v1/logs/{bob_entry_id} as Alice → 404, blood_sugar unchanged."""
        self.client.force_login(self.alice)
        resp = self.client.patch(
            f"/api/v1/logs/{self.bob_entry.id}",
            data={"blood_sugar": 99},
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 404)
        self.bob_entry.refresh_from_db()
        self.assertEqual(self.bob_entry.blood_sugar, Decimal("140"))

    def test_alice_cannot_delete_bobs_entry(self):
        """DELETE /api/v1/logs/{bob_entry_id} as Alice → 404, entry still in DB."""
        self.client.force_login(self.alice)
        resp = self.client.delete(f"/api/v1/logs/{self.bob_entry.id}")
        self.assertEqual(resp.status_code, 404)
        self.assertTrue(LogEntry.objects.filter(id=self.bob_entry.id).exists())
