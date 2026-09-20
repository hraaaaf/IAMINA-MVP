"""Focused tests for public-demo model selection boundaries."""

import os
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from companion.demo_model import generate_demo_reply


class DemoModelSelectionTests(SimpleTestCase):
    @patch.dict(os.environ, {"IAMINA_DEMO_EXTERNAL_AI_ENABLED": "true", "IAMINA_DEMO_LLM_PROVIDER": "groq", "IAMINA_DEMO_LLM_MODEL": "allam-2-7b"}, clear=False)
    @patch("companion.demo_model.build_openai_compatible_provider")
    def test_demo_model_override_is_isolated_to_public_demo(self, build):
        provider = MagicMock()
        provider.complete.return_value.content = "Fahmtk. Kat7ess b doukha daba?"
        build.return_value = provider
        reply = generate_demo_reply("fia doukha", "fr")
        build.assert_called_once_with("groq", model="allam-2-7b")
        self.assertEqual(reply, "Fahmtk. Kat7ess b doukha daba?")

    @patch.dict(os.environ, {"IAMINA_DEMO_EXTERNAL_AI_ENABLED": "true", "IAMINA_DEMO_LLM_PROVIDER": "groq", "IAMINA_DEMO_LLM_MODEL": ""}, clear=False)
    @patch("companion.demo_model.build_openai_compatible_provider")
    def test_unset_override_preserves_registry_default(self, build):
        provider = MagicMock()
        provider.complete.return_value.content = "Hello."
        build.return_value = provider
        generate_demo_reply("Hello", "en")
        build.assert_called_once_with("groq", model=None)
