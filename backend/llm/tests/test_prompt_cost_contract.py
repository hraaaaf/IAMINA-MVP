from companion.narrator_prompts import CHAT_USER
from llm.gemini import _MAX_OUTPUT_TOKENS as GEMINI_MAX_OUTPUT_TOKENS
from llm.kimi import _MAX_OUTPUT_TOKENS as KIMI_MAX_OUTPUT_TOKENS


def test_narrator_schema_only_requests_consumed_reply_field():
    rendered = CHAT_USER.format(memory="m", history="h", message="x")
    assert '"reply"' in rendered
    assert "concern_detected" not in rendered


def test_routine_provider_output_ceiling_matches_short_reply_contract():
    assert GEMINI_MAX_OUTPUT_TOKENS == 160
    assert KIMI_MAX_OUTPUT_TOKENS == 160
