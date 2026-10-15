"""Synthetic chat error-log privacy tests. No external model or patient data."""
from types import SimpleNamespace
from unittest.mock import MagicMock, patch


def _request():
    return SimpleNamespace(user=SimpleNamespace(id=73))


def test_regular_chat_exception_is_not_copied_into_logs():
    from ai.api.v1.ai import ChatRequest, chat_with_amina

    canary = "synthetic_private_chat_text_in_exception"
    with (
        patch("ai.api.v1.ai._get_patient_language", return_value="fr"),
        patch("ai.api.v1.ai.evaluate_input_safety", return_value=SimpleNamespace(action="ALLOW")),
        patch("companion.core.IAmina", side_effect=RuntimeError(canary)),
        patch("companion.conversation.detect_language", return_value="fr"),
        patch("companion.conversation.is_governance_blocked_reply", return_value=False),
        patch("ai.api.v1.ai.track"),
        patch("ai.api.v1.ai.logger.error") as log_event,
    ):
        result = chat_with_amina.__wrapped__(_request(), ChatRequest(message="synthetic hello"))

    assert "erreur inattendue" in result["reply"]
    assert result["is_emergency"] is False
    log_event.assert_called_once()
    assert "RuntimeError" in str(log_event.call_args)
    assert canary not in str(log_event.call_args)
    assert "user=" not in str(log_event.call_args)


def test_streaming_chat_exception_keeps_sse_end_without_private_log():
    from ai.api.v1.ai import ChatRequest, chat_stream

    canary = "synthetic_private_sse_provider_exception"
    queryset = MagicMock()
    queryset.order_by.return_value = []
    with (
        patch("ai.api.v1.ai._get_patient_language", return_value="fr"),
        patch("ai.api.v1.ai.evaluate_input_safety", return_value=SimpleNamespace(action="ALLOW")),
        patch("ai.api.v1.ai.LogEntry.objects.filter", return_value=queryset),
        patch("ai.api.v1.ai.track"),
        patch("companion.router.route", side_effect=RuntimeError(canary)),
        patch("ai.api.v1.ai.logger.error") as log_event,
    ):
        response = chat_stream.__wrapped__(
            _request(), ChatRequest(message="synthetic question")
        )
        content = b"".join(response.streaming_content).decode()

    assert "Une erreur est survenue." in content
    assert "data: [DONE]" in content
    assert canary not in content
    log_event.assert_called_once()
    assert "RuntimeError" in str(log_event.call_args)
    assert canary not in str(log_event.call_args)
