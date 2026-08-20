"""
RGPD account endpoints — Art. 7 (consent) + Art. 17 (erasure).

Endpoints under test:
  GET    /api/v1/account/consent
  POST   /api/v1/account/consent
  DELETE /api/v1/account/consent
  DELETE /api/v1/account
"""
from datetime import date
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from core.models import BasePatientProfile
from diabetes.models import AuditLog, DiabetesProfile


def _make_user(username: str) -> User:
    user = User.objects.create_user(username=username, email=f"{username}@test.com")
    base = BasePatientProfile.objects.create(
        patient=user,
        date_of_birth=date(1990, 3, 15),
    )
    DiabetesProfile.objects.create(
        base_profile=base,
        diabetes_type="type1",
        treatment_type="insulin",
    )
    return user


# ── GET /api/v1/account/consent ───────────────────────────────────────────────

class GetConsentStatusTest(TestCase):

    def setUp(self):
        self.user = _make_user("consent_get")
        self.client.force_login(self.user)

    def test_no_consent_returns_false(self):
        resp = self.client.get("/api/v1/account/consent")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertFalse(data["ai_consent_given"])
        self.assertIsNone(data["ai_consent_given_at"])

    def test_with_consent_returns_true(self):
        base = BasePatientProfile.objects.get(patient=self.user)
        base.ai_consent_given_at = timezone.now()
        base.save(update_fields=["ai_consent_given_at"])

        resp = self.client.get("/api/v1/account/consent")
        data = resp.json()
        self.assertTrue(data["ai_consent_given"])
        self.assertIsNotNone(data["ai_consent_given_at"])

    def test_no_profile_returns_false_gracefully(self):
        """User with no BasePatientProfile at all → {ai_consent_given: false}."""
        bare_user = User.objects.create_user(username="bare_consent", email="bare@test.com")
        self.client.force_login(bare_user)
        resp = self.client.get("/api/v1/account/consent")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertFalse(data["ai_consent_given"])

    def test_unauthenticated_request_rejected(self):
        self.client.logout()
        resp = self.client.get("/api/v1/account/consent")
        self.assertIn(resp.status_code, [401, 403])


# ── POST /api/v1/account/consent ──────────────────────────────────────────────

class GiveConsentTest(TestCase):

    def setUp(self):
        self.user = _make_user("consent_post")
        self.client.force_login(self.user)

    def test_post_sets_consent_timestamp(self):
        resp = self.client.post("/api/v1/account/consent", content_type="application/json")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["ai_consent_given"])
        self.assertIsNotNone(data["ai_consent_given_at"])

    def test_post_persists_to_db(self):
        self.client.post("/api/v1/account/consent", content_type="application/json")
        base = BasePatientProfile.objects.get(patient=self.user)
        self.assertIsNotNone(base.ai_consent_given_at)

    def test_post_is_idempotent(self):
        """Second POST must not reset the existing timestamp."""
        self.client.post("/api/v1/account/consent", content_type="application/json")
        base_after_first = BasePatientProfile.objects.get(patient=self.user)
        ts_first = base_after_first.ai_consent_given_at

        self.client.post("/api/v1/account/consent", content_type="application/json")
        base_after_second = BasePatientProfile.objects.get(patient=self.user)
        # Timestamp must be unchanged
        self.assertEqual(base_after_second.ai_consent_given_at, ts_first)

    def test_post_creates_audit_log(self):
        self.client.post("/api/v1/account/consent", content_type="application/json")
        self.assertTrue(
            AuditLog.objects.filter(patient=self.user, action="consent_given").exists()
        )


# ── DELETE /api/v1/account/consent ────────────────────────────────────────────

class WithdrawConsentTest(TestCase):

    def setUp(self):
        self.user = _make_user("consent_delete")
        self.client.force_login(self.user)
        # Pre-grant consent
        base = BasePatientProfile.objects.get(patient=self.user)
        base.ai_consent_given_at = timezone.now()
        base.save(update_fields=["ai_consent_given_at"])

    def test_delete_clears_consent(self):
        resp = self.client.delete("/api/v1/account/consent")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertFalse(data["ai_consent_given"])
        self.assertIsNone(data["ai_consent_given_at"])

    def test_delete_persists_to_db(self):
        self.client.delete("/api/v1/account/consent")
        base = BasePatientProfile.objects.get(patient=self.user)
        self.assertIsNone(base.ai_consent_given_at)

    def test_delete_creates_audit_log(self):
        self.client.delete("/api/v1/account/consent")
        self.assertTrue(
            AuditLog.objects.filter(patient=self.user, action="consent_withdrawn").exists()
        )

    def test_delete_without_consent_is_safe(self):
        """DELETE when no consent exists must not crash (idempotent)."""
        base = BasePatientProfile.objects.get(patient=self.user)
        base.ai_consent_given_at = None
        base.save(update_fields=["ai_consent_given_at"])

        resp = self.client.delete("/api/v1/account/consent")
        self.assertEqual(resp.status_code, 200)


