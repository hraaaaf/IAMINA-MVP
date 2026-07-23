"""
TriageVitalMiddleware — unit tests
===================================
Covers three layers:

  1. detect_vital_distress()   — keyword + numeric pattern detection
  2. _pick_emergency_response() — language selection (FR vs Darija)
  3. TriageVitalMiddleware      — WSGI middleware integration (RequestFactory)
"""
import json

from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory, SimpleTestCase, TestCase

from core.middleware.triage_vital import (
    _EMERGENCY_RESPONSE_DARIJA,
    _EMERGENCY_RESPONSE_FR,
    TriageVitalMiddleware,
    _pick_emergency_response,
    detect_vital_distress,
)

# ─────────────────────────────────────────────────────────────────────────────
# 1. detect_vital_distress()
# ─────────────────────────────────────────────────────────────────────────────

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
        # "40g de sucre glace" — numeric but no glucose proximity keyword
        self.assertFalse(detect_vital_distress("j'ai mis 40g de sucre glace dans le gâteau"))

    def test_empty_string_is_safe(self):
        self.assertFalse(detect_vital_distress(""))

    def test_coma_keyword_triggers(self):
        self.assertTrue(detect_vital_distress("Il est dans le coma depuis hier"))

    def test_convulsion_keyword_triggers(self):
        self.assertTrue(detect_vital_distress("Elle a eu des convulsions"))

    def test_arabic_unicode_glucose_triggers(self):
        # Regression: patients who type in Arabic script must be caught.
        self.assertTrue(detect_vital_distress("عندي سكريتي 35 وكانزووم"))

    def test_arabic_unicode_glucose_number_pattern(self):
        self.assertTrue(detect_vital_distress("سكري 28"))

    def test_arabic_unicode_vertigo_triggers(self):
        self.assertTrue(detect_vital_distress("كانزووم وما قادرش نمشي"))


# ─────────────────────────────────────────────────────────────────────────────
# 2. _pick_emergency_response()
# ─────────────────────────────────────────────────────────────────────────────

class PickEmergencyResponseTests(SimpleTestCase):

    def test_pure_french_returns_fr_response(self):
        msg = "Je suis en train de tomber dans les pommes, j'ai du mal à respirer"
        self.assertIs(_pick_emergency_response(msg), _EMERGENCY_RESPONSE_FR)

    def test_darija_tokens_return_darija_response(self):
        msg = "3yyan bzaf sukkar bhal zero ma3endouch"
        self.assertIs(_pick_emergency_response(msg), _EMERGENCY_RESPONSE_DARIJA)

    def test_darija_single_indicator_is_enough(self):
        # One Darija token mixed into otherwise French text → Darija response
        msg = "je suis 3yyan j'ai des convulsions"
        self.assertIs(_pick_emergency_response(msg), _EMERGENCY_RESPONSE_DARIJA)

    def test_fr_response_has_samu_15(self):
        self.assertIn("15", _EMERGENCY_RESPONSE_FR["reply"])

    def test_darija_response_has_moroccan_141(self):
        self.assertIn("141", _EMERGENCY_RESPONSE_DARIJA["reply"])

    def test_both_responses_have_is_emergency_true(self):
        self.assertTrue(_EMERGENCY_RESPONSE_FR["is_emergency"])
        self.assertTrue(_EMERGENCY_RESPONSE_DARIJA["is_emergency"])

    def test_both_responses_have_triage_vital_id(self):
        self.assertEqual(_EMERGENCY_RESPONSE_FR["conversation_id"], "TRIAGE_VITAL")
        self.assertEqual(_EMERGENCY_RESPONSE_DARIJA["conversation_id"], "TRIAGE_VITAL")


# ─────────────────────────────────────────────────────────────────────────────
# 3. TriageVitalMiddleware (WSGI integration)
# ─────────────────────────────────────────────────────────────────────────────

class TriageVitalMiddlewareTests(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        # get_response returns a sentinel so we can detect passthrough
        self.sentinel = object()
        self.middleware = TriageVitalMiddleware(get_response=lambda r: self.sentinel)

    def _post_chat(self, message: str):
        req = self.factory.post(
            "/api/v1/ai/chat",
            data=json.dumps({"message": message}),
            content_type="application/json",
        )
        req.user = AnonymousUser()  # RequestFactory skips AuthMiddleware
        return self.middleware(req)

    # -- emergency interception --

    def test_french_emergency_returns_200_json(self):
        resp = self._post_chat("Je suis inconscient, j'ai du mal à respirer")
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertTrue(data["is_emergency"])
        self.assertIn("timestamp", data)

    def test_darija_emergency_returns_darija_reply(self):
        resp = self._post_chat("3yyan bzaf ma3endouch l7al")
        data = json.loads(resp.content)
        self.assertTrue(data["is_emergency"])
        self.assertIn("141", data["reply"])  # Moroccan SAMU number

    # -- safe messages pass through --

    def test_safe_french_message_passes_through(self):
        resp = self._post_chat("Ma glycémie est à 140 ce matin.")
        self.assertIs(resp, self.sentinel)

    def test_non_post_always_passes_through(self):
        req = self.factory.get("/api/v1/ai/chat")
        req.user = AnonymousUser()
        resp = self.middleware(req)
        self.assertIs(resp, self.sentinel)

    def test_non_chat_path_passes_through(self):
        req = self.factory.post(
            "/api/v1/logs",
            data=json.dumps({"blood_sugar": 120}),
            content_type="application/json",
        )
        req.user = AnonymousUser()
        resp = self.middleware(req)
        self.assertIs(resp, self.sentinel)

    def test_malformed_json_body_passes_through(self):
        req = self.factory.post(
            "/api/v1/ai/chat",
            data=b"not json",
            content_type="application/json",
        )
        req.user = AnonymousUser()
        resp = self.middleware(req)
        self.assertIs(resp, self.sentinel)
