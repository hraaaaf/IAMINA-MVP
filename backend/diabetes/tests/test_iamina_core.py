"""
IAmina Core Unit Tests
======================
Tests for reactor.py, narrator.py, and memory.py modules.
Uses unittest.mock to isolate from LLM, Redis, and DB.
"""

from unittest.mock import MagicMock, patch

from django.contrib.auth.models import User
from django.test import TestCase

from companion.memory import IAminaMemory, _detect_emotional_signals
from companion.parser import parse_llm_json
from companion.reactor import _fallback, react

# ──────────────────────────────────────────────────────────────
# 1. MEMORY — Emotional signal detection & tone update
# ──────────────────────────────────────────────────────────────

class MemoryEmotionalSignalTest(TestCase):

    def _make_memory(self):
        return IAminaMemory(
            patient_id=999,
            current_tone="challenge",
        )

    def test_discouragement_keyword_triggers_gentle_tone(self):
        memory = self._make_memory()
        _detect_emotional_signals("J'en ai marre de tout noter", memory)
        self.assertIn("discouragement", memory.emotional_signals)
        self.assertEqual(memory.current_tone, "gentle")

    def test_fatigue_keyword_triggers_gentle_tone(self):
        memory = self._make_memory()
        _detect_emotional_signals("Je suis épuisé ce soir", memory)
        self.assertIn("fatigue", memory.emotional_signals)
        self.assertEqual(memory.current_tone, "gentle")

    def test_fear_keyword_triggers_gentle_tone(self):
        memory = self._make_memory()
        _detect_emotional_signals("J'ai peur de faire une hypo", memory)
        self.assertIn("fear", memory.emotional_signals)
        self.assertEqual(memory.current_tone, "gentle")

    def test_neutral_message_does_not_change_tone(self):
        memory = self._make_memory()
        _detect_emotional_signals("Ma glycémie est à 1.2 g/L", memory)
        self.assertEqual(memory.emotional_signals, [])
        self.assertEqual(memory.current_tone, "challenge")

    def test_duplicate_signals_not_added(self):
        memory = self._make_memory()
        memory.emotional_signals = ["discouragement"]
        _detect_emotional_signals("J'en ai marre", memory)
        self.assertEqual(memory.emotional_signals.count("discouragement"), 1)

    def test_last_concern_stored(self):
        memory = self._make_memory()
        long_message = "J'ai peur " + "x" * 200
        _detect_emotional_signals(long_message, memory)
        self.assertIsNotNone(memory.last_concern)
        self.assertLessEqual(len(memory.last_concern), 100)

    def test_already_gentle_tone_not_changed(self):
        memory = self._make_memory()
        memory.current_tone = "gentle"
        _detect_emotional_signals("Je suis découragé", memory)
        self.assertEqual(memory.current_tone, "gentle")


# ──────────────────────────────────────────────────────────────
# 2. PARSER — JSON extraction robustness
# ──────────────────────────────────────────────────────────────

class ParserTest(TestCase):

    def test_clean_json_extraction(self):
        content = '{"reply": "Bonjour !", "concern_detected": ""}'
        result = parse_llm_json(content, ["reply", "concern_detected"])
        self.assertEqual(result["reply"], "Bonjour !")
        self.assertEqual(result["concern_detected"], "")

    def test_markdown_fence_stripped(self):
        content = '```json\n{"message": "Ok"}\n```'
        result = parse_llm_json(content, ["message"])
        self.assertEqual(result["message"], "Ok")

    def test_missing_field_returns_empty_string(self):
        content = '{"reply": "Ici"}'
        result = parse_llm_json(content, ["reply", "concern_detected"])
        self.assertEqual(result["concern_detected"], "")

    def test_malformed_json_never_crashes(self):
        content = "This is not JSON at all."
        result = parse_llm_json(content, ["reply", "tone_detected"])
        self.assertEqual(result["reply"], "")
        self.assertEqual(result["tone_detected"], "")

    def test_empty_string_never_crashes(self):
        result = parse_llm_json("", ["reply"])
        self.assertEqual(result["reply"], "")


# ──────────────────────────────────────────────────────────────
# 3. REACTOR — Post-log reaction
# ──────────────────────────────────────────────────────────────

class ReactorTest(TestCase):

    def _make_memory(self, tone="encouraging"):
        return IAminaMemory(patient_id=1, current_tone=tone)

    def _make_entry(self, blood_sugar=1.2, meal="pizza", notes=""):
        entry = MagicMock()
        entry.id = 42
        entry.blood_sugar = blood_sugar
        entry.meal_type = meal
        entry.notes = notes
        return entry

    def _make_llm(self, response_json: str):
        from llm.base import LLMResponse
        llm = MagicMock()
        llm.complete.return_value = LLMResponse(content=response_json, provider="mock")
        return llm

    def test_valid_response_returned(self):
        llm = self._make_llm('{"message": "C est noté !", "tone_detected": "encouraging"}')
        memory = self._make_memory()
        entry = self._make_entry()
        result = react(entry, memory, llm, "fr")
        self.assertEqual(result, "C est noté !")

    def test_tone_update_in_memory(self):
        llm = self._make_llm('{"message": "Ok", "tone_detected": "gentle"}')
        memory = self._make_memory(tone="challenge")
        entry = self._make_entry()
        react(entry, memory, llm, "fr")
        self.assertEqual(memory.current_tone, "gentle")

    def test_invalid_tone_not_persisted(self):
        llm = self._make_llm('{"message": "Ok", "tone_detected": "unknown_value"}')
        memory = self._make_memory(tone="encouraging")
        entry = self._make_entry()
        react(entry, memory, llm, "fr")
        self.assertEqual(memory.current_tone, "encouraging")

    def test_llm_failure_returns_fallback(self):
        llm = MagicMock()
        llm.complete.side_effect = RuntimeError("LLM unavailable")
        memory = self._make_memory(tone="gentle")
        entry = self._make_entry()
        result = react(entry, memory, llm, "fr")
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 5)

    def test_fallback_covers_all_tones(self):
        for tone in ("encouraging", "gentle", "challenge"):
            result = _fallback(tone)
            self.assertIsInstance(result, str)
            self.assertGreater(len(result), 0)

    def test_unknown_tone_fallback(self):
        result = _fallback("nonexistent")
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)

    def test_empty_reply_falls_back(self):
        llm = self._make_llm('{"message": "", "tone_detected": "encouraging"}')
        memory = self._make_memory()
        entry = self._make_entry()
        result = react(entry, memory, llm, "fr")
        self.assertGreater(len(result), 0)
