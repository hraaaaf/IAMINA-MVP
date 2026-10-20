"""D2 preview preference contract: synthetic patient A/B and opt-out tests."""

import json

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.utils import timezone

from core.consent_notice import expected_notice_claim
from core.d2_preview_notice import expected_d2_notice
from core.models import BasePatientProfile, D2PreviewConsentReceipt

PATH = "/api/v1/account/notification-preview-consent"


def grant_current_ai_consent(user, locale="fr"):
    """Seed only current exact global consent, without unrelated test imports."""
    notice = expected_notice_claim(locale)
    return BasePatientProfile.objects.update_or_create(
        patient=user,
        defaults={
            "ai_consent_given_at": timezone.now(),
            "ai_consent_notice_version": notice.version,
            "ai_consent_notice_hash": notice.notice_hash,
            "ai_consent_notice_locale": notice.locale,
        },
    )[0]


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

    def test_same_browser_session_switch_a_b_a_keeps_receipts_separated(self):
        """Server-side A -> B -> A scope, not Web vault isolation certification."""
        grant_current_ai_consent(self.a)
        grant_current_ai_consent(self.b)
        self.client.force_login(self.a)
        self.assertEqual(self._grant().status_code, 200)

        self.client.force_login(self.b)
        self.assertFalse(self.client.get(PATH).json()["opted_in"])
        self.assertEqual(self._grant("en").status_code, 200)
        self.assertTrue(self.client.get(PATH).json()["opted_in"])
        self.assertFalse(self.client.delete(PATH).json()["opted_in"])

        self.client.force_login(self.a)
        self.assertTrue(self.client.get(PATH).json()["opted_in"])
        self.assertEqual(
            D2PreviewConsentReceipt.objects.filter(
                patient=self.a, revoked_at__isnull=True,
            ).count(), 1,
        )
        self.assertEqual(
            D2PreviewConsentReceipt.objects.filter(
                patient=self.b, revoked_at__isnull=True,
            ).count(), 0,
        )

    def test_mixed_cookie_and_bearer_cannot_bypass_d2_consent_csrf(self):
        """A forged Bearer cannot turn an authenticated cookie into CSRF bypass."""
        grant_current_ai_consent(self.a)
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.a)
        client.cookies["csrftoken"] = "a" * 32
        notice = expected_d2_notice("fr")
        body = json.dumps({
            "locale": "fr",
            "notice_version": notice.version,
            "notice_hash": notice.notice_hash,
            "acknowledgment": "ENABLE_PREVIEW_ONLY",
        })
        headers = {
            "HTTP_AUTHORIZATION": "Bearer forged",
            "HTTP_X_CSRFTOKEN": "a" * 32,
        }
        response = client.put(
            PATH, data=body, content_type="application/json", **headers,
        )
        self.assertIn(response.status_code, (401, 403))
        self.assertFalse(D2PreviewConsentReceipt.objects.exists())

        # On an already consented session, mixed credentials cannot revoke.
        session_client = Client(enforce_csrf_checks=True)
        session_client.force_login(self.a)
        session_client.cookies["csrftoken"] = "a" * 32
        accepted = session_client.put(
            PATH, data=body, content_type="application/json",
            HTTP_X_CSRFTOKEN="a" * 32,
        )
        self.assertEqual(accepted.status_code, 200)
        self.assertEqual(
            session_client.delete(PATH, **headers).status_code, 403,
        )
        self.assertEqual(
            D2PreviewConsentReceipt.objects.filter(
                patient=self.a, revoked_at__isnull=True,
            ).count(), 1,
        )

    def test_cookie_session_mutations_enforce_csrf_token_and_origin(self):
        """A legitimate same-session cookie cannot opt in via forged cross-site POST."""
        grant_current_ai_consent(self.a)
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.a)
        notice = expected_d2_notice("fr")
        body = json.dumps({
            "locale": "fr",
            "notice_version": notice.version,
            "notice_hash": notice.notice_hash,
            "acknowledgment": "ENABLE_PREVIEW_ONLY",
        })
        params = {"data": body, "content_type": "application/json"}

        self.assertEqual(client.put(PATH, **params).status_code, 403)
        self.assertFalse(D2PreviewConsentReceipt.objects.exists())

        # Valid token but unrelated Vercel account origin is still rejected.
        client.cookies["csrftoken"] = "a" * 32
        self.assertEqual(
            client.put(
                PATH, **params,
                HTTP_X_CSRFTOKEN="a" * 32,
                HTTP_ORIGIN="https://unrelated-app.vercel.app",
            ).status_code, 403,
        )
        self.assertFalse(D2PreviewConsentReceipt.objects.exists())

        # No cross-site Origin; matching Django CSRF cookie/header is accepted.
        self.assertEqual(
            client.put(PATH, **params, HTTP_X_CSRFTOKEN="a" * 32).status_code,
            200,
        )
        self.assertTrue(client.get(PATH).json()["opted_in"])

        # Withdrawal is itself protected against CSRF.
        self.assertEqual(client.delete(PATH).status_code, 403)
        self.assertTrue(client.get(PATH).json()["opted_in"])
        self.assertEqual(
            client.delete(PATH, HTTP_X_CSRFTOKEN="a" * 32).status_code,
            200,
        )
        self.assertFalse(client.get(PATH).json()["opted_in"])
