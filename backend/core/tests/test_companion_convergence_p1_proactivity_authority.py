from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from companion import conversation
from core.contracts.domain_context import DomainContext


ROOT = Path(__file__).resolve().parents[2]
CONVERSATION = ROOT / "companion" / "conversation.py"
PROACTIVE_API = ROOT / "diabetes" / "api" / "v1" / "proactive.py"


def test_conversation_has_no_independent_proactive_emission_authority():
    source = CONVERSATION.read_text(encoding="utf-8")

    assert "_PROACTIVE_TEMPLATES" not in source
    assert "_PROACTIVE_DEFAULT" not in source
    assert "_inject_proactive_followup" not in source
    assert "is_first_message" not in source


def test_emotional_memory_remains_reactive_context_not_delivery_authority():
    source = CONVERSATION.read_text(encoding="utf-8")

    assert "memory.emotional_signals" in source
    assert "memory.last_concern" in source
    assert "_is_emotional(message)" in source
    assert "get_tone_instruction" in source


def test_governed_proactive_api_remains_the_delivery_authority():
    source = PROACTIVE_API.read_text(encoding="utf-8")

    assert "evaluate_proactive_insights(patient_id=request.user.id)" in source
    assert 'attention_budget: Literal["one_non_urgent_item_per_24h"]' in source
    assert 'router.post("/proactive-insights/evaluate/"' in source


class _Memory:
    patterns: list[str] = []
    emotional_signals = ["fatigue"]
    last_concern = "fatigue récente"

    def save(self):
        return None


class _Deep:
    def save(self):
        return None


class _LLM:
    def complete(self, system, user_prompt):
        return SimpleNamespace(content='{"reply":"Je suis là.","concern_detected":""}')


def test_prior_emotional_memory_cannot_emit_an_assistant_turn_before_user_message():
    patient = SimpleNamespace(id=991, first_name="")
    memory = _Memory()
    deep = _Deep()
    tone = SimpleNamespace(mode=SimpleNamespace(value="gentle"))

    with (
        patch("companion.conversation._recent_turns", return_value=[]),
        patch(
            "companion.conversation._get_context",
            return_value=DomainContext.empty(language="fr"),
        ),
        patch("companion.conversation.select_tone", return_value=tone),
        patch("companion.conversation.get_tone_instruction", return_value=""),
        patch(
            "companion.conversation.compute_state",
            return_value=SimpleNamespace(concern_level=0.0),
        ),
        patch("companion.conversation.state_to_prompt", return_value=""),
        patch("companion.conversation.apply_advice_throttle", side_effect=lambda reply, _: reply),
        patch("companion.conversation._append_turn") as append_turn,
    ):
        reply = conversation.chat(
            "Bonjour",
            memory=memory,
            deep=deep,
            llm=_LLM(),
            language="fr",
            patient=patient,
        )

    assert reply == "Je suis là."
    assert append_turn.call_args_list[0].args == (patient, "user", "Bonjour")
    assert append_turn.call_args_list[1].args == (patient, "assistant", "Je suis là.")
    assert len(append_turn.call_args_list) == 2
