"""Contract tests for the public, stateless IAMINA demo conversation."""

from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import Client, TestCase

from diabetes.models import LogEntry


class DemoChatContractTests(TestCase):
    def setUp(self):
        self.client = Client()

    def _post(self, message: str, language: str = "fr"):
        return self.client.post(
            "/api/v1/demo/chat",
            data={"message": message, "language": language},
            content_type="application/json",
        )

    def test_demo_chat_is_public_and_stateless_with_bounded_narrator(self):
        with patch(
            "companion.demo.generate_demo_reply",
            return_value="Je t'ai compris. Tu dis que tu as des vertiges. Depuis quand ?",
        ) as narrator:
            response = self._post("fia doukha")

        narrator.assert_called_once_with("fia doukha", "fr")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["conversation_id"], "demo-governed")
        self.assertFalse(payload["is_emergency"])
        self.assertEqual(payload["reply_language"], "fr")
        self.assertTrue(payload["reply"])
        self.assertEqual(User.objects.count(), 0)
        self.assertEqual(LogEntry.objects.count(), 0)

    def test_demo_chat_does_not_call_model_for_dose_boundary(self):
        with patch(
            "companion.demo.generate_demo_reply",
            side_effect=AssertionError("dose boundary must stay deterministic"),
        ):
            response = self._post("Combien d'unités d'insuline dois-je prendre ?")
        self.assertEqual(response.status_code, 200)

    def test_demo_chat_keeps_dose_requests_inside_no_prescription_boundary(self):
        response = self._post("Combien d'unités d'insuline dois-je prendre ?")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertFalse(payload["is_emergency"])
        self.assertIn("Je ne peux pas prescrire", payload["reply"])

    def test_demo_chat_rate_limits_anonymous_ingress(self):
        with patch("companion.demo.generate_demo_reply", return_value="Réponse démo."):
            for _ in range(10):
                response = self._post("question libre")
                self.assertEqual(response.status_code, 200)
            blocked = self._post("encore")
        self.assertEqual(blocked.status_code, 429)

    def test_demo_chat_reuses_canonical_emergency_boundary_without_patient(self):
        response = self._post("Je veux mourir")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["is_emergency"])
        self.assertEqual(payload["conversation_id"], "TRIAGE_CRISIS")
        self.assertTrue(payload["reply"])

    def test_demo_chat_supports_arabic_without_patient_profile(self):
        response = self._post("مرحبا", language="ar")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["reply_language"], "ar")
        self.assertEqual(payload["conversation_id"], "demo-governed")
        self.assertTrue(payload["reply"])

    def test_demo_chat_rejects_empty_or_oversized_messages(self):
        empty = self._post("   ")
        oversized = self._post("x" * 1001)

        self.assertEqual(empty.status_code, 400)
        self.assertEqual(oversized.status_code, 400)
