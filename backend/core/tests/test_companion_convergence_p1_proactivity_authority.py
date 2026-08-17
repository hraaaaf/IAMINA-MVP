from pathlib import Path


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
