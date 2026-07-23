"""
P3 Thinking Mode — tests.

Covers:
- BaseLLMProvider.think() default delegates to complete()
- FallbackProvider.think() returns ("", non_empty_string)
- QuotaExhaustedProvider.think() returns ("", non_empty_string)
- GuardedGeminiProvider.think() delegates to inner provider
- think_before_reply() always returns a string (even if empty)
"""
from dataclasses import dataclass, field
from typing import Optional
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase, override_settings

from llm.base import BaseLLMProvider, LLMResponse
from llm.fallback import FallbackProvider, QuotaExhaustedProvider

# ──────────────────────────────────────────────────────────────────────────────
# Helpers / minimal stubs
# ──────────────────────────────────────────────────────────────────────────────

class _ConcreteProvider(BaseLLMProvider):
    """Minimal concrete provider that exercises the BaseLLMProvider.think() default."""

    def complete(self, system: str, user: str) -> LLMResponse:
        return LLMResponse(content="base complete response", provider="test")


@dataclass
class _FakeMemory:
    patient_id: int = 1
    emotional_signals: list = field(default_factory=list)


@dataclass
class _FakeDeepMemory:
    patient_id: int = 1
    relationship_stage: str = "new"
    communication_style: str = "unknown"


@dataclass
class _FakeState:
    satisfaction: float = 0.5
    concern_level: float = 0.3
    engagement: float = 0.6
    clinical_mood: str = "watchful"
    next_intention: str = "support patient"
    self_note: str = ""


@dataclass
class _FakeCtx:
    pivot_text: str = ""
    tir_pct: Optional[float] = 72.0
    cv_pct: Optional[float] = 33.0
    pattern_codes: list = field(default_factory=lambda: ["PATTERN_A"])
    has_sufficient_data: bool = True
    tir_trend: dict = field(default_factory=dict)


# ──────────────────────────────────────────────────────────────────────────────
# BaseLLMProvider.think() default behaviour
# ──────────────────────────────────────────────────────────────────────────────

class BaseProviderThinkTest(SimpleTestCase):
    """BaseLLMProvider.think() default implementation delegates to complete()."""

    def test_think_returns_tuple(self):
        provider = _ConcreteProvider()
        result = provider.think(system="sys", user="user msg")
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)

    def test_think_first_element_is_empty_string(self):
        """Default implementation has no thinking — first element must be ''."""
        provider = _ConcreteProvider()
        thinking, _ = provider.think(system="sys", user="user msg")
        self.assertEqual(thinking, "")

    def test_think_second_element_matches_complete_content(self):
        """Response must match what complete() returns."""
        provider = _ConcreteProvider()
        _, response = provider.think(system="sys", user="user msg")
        expected = provider.complete(system="sys", user="user msg").content
        self.assertEqual(response, expected)

    def test_think_response_is_non_empty(self):
        provider = _ConcreteProvider()
        _, response = provider.think(system="sys", user="user msg")
        self.assertGreater(len(response), 0)


# ──────────────────────────────────────────────────────────────────────────────
# FallbackProvider.think()
# ──────────────────────────────────────────────────────────────────────────────

class FallbackProviderThinkTest(SimpleTestCase):

    def test_think_returns_tuple(self):
        provider = FallbackProvider()
        result = provider.think(system="chat assistant", user="bonjour")
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)

    def test_think_thinking_is_empty(self):
        """FallbackProvider has no native thinking — first element must be ''."""
        provider = FallbackProvider()
        thinking, _ = provider.think(system="chat assistant", user="bonjour")
        self.assertEqual(thinking, "")

    def test_think_response_is_non_empty_string(self):
        provider = FallbackProvider()
        _, response = provider.think(system="chat assistant", user="bonjour")
        self.assertIsInstance(response, str)
        self.assertGreater(len(response), 0)


# ──────────────────────────────────────────────────────────────────────────────
# QuotaExhaustedProvider.think()
# ──────────────────────────────────────────────────────────────────────────────

