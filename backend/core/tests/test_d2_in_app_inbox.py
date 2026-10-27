"""D2 synthetic inbox contract: no delivery, owner scope, consent, CSRF."""
import json
from datetime import timedelta

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.utils import timezone

from core.consent_notice import expected_notice_claim
from core.d2_preview_notice import expected_d2_notice
from core.models import BasePatientProfile, D2PreviewConsentReceipt, D2InAppNotice
from diabetes.models.entry import LogEntry
from diabetes.services.clinical.observation_memory import refresh_personal_response_memory

PATH = "/api/v1/account/notification-inbox"


class D2InboxTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.a = User.objects.create_user(username="d2-inbox-a")
        self.b = User.objects.create_user(username="d2-inbox-b")
        self.now = timezone.now()

    def _grant(self, patient):
        global_claim = expected_notice_claim("fr")
        d2_claim = expected_d2_notice("fr")
        base, _ = BasePatientProfile.objects.update_or_create(
            patient=patient,
            defaults={
                "ai_consent_given_at": timezone.now(),
                "ai_consent_notice_version": global_claim.version,
                "ai_consent_notice_hash": global_claim.notice_hash,
                "ai_consent_notice_locale": global_claim.locale,
            },
        )
        D2PreviewConsentReceipt.objects.create(
            patient=patient,
            notice_version=d2_claim.version,
            notice_hash=d2_claim.notice_hash,
            notice_locale=d2_claim.locale,
            global_consent_epoch=base.ai_consent_given_at,
            granted_at=timezone.now(),
        )

    def _seed(self, patient):
        for day, glucose in enumerate((150, 160, 170)):
            LogEntry.objects.create(
                patient=patient,
                logged_at=self.now - timedelta(days=day),
                blood_sugar=glucose,
                source="manual",
                stressed="yes",
            )
        LogEntry.objects.create(
            patient=patient,
            logged_at=self.now - timedelta(days=3),
            blood_sugar=110,
            source="manual",
        )
        refresh_personal_response_memory(patient_id=patient.pk)

    def _save(self, **overrides):
        body = {"acknowledgment": "SAVE_GOVERNED_PREVIEW"}
        body.update(overrides)
        return self.client.post(
            PATH + "/save", data=json.dumps(body), content_type="application/json",
        )

    def test_anonymous_and_unconsented_read_and_write_fail_closed(self):
        for method, url in (
            ("get", PATH),
            ("post", PATH + "/save"),
            ("put", PATH + "/1/read"),
            ("delete", PATH + "/1"),
        ):
            response = getattr(self.client, method)(url)
            self.assertIn(response.status_code, (401, 403))
        self.client.force_login(self.a)
        self.assertEqual(self.client.get(PATH).status_code, 409)
        self.assertEqual(self._save().status_code, 409)
        self.assertFalse(D2InAppNotice.objects.exists())

    def test_explicit_saved_governed_item_is_persisted_bounded_and_idempotent(self):
        self._grant(self.a)
        self._seed(self.a)
        self.client.force_login(self.a)
        empty = self.client.get(PATH)
        self.assertEqual(empty.status_code, 200)
        self.assertFalse(empty.json()["delivery_enabled"])
        self.assertEqual(empty.json()["items"], [])
        first = self._save()
        self.assertEqual(first.status_code, 200)
        self.assertTrue(first.json()["created"])
        self.assertFalse(first.json()["delivery_enabled"])
        self.assertIn(first.json()["item"]["kind"], ("context", "meal"))
        self.assertNotIn("blood_sugar", first.content.decode())
        self.assertNotIn("evidence_id", first.content.decode())
        again = self._save()
        self.assertEqual(again.status_code, 200)
        self.assertFalse(again.json()["created"])
        self.assertEqual(D2InAppNotice.objects.filter(patient=self.a).count(), 1)

        notice_id = first.json()["item"]["id"]
        read = self.client.put(f"{PATH}/{notice_id}/read")
        self.assertEqual(read.status_code, 200)
        self.assertTrue(read.json()["updated"])
        replay = self.client.put(f"{PATH}/{notice_id}/read")
        self.assertEqual(replay.status_code, 200)
        self.assertFalse(replay.json()["updated"])
        self.assertEqual(self.client.delete(f"{PATH}/{notice_id}").status_code, 200)
        self.assertFalse(D2InAppNotice.objects.exists())
        self.assertEqual(self.client.delete(f"{PATH}/{notice_id}").status_code, 404)

    def test_cross_patient_access_and_forged_patient_id_are_rejected(self):
        self._grant(self.a)
        self._grant(self.b)
        self._seed(self.a)
        self.client.force_login(self.a)
        result = self._save()
        self.assertEqual(result.status_code, 200)
        notice_id = result.json()["item"]["id"]
        self.client.force_login(self.b)
        self.assertEqual(self.client.get(PATH).json()["items"], [])
        self.assertEqual(self.client.put(f"{PATH}/{notice_id}/read").status_code, 404)
        self.assertEqual(self.client.delete(f"{PATH}/{notice_id}").status_code, 404)
        self.assertIn(self._save(patient_id=self.a.pk).status_code, (400, 422))
        self.assertTrue(D2InAppNotice.objects.filter(patient=self.a).exists())
        self.assertEqual(self._save().status_code, 409)

    def test_expired_items_hidden_and_preview_revocation_purges(self):
        self._grant(self.a)
        self._seed(self.a)
        self.client.force_login(self.a)
        self.assertEqual(self._save().status_code, 200)
        D2InAppNotice.objects.filter(patient=self.a).update(
            expires_at=timezone.now() - timedelta(seconds=1)
        )
        self.assertEqual(self.client.get(PATH).json()["items"], [])
        self.assertEqual(self._save().status_code, 200)
        self.assertEqual(D2InAppNotice.objects.filter(patient=self.a).count(), 1)
        self.assertEqual(
            self.client.delete("/api/v1/account/notification-preview-consent").status_code,
            200,
        )
        self.assertFalse(D2InAppNotice.objects.filter(patient=self.a).exists())
        self.assertEqual(self.client.get(PATH).status_code, 409)

    def test_global_ai_withdrawal_purges_inbox(self):
        self._grant(self.a)
        self._seed(self.a)
        self.client.force_login(self.a)
        self.assertEqual(self._save().status_code, 200)
        self.assertEqual(self.client.delete("/api/v1/account/consent").status_code, 200)
        self.assertFalse(D2InAppNotice.objects.exists())
        self.assertEqual(self.client.get(PATH).status_code, 409)

    def test_forged_cookie_and_bearer_cannot_save_read_or_delete(self):
        self._grant(self.a)
        self._seed(self.a)
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.force_login(self.a)
        body = json.dumps({"acknowledgment": "SAVE_GOVERNED_PREVIEW"})
        self.assertEqual(csrf_client.post(
            PATH + "/save", data=body, content_type="application/json",
        ).status_code, 403)
        self.assertFalse(D2InAppNotice.objects.exists())
        csrf_client.cookies["csrftoken"] = "a" * 32
        created = csrf_client.post(
            PATH + "/save", data=body, content_type="application/json",
            HTTP_X_CSRFTOKEN="a" * 32,
        )
        self.assertEqual(created.status_code, 200)
        pk = created.json()["item"]["id"]
        self.assertIn(csrf_client.put(f"{PATH}/{pk}/read", HTTP_AUTHORIZATION="Bearer forged").status_code, (401, 403))
        self.assertIn(csrf_client.delete(f"{PATH}/{pk}", HTTP_AUTHORIZATION="Bearer forged").status_code, (401, 403))
        self.assertIsNone(D2InAppNotice.objects.get(pk=pk).read_at)
        self.assertEqual(D2InAppNotice.objects.count(), 1)
