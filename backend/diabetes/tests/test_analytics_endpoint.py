"""
Tests for GET /api/v1/analytics/overview — staff-only retention dashboard.

Test cases per plan RFC-003:
  E1 — non-staff authenticated user → 403 Forbidden
  E2 — staff user, any DB state → 200 + all 6 top-level JSON keys present
  E3 — staff user, no observability events → 200 + cohort_size=0 + retention.d1=null
"""
from django.contrib.auth import get_user_model
from django.test import TestCase

from core.observability.events import ObservabilityEvent

User = get_user_model()

ANALYTICS_URL = "/api/v1/analytics/overview"


class E1NonStaffForbiddenTest(TestCase):
    """Authenticated non-staff user receives 403."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="regular_user",
            password="pass1234",
            is_staff=False,
        )

    def test_non_staff_forbidden(self):
        self.client.force_login(self.user)
        resp = self.client.get(ANALYTICS_URL)
        self.assertEqual(resp.status_code, 403)


class E2StaffReturns200AndShapeTest(TestCase):
    """Staff user receives 200 with the expected JSON shape."""

    def setUp(self):
        self.staff = User.objects.create_user(
            username="staff_user",
            password="pass1234",
            is_staff=True,
        )

    def test_staff_returns_200(self):
        self.client.force_login(self.staff)
        resp = self.client.get(ANALYTICS_URL)
        self.assertEqual(resp.status_code, 200)

    def test_staff_response_has_all_top_level_keys(self):
        self.client.force_login(self.staff)
        resp = self.client.get(ANALYTICS_URL)
        data = resp.json()

        expected_keys = {
            "retention",
            "cohort_ready",
            "funnel",
            "companion_engagement",
            "cohort_size",
            "computed_at",
        }
        self.assertEqual(set(data.keys()), expected_keys)

    def test_retention_has_d1_d7_d30_d90_keys(self):
        self.client.force_login(self.staff)
        resp = self.client.get(ANALYTICS_URL)
        retention = resp.json()["retention"]
        self.assertIn("d1",  retention)
        self.assertIn("d7",  retention)
        self.assertIn("d30", retention)
        self.assertIn("d90", retention)

    def test_funnel_has_four_keys(self):
        self.client.force_login(self.staff)
        resp = self.client.get(ANALYTICS_URL)
        funnel = resp.json()["funnel"]
        self.assertIn("session_start",  funnel)
        self.assertIn("log_created",    funnel)
        self.assertIn("chat_message",   funnel)
        self.assertIn("summary_viewed", funnel)

    def test_cohort_ready_has_d1_d7_d30_d90_keys(self):
        self.client.force_login(self.staff)
        resp = self.client.get(ANALYTICS_URL)
        cohort_ready = resp.json()["cohort_ready"]
        self.assertIn("d1",  cohort_ready)
        self.assertIn("d7",  cohort_ready)
        self.assertIn("d30", cohort_ready)
        self.assertIn("d90", cohort_ready)

    def test_companion_engagement_has_expected_key(self):
        self.client.force_login(self.staff)
        resp = self.client.get(ANALYTICS_URL)
        engagement = resp.json()["companion_engagement"]
        self.assertIn("chat_per_active_patient", engagement)


class E3EmptyDbReturnsZeroCohortTest(TestCase):
    """
    Staff user with no observability events in DB.
    cohort_size must be 0 and retention.d1 must be null.
    """

    def setUp(self):
        self.staff = User.objects.create_user(
            username="staff_empty",
            password="pass1234",
            is_staff=True,
        )
        # Ensure no observability events exist
        ObservabilityEvent.objects.all().delete()

    def test_empty_db_returns_200(self):
        self.client.force_login(self.staff)
        resp = self.client.get(ANALYTICS_URL)
        self.assertEqual(resp.status_code, 200)

    def test_empty_db_cohort_size_zero(self):
        self.client.force_login(self.staff)
        resp = self.client.get(ANALYTICS_URL)
        data = resp.json()
        self.assertEqual(data["cohort_size"], 0)

    def test_empty_db_retention_d1_null(self):
        self.client.force_login(self.staff)
        resp = self.client.get(ANALYTICS_URL)
        data = resp.json()
        self.assertIsNone(data["retention"]["d1"])

    def test_empty_db_all_retention_null(self):
        self.client.force_login(self.staff)
        resp = self.client.get(ANALYTICS_URL)
        retention = resp.json()["retention"]
        self.assertIsNone(retention["d1"])
        self.assertIsNone(retention["d7"])
        self.assertIsNone(retention["d30"])
        self.assertIsNone(retention["d90"])

    def test_empty_db_all_cohort_ready_false(self):
        self.client.force_login(self.staff)
        resp = self.client.get(ANALYTICS_URL)
        cohort_ready = resp.json()["cohort_ready"]
        self.assertFalse(cohort_ready["d1"])
        self.assertFalse(cohort_ready["d7"])
        self.assertFalse(cohort_ready["d30"])
        self.assertFalse(cohort_ready["d90"])

    def test_empty_db_funnel_all_zero(self):
        self.client.force_login(self.staff)
        resp = self.client.get(ANALYTICS_URL)
        funnel = resp.json()["funnel"]
        self.assertEqual(funnel["session_start"],  0)
        self.assertEqual(funnel["log_created"],    0)
        self.assertEqual(funnel["chat_message"],   0)
        self.assertEqual(funnel["summary_viewed"], 0)
