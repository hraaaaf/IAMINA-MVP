"""Focused tests for public-demo model selection boundaries."""

import json
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

    @patch.dict(
        os.environ,
        {
            "IAMINA_DEMO_EXTERNAL_AI_ENABLED": "true",
            "IAMINA_DEMO_LLM_PROVIDER": "groq",
            "IAMINA_DEMO_LLM_MODEL": "",
        },
        clear=False,
    )
    @patch("companion.demo_model.build_openai_compatible_provider")
    def test_demo_history_is_serialized_only_inside_current_request(self, build):
        provider = MagicMock()
        provider.complete.return_value.content = "Ton objectif était de mieux dormir."
        build.return_value = provider

        history = [
            {"role": "user", "content": "Je veux mieux dormir."},
            {"role": "assistant", "content": "D'accord, je garde cet objectif en tête."},
        ]
        generate_demo_reply(
            "Quel était mon objectif ?",
            "fr",
            history=history,
        )

        _, user_payload = provider.complete.call_args.args
        decoded = json.loads(user_payload)
        self.assertEqual(decoded["bounded_demo_history"], history)
        self.assertEqual(decoded["current_message"], "Quel était mon objectif ?")

    @patch.dict(
        os.environ,
        {
            "IAMINA_DEMO_EXTERNAL_AI_ENABLED": "true",
            "IAMINA_DEMO_LLM_PROVIDER": "groq",
            "IAMINA_DEMO_LLM_MODEL": "",
        },
        clear=False,
    )
    @patch("companion.demo_model.build_openai_compatible_provider")
    def test_sensitive_history_pair_is_dropped_before_provider(self, build):
        provider = MagicMock()
        provider.complete.return_value.content = "Bonjour."
        build.return_value = provider

        generate_demo_reply(
            "Continuons.",
            "fr",
            history=[
                {"role": "user", "content": "Mon email est patient@example.com"},
                {"role": "assistant", "content": "Merci."},
            ],
        )

        _, user_payload = provider.complete.call_args.args
        decoded = json.loads(user_payload)
        self.assertEqual(decoded["bounded_demo_history"], [])

    @patch.dict(
        os.environ,
        {
            "IAMINA_DEMO_EXTERNAL_AI_ENABLED": "true",
            "IAMINA_DEMO_LLM_PROVIDER": "groq",
            "IAMINA_DEMO_LLM_MODEL": "",
        },
        clear=False,
    )
    @patch("companion.demo_model.build_openai_compatible_provider")
    def test_safety_bound_history_pair_is_dropped_before_provider(self, build):
        provider = MagicMock()
        provider.complete.return_value.content = "On peut continuer de façon générale."
        build.return_value = provider

        generate_demo_reply(
            "Parlons d'autre chose.",
            "fr",
            history=[
                {"role": "user", "content": "Combien d'unités d'insuline dois-je prendre ?"},
                {"role": "assistant", "content": "Je ne peux pas prescrire."},
            ],
        )

        _, user_payload = provider.complete.call_args.args
        decoded = json.loads(user_payload)
        self.assertEqual(decoded["bounded_demo_history"], [])

