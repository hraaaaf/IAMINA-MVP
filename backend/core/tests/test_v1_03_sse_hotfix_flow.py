"""Synthetic-only SSE hotfix integration tests on the isolated main-based PR.

These in-process tests do not inspect CDN, edge, proxies or actual patient data.
"""
import json
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import Client, TestCase


class SseHotfixFlowTests(TestCase):
    def setUp(self):
        self.patient = User.objects.create_user(username="sse-hotfix-synthetic")
        self.browser = Client()
        self.browser.force_login(self.patient)

    @staticmethod
    def post(client, message="Synthetic greeting."):
        return client.post(
            "/api/v1/ai/chat/stream",
            data=json.dumps({"message": message, "context_days": 14}),
            content_type="application/json",
        )

    @patch("companion.advice_filter.contains_medical_advice", return_value=False)
    @patch("companion.router.route")
    @patch("companion.core.IAmina")
    def test_post_json_delivers_sse_without_text_in_url(
        self, ai_class, _route, _contains_advice
    ):
        marker = "SYNTHETIC_PRIVATE_POST_BODY_ONLY"
        ai_class.return_value.stream_chat.return_value = iter(
            ["Bonjour. ", "Comment allez-vous ?"]
        )
        response = self.post(self.browser, marker)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.streaming)
        self.assertEqual(response["Content-Type"], "text/event-stream")
        self.assertEqual(response["Cache-Control"], "no-store")
        self.assertNotIn(marker, response.wsgi_request.get_full_path())
        data = b"".join(response.streaming_content).decode("utf-8")
        self.assertIn("data: [DONE]", data)
        self.assertIn("Bonjour", data)
        ai_class.return_value.stream_chat.assert_called_once_with(
            marker, context_days=14
        )

    @patch("companion.core.IAmina")
    def test_session_post_rejects_missing_csrf_despite_spoofed_bearer(self, ai_class):
        browser = Client(enforce_csrf_checks=True)
        browser.force_login(self.patient)
        response = browser.post(
            "/api/v1/ai/chat/stream",
            data=json.dumps({"message": "Synthetic greeting.", "context_days": 14}),
            content_type="application/json",
            HTTP_AUTHORIZATION="Bearer invalid.synthetic.credential",
        )
        self.assertEqual(response.status_code, 403)
        ai_class.assert_not_called()

    @patch("companion.core.IAmina")
    def test_invalid_post_json_does_not_reach_companion(self, ai_class):
        response = self.browser.post(
            "/api/v1/ai/chat/stream",
            data=json.dumps({"context_days": 14}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 422)
        ai_class.assert_not_called()

    @patch("companion.core.IAmina")
    @patch("core.middleware.triage_vital.logger.critical")
    def test_urgent_post_uses_canonical_sse_after_session_csrf(
        self, critical_log, ai_class
    ):
        browser = Client(enforce_csrf_checks=True)
        browser.force_login(self.patient)
        marker = "Je suis inconscient, urgence glycémie"

        forbidden = self.post(browser, marker)
        self.assertEqual(forbidden.status_code, 403)

        token = "a" * 32
        browser.cookies["csrftoken"] = token
        response = browser.post(
            "/api/v1/ai/chat/stream",
            data=json.dumps({"message": marker, "context_days": 14}),
            content_type="application/json",
            HTTP_X_CSRFTOKEN=token,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.streaming)
        self.assertEqual(response["Content-Type"], "text/event-stream")
        self.assertEqual(response["Cache-Control"], "no-store")
        data = b"".join(response.streaming_content).decode("utf-8")
        first = data.split("\n\n")[0]
        self.assertTrue(first.startswith("data: "))
        event = json.loads(first.removeprefix("data: "))
        self.assertTrue(event["is_emergency"])
        self.assertIn("token", event)
        self.assertIn("data: [DONE]", data)
        ai_class.assert_not_called()
        critical_log.assert_not_called()

    @patch("companion.core.IAmina")
    def test_anonymous_urgent_post_never_bypasses_ninja_auth(self, ai_class):
        anonymous = Client()
        response = self.post(anonymous, "Je suis inconscient, urgence glycémie")
        self.assertIn(response.status_code, (401, 403))
        ai_class.assert_not_called()

    @patch("core.middleware.triage_vital.logger.critical")
    def test_nonstream_urgent_log_never_contains_health_text_or_user_id(
        self, critical_log
    ):
        marker = "Je suis inconscient - SYNTHETIC_PRIVATE_MEASUREMENT_175"
        response = self.browser.post(
            "/api/v1/ai/chat",
            data=json.dumps({"message": marker, "context_days": 14}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["is_emergency"])
        critical_log.assert_called()
        for call in critical_log.call_args_list:
            self.assertNotIn(marker, str(call))
            self.assertNotIn("snippet=", str(call))
            self.assertNotIn("user_id=", str(call))