# ── DELETE /api/v1/account ────────────────────────────────────────────────────

class DeleteAccountTest(TestCase):

    def setUp(self):
        self.user = _make_user("erasure_user")
        self.client.force_login(self.user)
        self.pending_purge_patcher = patch(
            "media.documents.pending_cache.purge_patient_pending_extractions",
            return_value=0,
        )
        self.pending_purge = self.pending_purge_patcher.start()
        self.addCleanup(self.pending_purge_patcher.stop)

    def test_wrong_confirm_returns_400(self):
        resp = self.client.delete(
            "/api/v1/account",
            data='{"confirm": "WRONG"}',
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)
        # User must still exist
        self.assertTrue(User.objects.filter(username="erasure_user").exists())

    def test_correct_confirm_deletes_user(self):
        user_id = self.user.id
        resp = self.client.delete(
            "/api/v1/account",
            data='{"confirm": "DELETE MY ACCOUNT"}',
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(User.objects.filter(id=user_id).exists())

    def test_correct_confirm_cascades_log_entries(self):
        from diabetes.models import LogEntry
        LogEntry.objects.create(patient=self.user, blood_sugar=120, logged_at=timezone.now())

        self.client.delete(
            "/api/v1/account",
            data='{"confirm": "DELETE MY ACCOUNT"}',
            content_type="application/json",
        )
        # CASCADE must have removed the log entry
        self.assertEqual(LogEntry.objects.filter(patient_id=self.user.id).count(), 0)

    def test_correct_confirm_cascades_retained_lab_report_raw_text(self):
        from diabetes.models import LabReport

        patient_id = self.user.id
        LabReport.objects.create(
            patient=self.user,
            document_type="lab_report",
            source_format="pdf",
            raw_text="SYNTHETIC_RETAINED_RAW_TEXT",
        )

        resp = self.client.delete(
            "/api/v1/account",
            data='{"confirm": "DELETE MY ACCOUNT"}',
            content_type="application/json",
        )

        self.assertEqual(resp.status_code, 200)
        self.assertFalse(LabReport.objects.filter(patient_id=patient_id).exists())

    def test_pending_cache_failure_blocks_erasure_and_preserves_raw_text(self):
        from diabetes.models import LabReport

        patient_id = self.user.id
        LabReport.objects.create(
            patient=self.user,
            document_type="lab_report",
            source_format="pdf",
            raw_text="SYNTHETIC_RETAINED_RAW_TEXT",
        )
        self.pending_purge.side_effect = RuntimeError("redis unavailable")

        resp = self.client.delete(
            "/api/v1/account",
            data='{"confirm": "DELETE MY ACCOUNT"}',
            content_type="application/json",
        )

        self.assertEqual(resp.status_code, 500)
        self.assertTrue(User.objects.filter(id=patient_id).exists())
        self.assertTrue(
            LabReport.objects.filter(
                patient_id=patient_id,
                raw_text="SYNTHETIC_RETAINED_RAW_TEXT",
            ).exists()
        )

    def test_audit_log_preserved_after_erasure(self):
        """AuditLog uses SET_NULL — rows must survive user deletion."""
        self.client.delete(
            "/api/v1/account",
            data='{"confirm": "DELETE MY ACCOUNT"}',
            content_type="application/json",
        )
        # At minimum the account_deleted event must exist with patient=NULL
        self.assertTrue(
            AuditLog.objects.filter(patient=None, action="account_deleted").exists()
        )

    def test_unauthenticated_erasure_rejected(self):
        self.client.logout()
        resp = self.client.delete(
            "/api/v1/account",
            data='{"confirm": "DELETE MY ACCOUNT"}',
            content_type="application/json",
        )
        self.assertIn(resp.status_code, [401, 403])
