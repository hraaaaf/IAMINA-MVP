"""Contract tests for demo/application runtime parity."""

from unittest.mock import patch

from django.test import Client, TestCase
from django.utils import timezone

from core.companion.clinical import get_domain_context
from diabetes.models import LogEntry
from diabetes.services.demo_patient import get_or_create_synthetic_demo_patient


class DemoChatContractTests(TestCase):
    def setUp(self):
        self.client = Client()

    def _post(self, message: str, language: str = "fr", history=None, remote_addr="127.0.0.1"):
        return self.client.post(
            "/api/v1/demo/chat",
            data={
                "message": message,
                "language": language,
                "history": history or [],
            },
            content_type="application/json",
            REMOTE_ADDR=remote_addr,
        )

    @patch("companion.demo_runtime.IAmina")
    def test_demo_uses_application_runtime_with_synthetic_logs(self, iamina_cls):
        iamina_cls.return_value.chat.return_value = "Réponse issue du runtime IAmina."

        response = self._post("Comment était mon diabète cette semaine ?")

        self.assertEqual(response.status_code, 200)
        patient = iamina_cls.call_args.args[0]
        self.assertTrue(patient.username.startswith("demo_runtime_"))
        self.assertTrue(patient.has_usable_password() is False)
        self.assertGreater(LogEntry.objects.filter(patient=patient).count(), 20)
        iamina_cls.return_value.chat.assert_called_once_with(
            "Comment était mon diabète cette semaine ?",
            context_days=14,
        )
        self.assertEqual(response.json()["reply"], "Réponse issue du runtime IAmina.")

    def test_synthetic_demo_context_is_clinically_analyzable(self):
        patient = get_or_create_synthetic_demo_patient("contract-subject")

        context = get_domain_context(patient.id, language="fr", days=7)

        self.assertTrue(context.has_sufficient_data)
        self.assertEqual(context.analysis_status, "complete")
        self.assertTrue(context.kpi_summary)
        self.assertIn("tir_pct", context.kpi_summary)

    @patch("companion.demo_runtime.IAmina")
    def test_personal_weekly_request_is_not_forced_to_no_patient_record(self, iamina_cls):
        iamina_cls.return_value.chat.return_value = (
            "Sur les 7 derniers jours, tes données synthétiques sont disponibles."
        )

        response = self._post("Comment était mon diabète cette semaine ?")

        self.assertEqual(response.status_code, 200)
        reply = response.json()["reply"].lower()
        self.assertIn("7 derniers jours", reply)
        self.assertNotIn("aucun dossier patient", reply)
        self.assertNotIn("mode démo", reply)

    @patch("companion.demo_runtime.IAmina")
    def test_demo_subject_is_stable_per_remote_address(self, iamina_cls):
        iamina_cls.return_value.chat.return_value = "ok"

        first = self._post("Bonjour", remote_addr="198.51.100.10")
        first_patient = iamina_cls.call_args.args[0]
        second = self._post("Encore", remote_addr="198.51.100.10")
        second_patient = iamina_cls.call_args.args[0]

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(first_patient.id, second_patient.id)
        self.assertNotIn("198.51.100.10", first_patient.username)

    @patch("companion.demo_runtime.IAmina")
    def test_demo_subject_isolated_between_remote_addresses(self, iamina_cls):
        iamina_cls.return_value.chat.return_value = "ok"

        self._post("Bonjour", remote_addr="198.51.100.11")
        first_patient = iamina_cls.call_args.args[0]
        self._post("Bonjour", remote_addr="198.51.100.12")
        second_patient = iamina_cls.call_args.args[0]

        self.assertNotEqual(first_patient.id, second_patient.id)

    @patch("companion.demo_runtime.IAmina")
    def test_urgent_content_stays_deterministic_before_llm_runtime(self, iamina_cls):
        response = self._post(
            "sokkar 45 w kan7ess brassi mdowekh bzaf, chno ndir daba?"
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["is_emergency"])
        self.assertEqual(payload["conversation_id"], "TRIAGE_VITAL")
        self.assertEqual(payload["reply_language"], "ar-MA")
        iamina_cls.assert_not_called()

    @patch("companion.demo_runtime.IAmina")
    def test_dose_request_stays_deterministic_before_llm_runtime(self, iamina_cls):
        response = self._post("Combien d'unités d'insuline dois-je prendre ?")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertFalse(payload["is_emergency"])
        self.assertIn("Je ne peux pas prescrire", payload["reply"])
        iamina_cls.assert_not_called()

    def test_demo_chat_rejects_history_above_bounded_limits(self):
        too_many = [
            {"role": "user" if index % 2 == 0 else "assistant", "content": "x"}
            for index in range(22)
        ]
        too_large = [
            {"role": "user", "content": "a" * 4000},
            {"role": "assistant", "content": "b" * 3000},
        ]

        self.assertEqual(self._post("hello", history=too_many).status_code, 400)
        self.assertEqual(self._post("hello", history=too_large).status_code, 400)

    def test_demo_chat_rejects_empty_or_oversized_messages(self):
        self.assertEqual(self._post("   ").status_code, 400)
        self.assertEqual(self._post("x" * 1001).status_code, 400)

    def test_demo_chat_rate_limits_anonymous_ingress(self):
        from core.models import AIUserThrottleWindow

        fixed_now = timezone.now()
        payload = {
            "reply": "Réponse démo.",
            "conversation_id": "conv-demo-test",
            "timestamp": fixed_now.isoformat(),
            "is_emergency": False,
            "reply_language": "fr",
        }
        with (
            patch("diabetes.api.v1.demo.timezone.now", return_value=fixed_now),
            patch(
                "diabetes.api.v1.demo.reply_with_synthetic_patient",
                return_value=payload,
            ),
        ):
            for _ in range(10):
                response = self._post("question libre")
                self.assertEqual(response.status_code, 200)
            blocked = self._post("encore")

        self.assertEqual(blocked.status_code, 429)
        subject_rows = AIUserThrottleWindow.objects.filter(
            subject_key__startswith="demo:"
        )
        self.assertEqual(subject_rows.count(), 1)
        self.assertEqual(subject_rows.get().request_count, 10)
