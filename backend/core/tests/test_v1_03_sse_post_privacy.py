"""V1-03 #925: synthetic SSE POST privacy and deferred egress scope tests."""

import json
from datetime import date
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.utils import timezone

from core.ai_egress import TEXT, AIEgressDenied, assert_ai_egress_allowed
from core.consent_notice import expected_notice_claim
from core.models import BasePatientProfile


class PatientSsePostPrivacyTests(TestCase):
    def setUp(self):
        self.patient = self._patient("sse-privacy-a")
        self.client.force_login(self.patient)

    @staticmethod
    def _patient(username):
        user = User.objects.create_user(username=username)
        claim = expected_notice_claim("fr")
        BasePatientProfile.objects.create(
            patient=user,
            date_of_birth=date(1990, 1, 1),
            ai_consent_given_at=timezone.now(),
            ai_consent_notice_version=claim.version,
            ai_consent_notice_hash=claim.notice_hash,
            ai_consent_notice_locale=claim.locale,
        )
        return user

    def _post(self, client, text="Bonjour IAmina.", days=14):
        return client.post(
            "/api/v1/ai/chat/stream",
            data=json.dumps({"message": text, "context_days": days}),
            content_type="application/json",
        )

    def test_get_query_transport_is_disabled(self):
        response = self.client.get("/api/v1/ai/chat/stream?message=synthetic")
        self.assertEqual(response.status_code, 405)

    @patch("companion.advice_filter.contains_medical_advice", return_value=False)
    @patch("companion.router.route")
    @patch("companion.core.IAmina")
    def test_post_body_and_deferred_scope_reset_between_chunks(
        self, ai_cls, _route, _advice
    ):
        message = "Synthetic patient-safe greeting."

        def chunks(text, context_days):
            self.assertEqual(text, message)
            self.assertEqual(context_days, 14)
            scope = assert_ai_egress_allowed(TEXT)
            self.assertEqual(scope.patient_id, self.patient.id)
            yield "Bonjour. "
            scope = assert_ai_egress_allowed(TEXT)
            self.assertEqual(scope.patient_id, self.patient.id)
            yield "Comment allez-vous ?"

        ai_cls.return_value.stream_chat.side_effect = chunks
        response = self._post(self.client, message)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/event-stream")
        self.assertNotIn(message, response.wsgi_request.get_full_path())

        with self.assertRaises(AIEgressDenied):
            assert_ai_egress_allowed(TEXT)
        iterator = iter(response.streaming_content)
        first = next(iterator).decode()
        self.assertIn('"token"', first)
        with self.assertRaises(AIEgressDenied):
            assert_ai_egress_allowed(TEXT)
        remainder = b"".join(iterator).decode()
        self.assertIn("[DONE]", remainder)
        with self.assertRaises(AIEgressDenied):
            assert_ai_egress_allowed(TEXT)
        ai_cls.return_value.stream_chat.assert_called_once_with(
            message, context_days=14
        )

    @patch("companion.advice_filter.contains_medical_advice", return_value=False)
    @patch("companion.router.route")
    @patch("companion.core.IAmina")
    def test_interleaved_streams_never_share_patient_scope(
        self, ai_cls, _route, _advice
    ):
        patient_b = self._patient("sse-privacy-b")
        other_client = Client()
        other_client.force_login(patient_b)

        testcase = self

        def construct(patient, language):
            class FakeAi:
                def stream_chat(self, message, context_days):
                    for value in ["Bonjour. ", "Encore. ", "Fin."]:
                        context = assert_ai_egress_allowed(TEXT)
                        testcase.assertEqual(context.patient_id, patient.id)
                        yield value

            return FakeAi()

        ai_cls.side_effect = construct
        response_a = self._post(self.client, "Test A")
        response_b = self._post(other_client, "Test B")
        self.assertEqual(response_a.status_code, 200)
        self.assertEqual(response_b.status_code, 200)
        a, b = iter(response_a.streaming_content), iter(response_b.streaming_content)
        self.assertTrue(next(a).startswith(b"data: "))
        with self.assertRaises(AIEgressDenied):
            assert_ai_egress_allowed(TEXT)
        self.assertTrue(next(b).startswith(b"data: "))
        output_a = b"".join(a).decode()
        output_b = b"".join(b).decode()
        self.assertIn("[DONE]", output_a)
        self.assertIn("[DONE]", output_b)
        self.assertIn("Fin.", output_a)
        self.assertIn("Fin.", output_b)
        self.assertNotIn("Une erreur", output_a + output_b)
        with self.assertRaises(AIEgressDenied):
            assert_ai_egress_allowed(TEXT)

    @patch("companion.router.route")
    @patch("companion.core.IAmina")
    def test_denied_server_consent_never_enters_provider(self, ai_cls, _route):
        patient = self.patient
        profile = patient.base_profile
        profile.ai_consent_given_at = None
        profile.save(update_fields=["ai_consent_given_at"])
        calls = []

        def blocked_stream(_message, context_days):
            assert_ai_egress_allowed(TEXT)
            calls.append("provider-entered")
            yield "Should never be emitted"

        ai_cls.return_value.stream_chat.side_effect = blocked_stream
        response = self._post(self.client, "Synthetic forbidden chat")
        self.assertEqual(response.status_code, 200)
        payload = b"".join(response.streaming_content).decode()
        self.assertIn("Une erreur est survenue.", payload)
        self.assertNotIn("Should never", payload)
        self.assertEqual(calls, [])
        with self.assertRaises(AIEgressDenied):
            assert_ai_egress_allowed(TEXT)

    @patch("companion.core.IAmina")
    def test_unauthenticated_post_is_denied(self, ai_cls):
        anonymous = Client()
        response = self._post(anonymous, "Synthetic unauthed text")
        self.assertIn(response.status_code, (401, 403))
        ai_cls.assert_not_called()

    @patch("companion.core.IAmina")
    def test_invalid_json_body_is_rejected_before_stream(self, ai_cls):
        response = self.client.post(
            "/api/v1/ai/chat/stream",
            data=json.dumps({"context_days": 14}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 422)
        ai_cls.assert_not_called()

    @patch("companion.core.IAmina")
    def test_urgent_post_stream_returns_canonical_sse_not_json(self, ai_cls):
        synthetic = "Je suis inconscient, urgence glycémie"
        with self.assertLogs("core.middleware.triage_vital", level="CRITICAL") as observed:
            response = self._post(self.client, synthetic)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.streaming)
        self.assertEqual(response["Content-Type"], "text/event-stream")
        self.assertEqual(response["Cache-Control"], "no-store")
        body = b"".join(response.streaming_content).decode("utf-8")
        self.assertIn("data: [DONE]", body)
        first = next(line[6:] for line in body.splitlines() if line.startswith("data: {"))
        event = json.loads(first)
        self.assertTrue(event["is_emergency"])
        self.assertIn("token", event)
        self.assertTrue(event["token"])
        self.assertNotIn(synthetic, "\\n".join(observed.output))
        ai_cls.assert_not_called()

    @patch("companion.core.IAmina")
    def test_nonstream_urgent_keeps_json_response_contract(self, ai_cls):
        response = self.client.post(
            "/api/v1/ai/chat",
            data=json.dumps({"message": "Je suis inconscient, urgence glycémie"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.streaming)
        self.assertTrue(response.json()["is_emergency"])
        ai_cls.assert_not_called()

    @patch("companion.core.IAmina")
    @patch("core.middleware.triage_vital.logger.critical")
    @patch("core.middleware.triage_vital.evaluate_input_safety")
    def test_urgent_post_preserves_sse_and_no_patient_message_logging(
        self, triage_decision, critical_log, ai_cls
    ):
        from core.input_safety import URGENT, InputSafetyDecision

        triage_decision.return_value = InputSafetyDecision(
            URGENT, "glycemic_emergency"
        )
        message = "Synthetic patient emergency phrase."
        response = self._post(self.client, message)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.streaming)
        self.assertEqual(response["Content-Type"], "text/event-stream")
        self.assertEqual(response["Cache-Control"], "no-store")
        raw_events = b"".join(response.streaming_content).decode()
        first_event = raw_events.split("\n\n")[0]
        self.assertTrue(first_event.startswith("data: "))
        event = json.loads(first_event.removeprefix("data: "))
        self.assertTrue(event["is_emergency"])
        self.assertTrue(event["token"])
        self.assertIn("data: [DONE]", raw_events)
        ai_cls.assert_not_called()
        critical_log.assert_called()
        for call in critical_log.call_args_list:
            self.assertNotIn(message, str(call))

    @patch("companion.router.route")
    @patch("companion.core.IAmina")
    def test_stream_exception_does_not_log_patient_body(self, ai_cls, _route):
        synthetic_secret = "SYNTHETIC_PRIVATE_PATIENT_DIABETES_175"
        ai_cls.return_value.stream_chat.side_effect = RuntimeError(synthetic_secret)
        with self.assertLogs("ai.api.v1.ai", level="ERROR") as observed:
            response = self._post(self.client, synthetic_secret)
            body = b"".join(response.streaming_content).decode()
        self.assertIn("Une erreur est survenue.", body)
        self.assertNotIn(synthetic_secret, "\n".join(observed.output))
