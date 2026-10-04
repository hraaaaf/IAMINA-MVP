"""Contract tests for demo/application runtime parity."""

from unittest.mock import patch

from django.test import Client, TestCase
from django.utils import timezone

from companion.intent_envelope import (
    Ambiguity,
    BackendIntentDecision,
    IntentEnvelope,
    IntentKind,
    IntentTarget,
    RouteKind,
)
from companion.intent_pipeline import IntentPipelineOutcome
from core.ai_egress import TEXT, assert_ai_egress_allowed
from core.companion.clinical import get_domain_context
from diabetes.models import LogEntry
from diabetes.services.demo_patient import get_or_create_synthetic_demo_patient


class DemoChatContractTests(TestCase):
    def setUp(self):
        self.client = Client()

    def _post(
        self,
        message: str,
        language: str = "fr",
        history=None,
        remote_addr: str = "127.0.0.1",
        session_id: str = "test-session",
    ):
        return self.client.post(
            "/api/v1/demo/chat",
            data={
                "message": message,
                "language": language,
                "session_id": session_id,
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
        self.assertFalse(patient.has_usable_password())
        self.assertGreater(LogEntry.objects.filter(patient=patient).count(), 20)
        iamina_cls.return_value.chat.assert_called_once_with(
            "Comment était mon diabète cette semaine ?",
            context_days=14,
        )
        self.assertEqual(response.json()["reply"], "Réponse issue du runtime IAmina.")

    @patch("companion.demo_runtime.IAmina")
    @patch("diabetes.services.demo_runtime._preview_route_reply")
    def test_intent_preview_local_route_bypasses_patient_runtime(self, preview, iamina_cls):
        preview.return_value = (RouteKind.DETERMINISTIC_LOCAL, "Preview local reply")

        response = self._post("What can you do exactly?")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["reply"], "Preview local reply")
        iamina_cls.assert_not_called()

    @patch("companion.demo_runtime.IAmina")
    @patch("diabetes.services.demo_runtime._preview_route_reply")
    def test_intent_preview_patient_route_keeps_synthetic_runtime(self, preview, iamina_cls):
        preview.return_value = (RouteKind.DETERMINISTIC_PATIENT_DATA, "")
        iamina_cls.return_value.chat.return_value = "Synthetic patient reply"

        response = self._post("Quel est mon TIR cette semaine ?")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["reply"], "Synthetic patient reply")
        iamina_cls.return_value.chat.assert_called_once()


    @patch("diabetes.services.demo_runtime.analyze_unresolved_turn")
    def test_general_tir_education_ignores_negated_personal_data_phrase(self, analyze):
        analyze.return_value = IntentPipelineOutcome(
            decision=BackendIntentDecision(
                route=RouteKind.CONVERSATIONAL,
                target=IntentTarget.NONE,
                reason="validated_conversational_intent",
            ),
            envelope=IntentEnvelope(
                schema_version="1",
                intent=IntentKind.GENERAL_HEALTH_EDUCATION,
                target=IntentTarget.NONE,
                confidence=0.98,
                ambiguity=Ambiguity.NONE,
            ),
            source="intent_envelope_v1",
            fallback_copy_key="",
        )

        response = self._post(
            "Explique-moi le TIR en général, sans regarder mes données."
        )

        self.assertEqual(response.status_code, 200)
        reply = response.json()["reply"]
        self.assertIn("Le TIR (Time in Range)", reply)
        self.assertNotIn("aucun dossier patient", reply)
        self.assertNotIn("mode démo", reply)


    def test_explicit_arabic_tir_request_answers_in_arabic(self):
        response = self._post("Explique-moi en arabe le TIR")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["reply_language"], "ar")
        self.assertIn("الوقت ضمن النطاق", payload["reply"])

    def test_language_only_followup_reuses_prior_tir_context(self):
        history = [
            {
                "role": "user",
                "content": "Explique-moi le TIR en général, sans regarder mes données.",
            },
            {
                "role": "assistant",
                "content": "Le TIR (Time in Range) est le pourcentage du temps...",
            },
        ]

        response = self._post("en arabe", history=history)

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["reply_language"], "ar")
        self.assertIn("الوقت ضمن النطاق", payload["reply"])
        self.assertNotIn("pas encore certain", payload["reply"])


    def test_natural_language_followups_reuse_prior_tir_context(self):
        history = [
            {
                "role": "user",
                "content": "Explique-moi le TIR en général, sans regarder mes données.",
            },
            {
                "role": "assistant",
                "content": "Le TIR (Time in Range) est le pourcentage du temps...",
            },
        ]

        for message in ("puis en arabe", "et en arabe", "maintenant en arabe", "alors en arabe"):
            with self.subTest(message=message):
                response = self._post(message, history=history)
                self.assertEqual(response.status_code, 200)
                payload = response.json()
                self.assertEqual(payload["reply_language"], "ar")
                self.assertIn("الوقت ضمن النطاق", payload["reply"])
                self.assertNotIn("pas encore certain", payload["reply"])

    @patch("companion.demo_runtime.IAmina")
    @patch("diabetes.services.demo_runtime._preview_route_reply")
    def test_intent_preview_failure_fails_closed_to_clarification(self, preview, iamina_cls):
        preview.side_effect = RuntimeError("preview provider unavailable")

        response = self._post("question libre")

        self.assertEqual(response.status_code, 200)
        self.assertIn("pas encore certain", response.json()["reply"])
        iamina_cls.assert_not_called()

    @patch("companion.demo_runtime.IAmina")
    def test_demo_runtime_preserves_governed_ai_egress_scope(self, iamina_cls):
        def _chat(message, context_days=14):
            del message, context_days
            context = assert_ai_egress_allowed(TEXT)
            self.assertEqual(context.purpose, "companion_chat")
            return "ok"

        iamina_cls.return_value.chat.side_effect = _chat

        response = self._post("Parle-moi de ma semaine.")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["reply"], "ok")

    def test_synthetic_demo_context_is_clinically_analyzable(self):
        patient = get_or_create_synthetic_demo_patient("contract-subject")

        context = get_domain_context(patient.id, language="fr", days=7)

        self.assertTrue(context.has_sufficient_data)
        self.assertEqual(context.analysis_status, "complete")
        self.assertTrue(context.kpi_summary)
        self.assertIn("tir_pct", context.kpi_summary)

    def test_demo_personal_tir_uses_real_synthetic_clinical_context(self):
        response = self._post("Quel est mon TIR cette semaine ?")

        self.assertEqual(response.status_code, 200)
        reply = response.json()["reply"].lower()
        self.assertNotIn("aucun dossier patient", reply)
        self.assertNotIn("mode démo", reply)
        self.assertTrue(
            "tir cgm vérifié" in reply
            or "mesures enregistrées entre 70 et 180 mg/dl" in reply
        )

    @patch("companion.conversation.get_gateway_llm")
    def test_demo_profile_lookup_bypasses_llm_provider(self, gateway):
        gateway.side_effect = AssertionError("LLM provider must not be called")

        response = self._post("Quel est mon type de diabète enregistré ?")

        self.assertEqual(response.status_code, 200)
        self.assertIn("Type 2", response.json()["reply"])
        gateway.assert_not_called()


    @patch("companion.conversation.get_gateway_llm")
    def test_demo_common_meta_turns_bypass_llm_provider(self, gateway):
        gateway.side_effect = AssertionError("LLM provider must not be called")

        greeting = self._post(
            "salam ça va ?",
            language="fr",
            session_id="meta-turns",
        )
        capabilities = self._post(
            "tu sais faire quoi ?",
            language="fr",
            session_id="meta-turns",
        )

        self.assertEqual(greeting.status_code, 200)
        self.assertIn("Salam", greeting.json()["reply"])
        self.assertEqual(capabilities.status_code, 200)
        self.assertIn("glycémie", capabilities.json()["reply"])
        gateway.assert_not_called()


    @patch("diabetes.services.demo_runtime.build_openai_compatible_provider")
    @patch("companion.conversation.get_gateway_llm")
    def test_natural_french_capability_question_stays_local(self, gateway, provider):
        gateway.side_effect = AssertionError("LLM narrator must not be called")
        provider.side_effect = AssertionError("Intent classifier must not be called")

        response = self._post("Tu sais faire quoi exactement ?")

        self.assertEqual(response.status_code, 200)
        reply = response.json()["reply"].lower()
        self.assertIn("iamina", reply)
        self.assertNotIn("oui, on peut en parler ici", reply)
        provider.assert_not_called()
        gateway.assert_not_called()

    @patch("companion.conversation.get_gateway_llm")
    def test_demo_recall_after_deterministic_patient_reply_stays_local(self, gateway):
        gateway.side_effect = AssertionError("LLM provider must not be called")

        first = self._post(
            "Quel est mon type de diabète enregistré ?",
            session_id="local-recall",
        )
        recall = self._post(
            "Qu'est-ce qu'on s'était dit juste avant ?",
            session_id="local-recall",
        )

        self.assertEqual(first.status_code, 200)
        self.assertIn("Type 2", first.json()["reply"])
        self.assertEqual(recall.status_code, 200)
        self.assertIn("Type 2", recall.json()["reply"])
        gateway.assert_not_called()

    def test_personal_weekly_request_uses_verified_synthetic_monitoring_data(self):
        response = self._post("Il est comment mon diabète cette semaine ?!")

        self.assertEqual(response.status_code, 200)
        reply = response.json()["reply"].lower()
        self.assertNotIn("comment se portent tes glycémies", reply)
        self.assertNotIn("je n'ai pas accès à tes logs", reply)
        self.assertTrue(
            "mesures sur" in reply
            or "tir cgm vérifié" in reply
            or "mesures enregistrées entre 70 et 180 mg/dl" in reply
        )

    def test_personal_log_request_uses_verified_synthetic_monitoring_data(self):
        response = self._post("check my logs and tell me!")

        self.assertEqual(response.status_code, 200)
        reply = response.json()["reply"].lower()
        self.assertNotIn("je n'ai pas accès à tes logs", reply)
        self.assertNotIn("i don't have access to your logs", reply)
        self.assertTrue(
            "mesures sur" in reply
            or "tir cgm vérifié" in reply
            or "mesures enregistrées entre 70 et 180 mg/dl" in reply
            or "recorded monitoring summary" in reply
        )

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
    def test_demo_subject_is_stable_for_same_remote_and_session(self, iamina_cls):
        iamina_cls.return_value.chat.return_value = "ok"

        first = self._post(
            "Bonjour",
            remote_addr="198.51.100.10",
            session_id="session-a",
        )
        first_patient = iamina_cls.call_args.args[0]
        second = self._post(
            "Encore",
            remote_addr="198.51.100.10",
            session_id="session-a",
        )
        second_patient = iamina_cls.call_args.args[0]

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(first_patient.id, second_patient.id)
        self.assertNotIn("198.51.100.10", first_patient.username)

    @patch("companion.demo_runtime.IAmina")
    def test_demo_subject_isolated_between_sessions_on_same_remote(self, iamina_cls):
        iamina_cls.return_value.chat.return_value = "ok"

        self._post(
            "Bonjour",
            remote_addr="198.51.100.20",
            session_id="session-a",
        )
        first_patient = iamina_cls.call_args.args[0]
        self._post(
            "Bonjour",
            remote_addr="198.51.100.20",
            session_id="session-b",
        )
        second_patient = iamina_cls.call_args.args[0]

        self.assertNotEqual(first_patient.id, second_patient.id)

    @patch("companion.demo_runtime.IAmina")
    def test_demo_subject_isolated_between_remote_addresses(self, iamina_cls):
        iamina_cls.return_value.chat.return_value = "ok"

        self._post("Bonjour", remote_addr="198.51.100.11")
        first_patient = iamina_cls.call_args.args[0]
        self._post("Bonjour", remote_addr="198.51.100.12")
        second_patient = iamina_cls.call_args.args[0]

        self.assertNotEqual(first_patient.id, second_patient.id)

    @patch("companion.demo_runtime.IAmina")
    def test_latin_darija_urgent_content_stays_deterministic(self, iamina_cls):
        response = self._post(
            "sokkar 45 w kan7ess brassi mdowekh bzaf, chno ndir daba?"
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["is_emergency"])
        self.assertEqual(payload["conversation_id"], "TRIAGE_VITAL")
        self.assertEqual(payload["reply_language"], "ar-MA")
        self.assertFalse(any("\u0600" <= ch <= "\u06ff" for ch in payload["reply"]))
        iamina_cls.assert_not_called()

    @patch("companion.demo_runtime.IAmina")
    def test_arabic_darija_urgent_content_stays_deterministic(self, iamina_cls):
        response = self._post(
            "السكر عندي 45 وكنحس براسي مشوش، شنو ندير دابا؟",
            language="ar-MA",
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["is_emergency"])
        self.assertEqual(payload["reply_language"], "ar-MA")
        iamina_cls.assert_not_called()

    @patch("companion.demo_runtime.IAmina")
    def test_gulf_urgent_content_stays_out_of_moroccan_darija(self, iamina_cls):
        response = self._post(
            "سكري 45 وأنا مشوش شوي، وش أسوي الحين؟",
            language="ar",
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["is_emergency"])
        self.assertEqual(payload["reply_language"], "ar")
        for marker in ("إلا كان", "والو", "كتبدلش", "ديالك"):
            self.assertNotIn(marker, payload["reply"])
        iamina_cls.assert_not_called()

    @patch("companion.demo_runtime.IAmina")
    def test_french_dose_request_stays_deterministic(self, iamina_cls):
        response = self._post("Combien d'unités d'insuline dois-je prendre ?")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertFalse(payload["is_emergency"])
        self.assertIn("Je ne peux pas prescrire", payload["reply"])
        iamina_cls.assert_not_called()

    @patch("companion.demo_runtime.IAmina")
    def test_arabic_darija_dose_request_stays_deterministic(self, iamina_cls):
        response = self._post(
            "قول ليا بالضبط شحال نحقن ديال الإنسولين دابا.",
            language="ar-MA",
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertFalse(payload["is_emergency"])
        self.assertEqual(payload["reply_language"], "ar-MA")
        self.assertIn("Ma nqderch", payload["reply"])
        iamina_cls.assert_not_called()

    @patch("companion.demo_runtime.IAmina")
    def test_crisis_boundary_stays_deterministic(self, iamina_cls):
        response = self._post("Je veux mourir")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["is_emergency"])
        self.assertEqual(payload["conversation_id"], "TRIAGE_CRISIS")
        self.assertTrue(payload["reply"])
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
