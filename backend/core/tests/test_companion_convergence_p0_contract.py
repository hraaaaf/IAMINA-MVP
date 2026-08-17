import json
from pathlib import Path

from django.http import StreamingHttpResponse
from django.test import RequestFactory

from core import medical_safety
from core.middleware import emergency_operating_mode


ROOT = Path(__file__).resolve().parents[2]
CONVERSATION = ROOT / "companion" / "conversation.py"


def test_conversation_has_no_local_emergency_copy_or_keyword_authority():
    source = CONVERSATION.read_text(encoding="utf-8")

    assert "_CHAT_EMERGENCY_FR" not in source
    assert "_CHAT_EMERGENCY_AR" not in source
    assert "def _is_chat_emergency" not in source
    assert "_EMERGENCY_KEYWORDS" not in source
    assert "compose_emergency_for_patient" in source


def test_nonurgent_sse_forbidden_text_is_filtered_before_patient_emission():
    request = RequestFactory().get(
        "/api/v1/ai/chat/stream",
        {"message": "bonjour"},
    )

    unsafe = "Tu as sûrement quelque chose."

    def get_response(req):
        return StreamingHttpResponse(
            iter(
                (
                    f"data: {json.dumps({'token': unsafe})}\n\n",
                    "data: [DONE]\n\n",
                )
            ),
            content_type="text/event-stream",
        )

    middleware = emergency_operating_mode.EmergencyOperatingModeMiddleware(get_response)
    response = middleware(request)
    body = b"".join(response.streaming_content).decode()
    first = next(line for line in body.splitlines() if line.startswith("data: {"))
    event = json.loads(first.removeprefix("data: "))

    assert event["token"] == medical_safety.no_prescription_message("fr")
    assert unsafe not in body


def test_safe_nonurgent_sse_token_passes_through_unchanged():
    request = RequestFactory().get(
        "/api/v1/ai/chat/stream",
        {"message": "bonjour"},
    )
    safe = "Je peux t'aider à organiser tes observations."

    def get_response(req):
        return StreamingHttpResponse(
            iter(
                (
                    f"data: {json.dumps({'token': safe})}\n\n",
                    "data: [DONE]\n\n",
                )
            ),
            content_type="text/event-stream",
        )

    middleware = emergency_operating_mode.EmergencyOperatingModeMiddleware(get_response)
    response = middleware(request)
    body = b"".join(response.streaming_content).decode()
    first = next(line for line in body.splitlines() if line.startswith("data: {"))
    event = json.loads(first.removeprefix("data: "))

    assert event["token"] == safe
