"""Contract tests for the public, stateless IAMINA demo conversation."""

from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.utils import timezone

from companion.demo_model import DemoModelUnavailable
from core.ai_egress import TEXT, assert_ai_egress_allowed
from core.companion.clinical import get_domain_context
from diabetes.models import LogEntry
from diabetes.services.demo_patient import get_or_create_synthetic_demo_patient


class DemoChatContractTests(TestCase):
    def setUp(self):
        self.client = Client()

    def _post(self, message: str, language: str = "fr", history=None):
        return self.client.post(
            "/api/v1/demo/chat",
            data={
                "message": message,
                "language": language,
                "history": history or [],
            },
            content_type="application/json",
        )

    def test_demo_chat_is_public_and_stateless_with_bounded_narrator(self):
        with patch(
            "companion.demo.generate_demo_reply",
            return_value="Je t'ai compris. Tu dis que tu as des vertiges. Depuis quand ?",
        ) as narrator:
            response = self._post("fia doukha")

        narrator.assert_called_once_with("fia doukha", "fr", history=[])

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["conversation_id"], "demo-governed")
        self.assertFalse(payload["is_emergency"])
        self.assertEqual(payload["reply_language"], "fr")
        self.assertTrue(payload["reply"])
        self.assertEqual(User.objects.count(), 0)
        self.assertEqual(LogEntry.objects.count(), 0)

    def test_demo_chat_forwards_bounded_history_without_persisting_it(self):
        history = [
            {"role": "user", "content": "Je veux mieux dormir."},
            {"role": "assistant", "content": "D'accord, gardons cet objectif en tête."},
        ]
        with patch(
            "companion.demo.generate_demo_reply",
            return_value="Ton objectif précédent était de mieux dormir.",
        ) as narrator:
            response = self._post(
                "Quel était mon objectif ?",
                history=history,
            )

        self.assertEqual(response.status_code, 200)
        narrator.assert_called_once_with(
            "Quel était mon objectif ?",
            "fr",
            history=history,
        )
        self.assertEqual(User.objects.count(), 0)
        self.assertEqual(LogEntry.objects.count(), 0)

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

    def test_demo_weekly_personal_diabetes_request_never_calls_model(self):
        with patch(
            "companion.demo.generate_demo_reply",
            side_effect=AssertionError("personal demo data request must stay deterministic"),
        ):
            response = self._post("Comment était mon diabète cette semaine ?")

        self.assertEqual(response.status_code, 200)
        reply = response.json()["reply"].lower()
        self.assertIn("mode démo", reply)
        self.assertIn("aucun dossier patient", reply)

    def test_demo_personal_tir_request_stays_data_bound_before_education(self):
        with patch(
            "companion.demo.generate_demo_reply",
            side_effect=AssertionError("personal TIR request must stay deterministic"),
        ):
            response = self._post(
                "Quel est mon TIR exact cette semaine ? Je n'ai partagé aucun log."
            )

        self.assertEqual(response.status_code, 200)
        reply = response.json()["reply"].lower()
        self.assertIn("aucun dossier patient", reply)
        self.assertNotIn("70–180", reply)

    def test_demo_personal_gmi_request_stays_data_bound_before_education(self):
        with patch(
            "companion.demo.generate_demo_reply",
            side_effect=AssertionError("personal GMI request must stay deterministic"),
        ):
            response = self._post(
                "What is my exact GMI this week? I shared no glucose logs.",
                language="en",
            )

        self.assertEqual(response.status_code, 200)
        reply = response.json()["reply"].lower()
        self.assertIn("cannot access any patient record", reply)
        self.assertNotIn("a1c-like estimate", reply)

    def test_demo_chat_routes_latin_darija_low_glucose_before_model(self):
        with patch(
            "companion.demo.generate_demo_reply",
            side_effect=AssertionError("urgent content must stay deterministic"),
        ):
            response = self._post(
                "sokkar 45 w kan7ess brassi mdowekh bzaf, chno ndir daba?"
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["is_emergency"])
        self.assertEqual(payload["conversation_id"], "TRIAGE_VITAL")
        self.assertEqual(payload["reply_language"], "ar-MA")
        self.assertFalse(
            any("\u0600" <= ch <= "\u06ff" for ch in payload["reply"])
        )

    def test_demo_chat_keeps_arabic_darija_emergency_script_consistent(self):
        response = self._post(
            "السكر عندي 45 وكنحس براسي مشوش، شنو ندير دابا؟",
            language="ar-MA",
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["is_emergency"])
        self.assertEqual(payload["reply_language"], "ar-MA")
        self.assertNotIn("ma katra9ebch", payload["reply"])

    def test_demo_chat_keeps_gulf_emergency_out_of_moroccan_darija(self):
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

    def test_demo_chat_arabic_darija_dose_stays_deterministic(self):
        with patch(
            "companion.demo.generate_demo_reply",
            side_effect=AssertionError("dose request must stay deterministic"),
        ):
            response = self._post(
                "قول ليا بالضبط شحال نحقن ديال الإنسولين دابا.",
                language="ar-MA",
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertFalse(payload["is_emergency"])
        self.assertEqual(payload["reply_language"], "ar-MA")
        self.assertIn("ما نقدرش", payload["reply"])
        self.assertFalse(any(ch.isascii() and ch.isalpha() for ch in payload["reply"]))

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
        from core.models import AIUserThrottleWindow

        fixed_now = timezone.now()
        with (
            patch("diabetes.api.v1.demo.timezone.now", return_value=fixed_now),
            patch("companion.demo.generate_demo_reply", return_value="Réponse démo."),
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

    def test_demo_chat_uses_gulf_casual_fallback_when_model_is_rejected(self):
        with patch(
            "companion.demo.generate_demo_reply",
            side_effect=DemoModelUnavailable("dialect/script guard"),
        ):
            response = self._post("هلا، ما أبي حلول الحين، بس ودي أسولف شوي.", language="ar")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["reply_language"], "ar")
        self.assertIn("سوالف خفيفة", payload["reply"])
        self.assertNotIn("وضع العرض", payload["reply"])

    def test_demo_chat_varies_gulf_casual_fallback_on_continuation(self):
        history = [
            {"role": "user", "content": "هلا، ما أبي حلول الحين، بس ودي أسولف شوي."},
            {"role": "assistant", "content": "تمام، نخليها سوالف خفيفة وبس."},
        ]
        with patch(
            "companion.demo.generate_demo_reply",
            side_effect=DemoModelUnavailable("dialect/script guard"),
        ):
            first = self._post("هلا، ما أبي حلول الحين، بس ودي أسولف شوي.", language="ar")
            followup = self._post(
                "إيه كذا أحسن، خلك خفيف وبسيط.",
                language="ar",
                history=history,
            )

        self.assertEqual(first.status_code, 200)
        self.assertEqual(followup.status_code, 200)
        self.assertNotEqual(first.json()["reply"], followup.json()["reply"])
        self.assertNotIn("وضع العرض", followup.json()["reply"])

    def test_demo_chat_uses_latin_darija_casual_fallback(self):
        with patch(
            "companion.demo.generate_demo_reply",
            side_effect=DemoModelUnavailable("dialect/script guard"),
        ):
            response = self._post("salam, ma bghit ta chi 7al daba, ghir n9ssr m3ak chwia")

        self.assertEqual(response.status_code, 200)
        reply = response.json()["reply"]
        self.assertIn("nhdro", reply)
        self.assertFalse(any("\u0600" <= ch <= "\u06ff" for ch in reply))
        self.assertNotIn("mode démo", reply.lower())

    def test_demo_chat_inherits_casual_mode_from_history_on_followup(self):
        history = [
            {"role": "user", "content": "هلا، ما أبي حلول الحين، بس ودي أسولف شوي."},
            {"role": "assistant", "content": "تمام، نخليها سوالف خفيفة وبس."},
        ]
        with patch(
            "companion.demo.generate_demo_reply",
            side_effect=DemoModelUnavailable("dialect/script guard"),
        ):
            response = self._post(
                "إيه كذا أحسن، خلك خفيف وبسيط.",
                language="ar",
                history=history,
            )

        self.assertEqual(response.status_code, 200)
        reply = response.json()["reply"]
        self.assertIn("سوالف خفيفة", reply)
        self.assertNotIn("وضع العرض", reply)

    def test_demo_food_permission_boundary_blocks_yes_no_approval_in_french(self):
        with patch(
            "companion.demo.generate_demo_reply",
            side_effect=AssertionError("food permission must stay deterministic"),
        ):
            response = self._post("je peux manger un mille feuille !?")

        self.assertEqual(response.status_code, 200)
        reply = response.json()["reply"]
        self.assertIn("Je ne peux pas te donner un feu vert/rouge personnalisé", reply)
        self.assertIn("glucides", reply)
        self.assertNotIn("Oui", reply)
        self.assertNotIn("allerg", reply.lower())

    def test_demo_food_permission_boundary_blocks_yes_no_approval_in_english(self):
        with patch(
            "companion.demo.generate_demo_reply",
            side_effect=AssertionError("food permission must stay deterministic"),
        ):
            response = self._post("Can I eat a slice of cake?", language="en")

        self.assertEqual(response.status_code, 200)
        reply = response.json()["reply"]
        self.assertIn("can’t give a personalized yes/no approval", reply)
        self.assertIn("carbohydrate", reply.lower())
        self.assertNotIn("Sure", reply)

    def test_demo_food_permission_boundary_stays_latin_in_darija(self):
        with patch(
            "companion.demo.generate_demo_reply",
            side_effect=AssertionError("food permission must stay deterministic"),
        ):
            response = self._post("wach n9dar nakol gateau?", language="fr")

        self.assertEqual(response.status_code, 200)
        reply = response.json()["reply"]
        self.assertIn("Ma n9drch ngolik yes/no", reply)
        self.assertFalse(any("\u0600" <= ch <= "\u06ff" for ch in reply))
        self.assertNotIn("activité", reply.lower())

    def test_demo_food_permission_boundary_blocks_yes_no_approval_in_arabic(self):
        with patch(
            "companion.demo.generate_demo_reply",
            side_effect=AssertionError("food permission must stay deterministic"),
        ):
            response = self._post("هل أقدر آكل قطعة حلوى؟", language="ar")

        self.assertEqual(response.status_code, 200)
        reply = response.json()["reply"]
        self.assertIn("ما أقدر أعطيك موافقة شخصية", reply)
        self.assertIn("الكربوهيدرات", reply)
        self.assertNotIn("أكيد", reply)

    def test_demo_reported_food_context_uses_governed_food_rule_from_history(self):
        history = [
            {"role": "user", "content": "j ai très faim et je viens de manger"},
            {
                "role": "assistant",
                "content": "Je comprends. Qu'est-ce que tu as mangé ?",
            },
        ]
        with patch(
            "companion.demo.generate_demo_reply",
            side_effect=AssertionError("reported food context must stay deterministic"),
        ):
            response = self._post(
                "mille feuilles et jus dananas",
                history=history,
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        reply = payload["reply"].lower()
        self.assertEqual(payload["conversation_id"], "demo-governed")
        self.assertIn("portion", reply)
        self.assertIn("glucides", reply)
        self.assertNotIn("gourmand", reply)

    def test_demo_non_food_history_does_not_force_food_governance(self):
        history = [
            {"role": "user", "content": "Je suis fatigué aujourd'hui."},
            {"role": "assistant", "content": "Tu veux en parler ?"},
        ]
        with patch(
            "companion.demo.generate_demo_reply",
            return_value="Oui, raconte-moi.",
        ) as narrator:
            response = self._post("Pas grand-chose.", history=history)

        self.assertEqual(response.status_code, 200)
        narrator.assert_called_once_with("Pas grand-chose.", "fr", history=history)
        self.assertEqual(response.json()["reply"], "Oui, raconte-moi.")

    def test_demo_chat_recognizes_gulf_casual_variant_without_solutions(self):
        with patch(
            "companion.demo.generate_demo_reply",
            side_effect=DemoModelUnavailable("dialect/script guard"),
        ):
            response = self._post(
                "هلا، ودي أسولف شوي بدون حلول.",
                language="ar",
            )

        self.assertEqual(response.status_code, 200)
        reply = response.json()["reply"]
        self.assertIn("سوالف خفيفة", reply)
        self.assertNotIn("وضع العرض", reply)

    def test_demo_chat_recognizes_arabic_darija_casual_variant(self):
        with patch(
            "companion.demo.generate_demo_reply",
            side_effect=DemoModelUnavailable("dialect/script guard"),
        ):
            response = self._post(
                "سلام، بغيت غير نهضر شوية بلا نصائح.",
                language="ar-MA",
            )

        self.assertEqual(response.status_code, 200)
        reply = response.json()["reply"]
        self.assertIn("نهضرو", reply)
        self.assertNotIn("فالوضع التجريبي", reply)



class DemoRuntimeParityTests(TestCase):
    def setUp(self):
        self.client = Client()

    def _post(
        self,
        message: str,
        language: str = "fr",
        history=None,
        remote_addr: str = "127.0.0.1",
    ):
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
        self.assertFalse(patient.has_usable_password())
        self.assertGreater(LogEntry.objects.filter(patient=patient).count(), 20)
        iamina_cls.return_value.chat.assert_called_once_with(
            "Comment était mon diabète cette semaine ?",
            context_days=14,
        )
        self.assertEqual(response.json()["reply"], "Réponse issue du runtime IAmina.")

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
