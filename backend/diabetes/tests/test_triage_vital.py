"""TriageVitalMiddleware regression tests.

The middleware must classify urgent glycemic/distress input deterministically,
select language deterministically, and never invent a country emergency number.
Country-specific contact selection is covered separately through the versioned
``core.emergency_resources`` jurisdiction contract.
"""

import json

from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory, SimpleTestCase, TestCase

from core.locale import ResolvedLocale
from core.middleware.triage_vital import (
    TriageVitalMiddleware,
    _pick_emergency_response,
    detect_vital_distress,
)


def _unconfirmed_locale() -> ResolvedLocale:
    return ResolvedLocale(
        country_code=None,
        ui_language="fr",
        response_language="fr",
        script_preference="latin",
        transliteration_preference="none",
        dialect=None,
        glucose_unit="mg/dL",
        timezone=None,
        country_confirmed=False,
        timezone_confirmed=False,
    )


class DetectVitalDistressTests(SimpleTestCase):
    def test_french_keyword_triggers(self):
        self.assertTrue(detect_vital_distress("Je suis inconscient"))

    def test_darija_keyword_triggers(self):
        self.assertTrue(detect_vital_distress("3yyan bzaf, ma3endouch l7al"))

    def test_safe_message_does_not_trigger(self):
        self.assertFalse(detect_vital_distress("Ma glycémie est à 140 ce matin."))

    def test_numeric_near_glucose_keyword_triggers(self):
        self.assertTrue(detect_vital_distress("ma glycémie est à 32"))

    def test_numeric_without_glucose_context_is_safe(self):
        self.assertFalse(
            detect_vital_distress("j'ai mis 40g de sucre glace dans le gâteau")
        )

    def test_empty_string_is_safe(self):
        self.assertFalse(detect_vital_distress(""))

    def test_loss_of_consciousness_keyword_triggers(self):
        self.assertTrue(detect_vital_distress("Il est inconscient"))

    def test_breathing_distress_keyword_triggers(self):
        self.assertTrue(detect_vital_distress("Elle a une difficulté à respirer"))

    def test_arabic_unicode_glucose_triggers(self):
        self.assertTrue(detect_vital_distress("عندي سكريتي 35 وكانزووم"))

    def test_arabic_unicode_glucose_number_pattern(self):
        self.assertTrue(detect_vital_distress("سكري 28"))


class PickEmergencyResponseTests(SimpleTestCase):
    def test_pure_french_returns_french_number_free_response_when_unconfirmed(self):
        payload = _pick_emergency_response(
            "Je suis inconscient",
            locale=_unconfirmed_locale(),
            language="fr",
        )
        self.assertTrue(payload["is_emergency"])
        self.assertEqual(payload["conversation_id"], "TRIAGE_VITAL")
        self.assertIn("SITUATION D'URGENCE", payload["reply"])
        self.assertIn("pas de numéro d'urgence confirmé", payload["reply"])
        self.assertNotIn("SAMU", payload["reply"])

    def test_darija_tokens_return_darija_number_free_response_when_unconfirmed(self):
        payload = _pick_emergency_response(
            "3yyan bzaf sukkar bhal zero ma3endouch",
            locale=_unconfirmed_locale(),
            language="ar-MA",
        )
        self.assertTrue(payload["is_emergency"])
        self.assertEqual(payload["conversation_id"], "TRIAGE_VITAL")
        self.assertIn("ما عندناش رقم مؤكد", payload["reply"])

    def test_message_language_fallback_detects_single_darija_indicator(self):
        payload = _pick_emergency_response(
            "je suis 3yyan et je me sens très mal",
            locale=_unconfirmed_locale(),
        )
        self.assertTrue(payload["is_emergency"])
        self.assertIn("IAmina", payload["reply"])
        self.assertNotIn("SITUATION D'URGENCE", payload["reply"])


class TriageVitalMiddlewareTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.sentinel = object()
        self.middleware = TriageVitalMiddleware(get_response=lambda request: self.sentinel)

    def _post_chat(self, message: str):
        request = self.factory.post(
            "/api/v1/ai/chat",
            data=json.dumps({"message": message}),
            content_type="application/json",
        )
        request.user = AnonymousUser()
        return self.middleware(request)

    def test_french_emergency_returns_200_json_without_invented_country_number(self):
        response = self._post_chat("Je suis inconscient, j'ai du mal à respirer")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data["is_emergency"])
        self.assertIn("timestamp", data)
        self.assertIn("pas de numéro d'urgence confirmé", data["reply"])

    def test_darija_emergency_remains_number_free_for_anonymous_unconfirmed_user(self):
        response = self._post_chat("3yyan bzaf ma3endouch l7al")
        data = json.loads(response.content)
        self.assertTrue(data["is_emergency"])
        self.assertIn("ما عندناش رقم مؤكد", data["reply"])

    def test_safe_french_message_passes_through(self):
        response = self._post_chat("Ma glycémie est à 140 ce matin.")
        self.assertIs(response, self.sentinel)

    def test_non_post_always_passes_through(self):
        request = self.factory.get("/api/v1/ai/chat")
        request.user = AnonymousUser()
        response = self.middleware(request)
        self.assertIs(response, self.sentinel)

    def test_non_chat_path_passes_through(self):
        request = self.factory.post(
            "/api/v1/logs",
            data=json.dumps({"blood_sugar": 120}),
            content_type="application/json",
        )
        request.user = AnonymousUser()
        response = self.middleware(request)
        self.assertIs(response, self.sentinel)

    def test_malformed_json_body_passes_through(self):
        request = self.factory.post(
            "/api/v1/ai/chat",
            data=b"not json",
            content_type="application/json",
        )
        request.user = AnonymousUser()
        response = self.middleware(request)
        self.assertIs(response, self.sentinel)
