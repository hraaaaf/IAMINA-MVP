"""W01 no-Redis synthetic-only gate; fail-closed document import and safe erasure."""
from datetime import date
from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase, override_settings

from core.models import BasePatientProfile
from core.models.erasure_record import ErasureRecord
from diabetes.api.v1.documents import confirm_import, ingest_document
from media.documents.pending_cache import purge_patient_pending_extractions


@override_settings(IAMINA_NO_REDIS=True)
class SyntheticNoRedisErasureTest(TestCase):
    def test_pending_purge_cannot_access_redis(self):
        with patch(
            "media.documents.pending_cache.get_redis_connection",
            side_effect=AssertionError("Redis accessed"),
        ):
            self.assertEqual(purge_patient_pending_extractions(17), 0)

    def test_normal_account_delete_succeeds_without_redis(self):
        user = User.objects.create_user(username="w01-no-redis", email="w01-no-redis@example.invalid")
        BasePatientProfile.objects.create(patient=user, date_of_birth=date(1990, 3, 15))
        patient_id = user.id
        self.client.force_login(user)
        with patch(
            "media.documents.pending_cache.get_redis_connection",
            side_effect=AssertionError("Redis accessed"),
        ):
            response = self.client.delete(
                "/api/v1/account",
                data='{"confirm":"DELETE MY ACCOUNT"}',
                content_type="application/json",
            )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(pk=patient_id).exists())
        self.assertTrue(ErasureRecord.objects.filter(patient_id_snapshot=patient_id).exists())


@override_settings(IAMINA_NO_REDIS=True)
class SyntheticNoRedisPulperDisabledTest(TestCase):
    def test_ingest_never_reads_file_or_stages_extracts_or_calls_ai(self):
        class NoReadUpload:
            name = "synthetic.pdf"
            content_type = "application/pdf"
            size = 8

            def read(self, *args, **kwargs):
                raise AssertionError("Disabled document ingestion read upload bytes")

        request = SimpleNamespace(auth=SimpleNamespace(id=17))
        with (
            patch("diabetes.api.v1.documents._read_upload_with_limit",
                  side_effect=AssertionError("read guard reached")),
            patch("diabetes.api.v1.documents.ingest",
                  side_effect=AssertionError("extractor reached")),
            patch("diabetes.api.v1.documents.cache.set",
                  side_effect=AssertionError("cache write reached")),
            patch("diabetes.api.v1.documents._do_persist",
                  side_effect=AssertionError("clinical persistence reached")),
        ):
            status, payload = ingest_document.__wrapped__(
                request, NoReadUpload(), confirm=False,
            )
        self.assertEqual(status, 503)
        self.assertIn("indisponible", payload["detail"])
        self.assertNotIn("batch_id", payload)

    def test_confirm_never_consumes_cache_or_persists(self):
        request = SimpleNamespace(auth=SimpleNamespace(id=17))
        with (
            patch("diabetes.api.v1.documents._consume_pending_batch_once",
                  side_effect=AssertionError("cache consume reached")),
            patch("diabetes.api.v1.documents._do_persist",
                  side_effect=AssertionError("clinical persistence reached")),
        ):
            response = confirm_import(request, "synthetic-nonexistent-batch")
        self.assertFalse(response.ok)
        self.assertIsNone(response.lab_report_id)
        self.assertEqual(response.glucose_readings_saved, 0)
        self.assertEqual(response.glucose_duplicates, 0)
        self.assertTrue(response.errors)