class QuotaExhaustedProviderThinkTest(SimpleTestCase):

    def test_think_returns_tuple(self):
        provider = QuotaExhaustedProvider()
        result = provider.think(system="chat assistant", user="bonjour")
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)

    def test_think_thinking_is_empty(self):
        provider = QuotaExhaustedProvider()
        thinking, _ = provider.think(system="chat assistant", user="bonjour")
        self.assertEqual(thinking, "")

    def test_think_response_is_non_empty_string(self):
        provider = QuotaExhaustedProvider()
        _, response = provider.think(system="chat assistant", user="bonjour")
        self.assertIsInstance(response, str)
        self.assertGreater(len(response), 0)


# ──────────────────────────────────────────────────────────────────────────────
# GuardedGeminiProvider.think() — quota guard delegation
# ──────────────────────────────────────────────────────────────────────────────

class GuardedGeminiProviderThinkTest(SimpleTestCase):

    def _make_guarded(self, inner=None):
        from llm.rate_guard import GuardedGeminiProvider
        if inner is None:
            inner = FallbackProvider()
        return GuardedGeminiProvider(inner)

    def test_think_delegates_to_inner_when_quota_available(self):
        """When quota is available, think() must delegate to the inner provider."""
        inner = MagicMock()
        inner.think.return_value = ("some thinking", "some response")
        inner.complete.return_value = LLMResponse(content="fallback", provider="mock")

        guarded = self._make_guarded(inner)
        with patch("llm.rate_guard.should_use_gemini", return_value=True):
            thinking, response = guarded.think(system="sys", user="user")

        inner.think.assert_called_once_with("sys", "user")
        self.assertEqual(thinking, "some thinking")
        self.assertEqual(response, "some response")

    def test_think_returns_quota_message_when_cap_hit(self):
        """When quota is exhausted, think() returns the quota-exhausted message."""
        inner = MagicMock()
        guarded = self._make_guarded(inner)
        with patch("llm.rate_guard.should_use_gemini", return_value=False):
            thinking, response = guarded.think(system="sys", user="user")

        self.assertEqual(thinking, "")
        self.assertIsInstance(response, str)
        self.assertGreater(len(response), 0)
        # Inner provider must NOT be called when quota is exhausted
        inner.think.assert_not_called()

    def test_think_handles_quota_error_gracefully(self):
        """A real 429 from inner.think() must fast-forward the counter and not raise."""
        inner = MagicMock()
        inner.think.side_effect = RuntimeError("429 RESOURCE_EXHAUSTED quota exceeded")

        guarded = self._make_guarded(inner)
        with patch("llm.rate_guard.should_use_gemini", return_value=True), \
             patch("llm.rate_guard._mark_cap_reached") as mock_mark:
            thinking, response = guarded.think(system="sys", user="user")

        mock_mark.assert_called_once()
        self.assertEqual(thinking, "")
        self.assertIsInstance(response, str)

    def test_think_handles_non_quota_error_gracefully(self):
        """A non-quota exception must be swallowed — think() must never crash."""
        inner = MagicMock()
        inner.think.side_effect = RuntimeError("network timeout")

        guarded = self._make_guarded(inner)
        with patch("llm.rate_guard.should_use_gemini", return_value=True):
            thinking, response = guarded.think(system="sys", user="user")

        self.assertEqual(thinking, "")
        self.assertIsInstance(response, str)

    def test_think_increments_counter_on_success(self):
        """Successful think() must increment the Gemini call counter."""
        inner = MagicMock()
        inner.think.return_value = ("thinking", "response")

        guarded = self._make_guarded(inner)
        with patch("llm.rate_guard.should_use_gemini", return_value=True), \
             patch("llm.rate_guard.record_gemini_call") as mock_record:
            guarded.think(system="sys", user="user")

        mock_record.assert_called_once()


# ──────────────────────────────────────────────────────────────────────────────
# think_before_reply()
# ──────────────────────────────────────────────────────────────────────────────

