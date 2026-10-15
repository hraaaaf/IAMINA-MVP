"""Protect emergency voice triage and STT-failure logs from transcript leaks.

Synthetic direct handler tests exercise its clinical branches without triggering
external AI egress, changing patient consent, or bypassing live authorization.
"""
from types import SimpleNamespace
from unittest.mock import patch

from ai.api.v1.voice import voice_chat
from core.input_safety import InputSafetyDecision, URGENT
from media.voice import TranscriptionError


def _fake_voice_request():
    request = SimpleNamespace(user=SimpleNamespace(id=73))
    audio = SimpleNamespace(
        content_type="audio/mp4",
        read=lambda: b"synthetic-audio-never-sent",
    )
    return request, audio


def test_emergency_voice_reply_preserved_without_transcript_in_logs():
    canary = "synthetic_confidential_patient_speech"
    request, audio = _fake_voice_request()
    with (
        patch("ai.api.v1.voice._get_language", return_value="fr"),
        patch("ai.api.v1.voice.transcribe", return_value=canary),
        patch(
            "core.input_safety.evaluate_input_safety",
            return_value=InputSafetyDecision(URGENT, "glycemic_emergency"),
        ),
        patch(
            "core.middleware.triage_vital._pick_emergency_response",
            return_value={"reply": "synthetic emergency response", "is_emergency": True},
        ),
        patch("ai.api.v1.voice.logger.critical") as logged_event,
    ):
        response = voice_chat.__wrapped__(request, audio)

    assert response["is_emergency"] is True
    assert response["transcript"] == canary
    logged_event.assert_called_once()
    assert "EMERGENCY" in str(logged_event.call_args)
    assert canary not in str(logged_event.call_args)
    assert "user_id" not in str(logged_event.call_args)
    assert "snippet" not in str(logged_event.call_args)


def test_stt_failure_retains_safe_reply_without_exception_or_user_in_logs():
    canary = "synthetic_secret_inside_provider_exception"
    request, audio = _fake_voice_request()
    with (
        patch("ai.api.v1.voice._get_language", return_value="fr"),
        patch(
            "ai.api.v1.voice.transcribe",
            side_effect=TranscriptionError(canary),
        ),
        patch("ai.api.v1.voice.logger.warning") as logged_event,
    ):
        response = voice_chat.__wrapped__(request, audio)

    assert response["is_emergency"] is False
    assert response["reply"]
    logged_event.assert_called_once()
    assert "TranscriptionError" in str(logged_event.call_args)
    assert canary not in str(logged_event.call_args)
    assert "user=" not in str(logged_event.call_args)
