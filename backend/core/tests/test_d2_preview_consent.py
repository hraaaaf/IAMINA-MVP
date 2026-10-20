"""D2 preview preference contract: synthetic patient A/B and opt-out tests."""

import json

from django.contrib.auth.models import User
from django.test import Client, TestCase

from core.d2_preview_notice import expected_d2_notice
from core.models import D2PreviewConsentReceipt

from core.tests.consent_helpers import grant_current_ai_consent


PATH = "/api/v1/account/notification-preview-consent"


class D2PreviewConsentTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.a = User.objects.create_user(username="d2-preview-a")
        self.b = User.objects.create_user(username="d2-preview-b")

    def _grant(self, locale="fr", **overrides):
        notice = expected_d2_notice(locale)
        body = {
            "locale": locale,
            "notice_version": notice.version,
            "notice_hash": notice.notice_hash,
            "acknowledgment": "ENABLE_PREVIEW_ONLY",
        }
        body.update(overrides)
        return self.client.put(
            PATH, data=json.dumps(body), content_type="application/json"
        )

    def test_anonymous_actions_do_not_read_or_write_receipts(self):
        notice = expected_d2_notice("fr")
        for verb, kw in (
            ("get", {}),
            ("put", {"data": json.dumps({
                "locale": "fr", "notice_version": notice.version,
                "notice_hash": notice.notice_hash,
                "acknowledgment": "ENABLE_PREVIEW_ONLY",
            }), "content_type": "application/json"}),
            ("delete", {}),
        ):
            response = getattr(self.client, verb)(PATH, **kw)
            self.assertIn(response.status_code, (401, 403))
        self.assertEqual(D2PreviewConsentReceipt.objects.count(), 0)

    def test_default_off_and_explicit_global_consent_required(self):
        self.client.force_login(self.a)
        self.assertEqual(self._grant().status_code, 409)
        grant_current_ai_consent(self.a)
        status = self.client.get(PATH).json()
        self.assertEqual(status["purpose"], "proactive_in_app_preview")
        self.assertFalse(status["opted_in"])
        self.assertFalse(status["browser_push_enabled"])
        self.assertFalse(status["delivery_enabled"])
        self.assertEqual(D2PreviewConsentReceipt.objects.count(), 0)

    def test_invalid_claim_and_forged_payload_rejected(self):
        grant_current_ai_consent(self.a)
        self.client.force_login(self.a)
        for kwargs in (
            {"notice_version": "expired"},
            {"notice_hash": "0" * 64},
            {"acknowledgment": "ENABLE_PUSH"},
            {"patient_id": self.b.id},
        ):
            with self.subTest(kwargs=kwargs):
                self.assertIn(self._grant(**kwargs).status_code, (400, 422))
        self.assertEqual(self.client.get(PATH + "?locale=xx").status_code, 422)
        self.assertFalse(D2PreviewConsentReceipt.objects.exists())

    def test_idempotent_patient_isolation_and_no_push(self):
        grant_current_ai_consent(self.a)
        self.client.force_login(self.a)
        for _ in range(2):
            result = self._grant()
            self.assertEqual(result.status_code, 200)
            payload = result.json()
            self.assertTrue(payload["opted_in"])
            self.assertFalse(payload["delivery_enabled"])
            self.assertFalse(payload["browser_push_enabled"])
        self.assertEqual(D2PreviewConsentReceipt.objects.filter(patient=self.a).count(), 1)
        self.client.force_login(self.b)
        self.assertFalse(self.client.get(PATH + f"?patient_id={self.a.id}").json()["opted_in"])
        self.assertFalse(self.client.delete(PATH).json()["opted_in"])
        self.assertTrue(D2PreviewConsentReceipt.objects.filter(
            patient=self.a, revoked_at__isnull=True
        ).exists())

    def test_revoke_idempotent_and_regrant_requires_new_receipt(self):
        grant_current_ai_consent(self.a)
        self.client.force_login(self.a)
        self.assertEqual(self._grant().status_code, 200)
        self.assertFalse(self.client.delete(PATH).json()["opted_in"])
        self.assertFalse(self.client.delete(PATH).json()["opted_in"])
        self.assertEqual(D2PreviewConsentReceipt.objects.filter(
            patient=self.a, revoked_at__isnull=True
        ).count(), 0)
        self.assertEqual(self._grant().status_code, 200)
        self.assertEqual(D2PreviewConsentReceipt.objects.filter(patient=self.a).count(), 2)

    def test_global_ai_withdraw_and_reconsent_never_reactivates_d2(self):
        grant_current_ai_consent(self.a)
        self.client.force_login(self.a)
        self.assertEqual(self._grant().status_code, 200)
        self.assertEqual(self.client.delete("/api/v1/account/consent").status_code, 200)
        self.assertFalse(self.client.get(PATH).json()["opted_in"])
        self.assertEqual(D2PreviewConsentReceipt.objects.filter(
            patient=self.a, revoked_at__isnull=True
        ).count(), 0)
        grant_current_ai_consent(self.a)
        self.assertFalse(self.client.get(PATH).json()["opted_in"])
        self.assertEqual(self._grant().status_code, 200)
        self.assertEqual(D2PreviewConsentReceipt.objects.filter(patient=self.a).count(), 2)

    def test_localization_and_cross_locale_status(self):
        grant_current_ai_consent(self.a, locale="ar-MA")
        self.client.force_login(self.a)
        self.assertEqual(self._grant("ar-MA").status_code, 200)
        self.assertEqual(expected_d2_notice("ar-MA").notice_hash,
                         expected_d2_notice("ar").notice_hash)
        for locale in ("fr", "en", "ar", "ar-MA"):
            with self.subTest(locale=locale):
                status = self.client.get(PATH + f"?locale={locale}").json()
                self.assertTrue(status["opted_in"])
                self.assertFalse(status["browser_push_enabled"])