class ThinkBeforeReplyTest(SimpleTestCase):

    def _call(self, llm=None, message="Je suis fatigué de gérer mon diabète"):
        from companion.thinker import think_before_reply
        if llm is None:
            llm = FallbackProvider()
        memory = _FakeMemory()
        deep = _FakeDeepMemory()
        state = _FakeState()
        ctx = _FakeCtx()
        return think_before_reply(message, memory, deep, state, ctx, llm, "fr")

    def test_returns_string(self):
        result = self._call()
        self.assertIsInstance(result, str)

    def test_returns_empty_string_for_fallback_provider(self):
        """FallbackProvider has no thinking — think_before_reply returns ''."""
        result = self._call(llm=FallbackProvider())
        self.assertEqual(result, "")

    def test_with_mock_llm_returning_thinking(self):
        """When LLM returns thinking, think_before_reply forwards it."""
        llm = MagicMock()
        llm.think.return_value = ("Je pense que ce patient est épuisé.", "réponse")
        result = self._call(llm=llm)
        self.assertEqual(result, "Je pense que ce patient est épuisé.")

    def test_with_mock_llm_returning_empty_thinking(self):
        """When LLM returns empty thinking, think_before_reply returns ''."""
        llm = MagicMock()
        llm.think.return_value = ("", "réponse finale")
        result = self._call(llm=llm)
        self.assertEqual(result, "")

    def test_never_crashes_when_llm_raises(self):
        """think_before_reply must never propagate exceptions."""
        llm = MagicMock()
        llm.think.side_effect = RuntimeError("unexpected LLM failure")
        result = self._call(llm=llm)
        self.assertIsInstance(result, str)

    def test_with_emotional_signals_in_memory(self):
        """Works correctly when memory.emotional_signals is populated."""
        from companion.thinker import think_before_reply
        llm = MagicMock()
        llm.think.return_value = ("réflexion interne", "bonne réponse")
        memory = _FakeMemory(emotional_signals=["fatigué", "découragé", "inquiet"])
        deep = _FakeDeepMemory(relationship_stage="trusted", communication_style="warm")
        state = _FakeState(satisfaction=0.3, concern_level=0.8)
        ctx = _FakeCtx(tir_pct=55.0, cv_pct=42.0, pattern_codes=["HYPO_RISK", "CV_HIGH"])
        result = think_before_reply("C'est trop dur", memory, deep, state, ctx, llm, "ar-MA")
        self.assertEqual(result, "réflexion interne")
        llm.think.assert_called_once()

    def test_llm_think_called_with_correct_args_structure(self):
        """think() must be called with a system string and a user prompt string."""
        from companion.thinker import think_before_reply
        llm = MagicMock()
        llm.think.return_value = ("", "ok")
        memory = _FakeMemory()
        deep = _FakeDeepMemory()
        state = _FakeState()
        ctx = _FakeCtx()
        think_before_reply("bonjour", memory, deep, state, ctx, llm, "fr")
        llm.think.assert_called_once()
        call_args = llm.think.call_args
        system_arg = call_args[0][0] if call_args[0] else call_args[1]["system"]
        user_arg = call_args[0][1] if len(call_args[0]) > 1 else call_args[1]["user"]
        self.assertIsInstance(system_arg, str)
        self.assertIsInstance(user_arg, str)
        self.assertIn("bonjour", user_arg)

    def test_raw_first_name_never_reaches_llm(self):
        """
        PHI regression guard: think_before_reply receives safe_message (already
        pseudonymised by the caller). If the caller passes a pseudonymised string,
        the raw first_name must NOT appear in what reaches llm.think().
        """
        from companion.thinker import think_before_reply
        from llm.pseudonymizer import PHIPseudonymizer

        first_name = "Fatima"
        raw_message = f"Salam, ana {first_name}, kan3ayen bzaf"

        # Simulate what conversation.py does before calling think_before_reply
        pseudo = PHIPseudonymizer()
        _, safe_message = pseudo.mask_patient_identity(first_name, raw_message)
        self.assertNotIn(first_name, safe_message)  # precondition

        llm = MagicMock()
        llm.think.return_value = ("some thinking", "reply")
        memory = _FakeMemory()
        deep = _FakeDeepMemory()
        state = _FakeState()
        ctx = _FakeCtx()

        think_before_reply(safe_message, memory, deep, state, ctx, llm, "ar-MA")

        llm.think.assert_called_once()
        call_args = llm.think.call_args
        user_arg = call_args[0][1] if len(call_args[0]) > 1 else call_args[1]["user"]
        self.assertNotIn(first_name, user_arg, "Raw first_name leaked into LLM think() call")
