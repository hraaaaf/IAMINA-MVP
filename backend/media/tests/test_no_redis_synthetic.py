"""W01 no-Redis synthetic-only gate; fail-closed document import and safe erasure."""
from datetime import date
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase, override_settings

from core.models import BasePatientProfile
from core.models.erasure_record import ErasureRecord
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
