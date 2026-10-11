"""Regression for legacy patient-text-in-URL SSE transport (#925).

Does not prove that CDN, edge, access logs or historical URLs are redacted.
"""

from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import Client, TestCase


class LegacySseNoProviderTest(TestCase):
    def setUp(self):
        self.patient = User.objects.create_user(username="legacy-sse-synthetic")
        self.browser = Client()
        self.browser.force_login(self.patient)

    @patch("companion.core.IAmina")
    def test_query_message_get_returns_405_without_provider(self, ai_cls):
        secret = "SYNTHETIC_PRIVATE_GLUC_175_MGDL"
        response = self.browser.get(
            "/api/v1/ai/chat/stream", {"message": secret, "context_days": 14}
        )
        self.assertEqual(response.status_code, 405)
        self.assertNotIn(secret, response.content.decode("utf-8"))
        ai_cls.assert_not_called()
