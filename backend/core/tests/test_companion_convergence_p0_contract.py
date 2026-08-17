from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CONVERSATION = ROOT / "companion" / "conversation.py"
AI_API = ROOT / "ai" / "api" / "v1" / "ai.py"


def test_conversation_has_no_local_emergency_copy_or_keyword_authority():
    source = CONVERSATION.read_text(encoding="utf-8")

    assert "_CHAT_EMERGENCY_FR" not in source
    assert "_CHAT_EMERGENCY_AR" not in source
    assert "def _is_chat_emergency" not in source
    assert "_EMERGENCY_KEYWORDS" not in source
    assert "compose_emergency_for_patient" in source


def test_stream_router_uses_canonical_emergency_composer():
    source = AI_API.read_text(encoding="utf-8")

    assert "compose_emergency_for_patient" in source
    assert "emergency_msg = (" not in source
    assert ".as_stream_event()" in source


def test_stream_router_filters_generated_sentence_before_patient_emission():
    source = AI_API.read_text(encoding="utf-8")

    helper_start = source.index("def _safe_patient_sentence")
    helper_end = source.index("\n\n", helper_start)
    helper = source[helper_start:helper_end]

    assert "apply_no_prescription_policy" in helper

    stream_start = source.index("def _event_generator")
    stream = source[stream_start:]
    assert "_safe_patient_sentence" in stream

    first_safe_call = stream.index("_safe_patient_sentence")
    first_token_yield = stream.index("yield f\"data: {json.dumps({'token':")
    assert first_safe_call < first_token_yield
