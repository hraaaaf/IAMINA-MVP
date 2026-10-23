"""W01-G5: synthetic-only Preview erasure without configured Redis.

Proves that Production, real patients, configured Redis, or clinical records
retain the existing fail-closed account-deletion behavior.
"""
from __future__ import annotations

import os
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from redis.exceptions import ConnectionError as RedisConnectionError

from core.models import BasePatientProfile
from diabetes.apps import _purge_pending_documents
from diabetes.models import LabReport, LogEntry
from diabetes.synthetic_preview_erasure import can_erase_synthetic_without_cache

PREVIEW = {
    "VERCEL": "1",
    "VERCEL_ENV": "preview",
    "IAMINA_ENV": "development",
    "VERCEL_PROJECT_ID": "prj_Pn9FnyconF3h2w9gOU74iV98kJoU",
    "IAMINA_EXPECTED_DB_HOST": "ep-old-art-b9sy0oo4.c-7.eu-central-1.aws.neon.tech",
    "IAMINA_EXPECTED_DB_NAME": "iamina925_empty",
    "IAMINA_EXPECTED_DB_ROLE": "iamina_preview_app",
}
EMAIL = "w01g5-bff-0123456789abcdef0123@example.invalid"


class W01SyntheticPreviewErasureTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username=EMAIL, email=EMAIL, password="test-only",
            first_name="Synthetic", last_name="W01-A",
        )
        BasePatientProfile.objects.create(patient=self.user)

    def _preview(self, *, overrides=None):
        values = dict(PREVIEW)
        values.update(overrides or {})
        return patch.dict(os.environ, values, clear=True)

    def test_eligible_only_with_exact_verified_synthetic_scope(self):
        with self._preview():
            self.assertTrue(can_erase_synthetic_without_cache(self.user.id, ""))
            for name, wrong in (
                ("VERCEL_ENV", "production"),
                ("IAMINA_ENV", "production"),
                ("VERCEL_PROJECT_ID", "prj_other"),
                ("IAMINA_EXPECTED_DB_HOST", "ep-other.example.test"),
                ("IAMINA_EXPECTED_DB_NAME", "patient_prod"),
                ("IAMINA_EXPECTED_DB_ROLE", "neondb_owner"),
            ):
                with self.subTest(name=name):
                    self.assertFalse(can_erase_synthetic_without_cache(
                        self.user.id, "", {**PREVIEW, name: wrong}
                    ))
            self.assertFalse(can_erase_synthetic_without_cache(
                self.user.id, "", {**PREVIEW, "REDIS_URL": "redis://localhost:6379/0"}
            ))
            self.assertFalse(can_erase_synthetic_without_cache(self.user.id, "firebase-id"))
            self.assertFalse(can_erase_synthetic_without_cache(0, ""))
            self.assertFalse(can_erase_synthetic_without_cache(999999, ""))

    def test_only_exact_generated_email_and_names_are_eligible(self):
        with self._preview():
            self.user.email = "real-patient@example.com"
            self.user.save(update_fields=["email"])
            self.assertFalse(can_erase_synthetic_without_cache(self.user.id, ""))
            self.user.email = EMAIL
            self.user.first_name = "Not synthetic"
            self.user.save(update_fields=["email", "first_name"])
            self.assertFalse(can_erase_synthetic_without_cache(self.user.id, ""))

    def test_clinical_or_log_records_prevent_cache_bypass(self):
        with self._preview():
            LabReport.objects.create(
                patient=self.user, document_type="lab_report",
                source_format="pdf", raw_text="test-only",
            )
            self.assertFalse(can_erase_synthetic_without_cache(self.user.id, ""))
            LabReport.objects.filter(patient=self.user).delete()
            from django.utils import timezone

            log = LogEntry.objects.create(
                patient=self.user, blood_sugar=120, logged_at=timezone.now(),
            )
            self.assertFalse(can_erase_synthetic_without_cache(self.user.id, ""))
            log.delete()

    def test_connection_error_allowed_for_synthetic_preview_only(self):
        with self._preview(), patch(
            "media.documents.pending_cache.purge_patient_pending_extractions",
            side_effect=RedisConnectionError("connection refused"),
        ):
            _purge_pending_documents(self.user.id, "")

    def test_configured_redis_and_production_stay_fail_closed(self):
        for change in (
            {"REDIS_URL": "redis://localhost:6379/0"},
            {"VERCEL_ENV": "production"},
            {"IAMINA_EXPECTED_DB_NAME": "other_database"},
        ):
            with self.subTest(change=change), self._preview(overrides=change), patch(
                "media.documents.pending_cache.purge_patient_pending_extractions",
                side_effect=RedisConnectionError("connection refused"),
            ):
                with self.assertRaises(RedisConnectionError):
                    _purge_pending_documents(self.user.id, "")

    def test_unexpected_cache_error_always_fails_closed(self):
        with self._preview(), patch(
            "media.documents.pending_cache.purge_patient_pending_extractions",
            side_effect=RuntimeError("unexpected cache failure"),
        ):
            with self.assertRaises(RuntimeError):
                _purge_pending_documents(self.user.id, "")

    def test_http_account_deletion_succeeds_only_for_synthetic_redisless_preview(self):
        user_id = self.user.pk
        self.client.force_login(self.user)
        with self._preview(), patch(
            "media.documents.pending_cache.purge_patient_pending_extractions",
            side_effect=RedisConnectionError("connection refused"),
        ):
            response = self.client.delete(
                "/api/v1/account",
                data='{"confirm":"DELETE MY ACCOUNT"}',
                content_type="application/json",
            )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(pk=user_id).exists())

    def test_http_account_deletion_stays_blocked_when_redis_is_configured(self):
        user_id = self.user.pk
        self.client.force_login(self.user)
        with self._preview(overrides={"REDIS_URL": "redis://localhost:6379/0"}), patch(
            "media.documents.pending_cache.purge_patient_pending_extractions",
            side_effect=RedisConnectionError("connection refused"),
        ):
            response = self.client.delete(
                "/api/v1/account",
                data='{"confirm":"DELETE MY ACCOUNT"}',
                content_type="application/json",
            )
        self.assertEqual(response.status_code, 500)
        self.assertTrue(User.objects.filter(pk=user_id).exists())
