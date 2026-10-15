"""V1-03: POST-only chat SSE, CSRF, safety and deferred patient egress.

Only synthetic prompts/accounts and mock providers are used. No vendor calls.
"""
import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest


def _request(patient_id=17):
    from django.test import RequestFactory

    request = RequestFactory().post("/api/v1/ai/chat/stream")
    request.user = SimpleNamespace(id=patient_id)
    return request


def _fake_entries():
    queryset = MagicMock()
    queryset.order_by.return_value = []
    return queryset


@pytest.mark.django_db
def test_get_query_no_longer_routes_or_processes_medical_message():
    from django.test import Client

    canary = "synthetic_private_glucose_in_query"
    with patch("companion.core.IAmina") as forbidden:
        response = Client().get("/api/v1/ai/chat/stream", {"message": canary})
    assert response.status_code == 405
    forbidden.assert_not_called()


@pytest.mark.django_db
def test_post_requires_authentication_before_creating_stream():
    from django.test import Client

    with patch("companion.core.IAmina") as forbidden:
        response = Client().post(
            "/api/v1/ai/chat/stream",
            data=json.dumps({"message": "synthetic hello"}),
            content_type="application/json",
        )
    assert response.status_code in (401, 403)
    forbidden.assert_not_called()


@pytest.mark.django_db
def test_session_cookie_plus_forged_bearer_cannot_bypass_csrf():
    from django.contrib.auth.models import User
    from django.test import Client

    user = User.objects.create_user(username="synthetic-sse-csrf")
    client = Client(enforce_csrf_checks=True)
    client.force_login(user)
    with patch("companion.core.IAmina") as forbidden:
        response = client.post(
            "/api/v1/ai/chat/stream",
            data=json.dumps({"message": "synthetic hello"}),
            content_type="application/json",
            HTTP_AUTHORIZATION="Bearer synthetic-forged-value",
        )
    assert response.status_code == 403
    forbidden.assert_not_called()


def test_post_urgent_is_canonical_sse_after_auth_without_model():
    from ai.api.v1.ai import ChatRequest, chat_stream
    from core.input_safety import URGENT, InputSafetyDecision
    from core.middleware.triage_vital import TriageVitalMiddleware

    request = _request()
    assert TriageVitalMiddleware(lambda req: None)._is_chat_endpoint(request) is False
    emergency = SimpleNamespace(
        as_stream_event=lambda: {"token": "synthetic canonical urgent", "is_emergency": True}
    )
    with (
        patch("ai.api.v1.ai._get_patient_language", return_value="fr"),
        patch("core.input_safety.evaluate_input_safety",
              return_value=InputSafetyDecision(URGENT, "glycemic_emergency")),
        patch("core.emergency_response.compose_emergency_for_patient",
              return_value=emergency) as compose,
        patch("ai.api.v1.ai.track"),
        patch("companion.core.IAmina") as forbidden,
    ):
        response = chat_stream.__wrapped__(request, ChatRequest(message="synthetic urgent"))
        data = b"".join(response.streaming_content).decode()
    compose.assert_called_once()
    assert '"is_emergency": true' in data
    assert "synthetic canonical urgent" in data
    assert "data: [DONE]" in data
    assert response["Cache-Control"] == "no-store"
    forbidden.assert_not_called()


def test_post_insulin_refusal_ends_stream_without_model():
    from ai.api.v1.ai import ChatRequest, chat_stream
    from core.input_safety import INSULIN_BLOCK, InputSafetyDecision

    with (
        patch("ai.api.v1.ai._get_patient_language", return_value="fr"),
        patch("core.input_safety.evaluate_input_safety",
              return_value=InputSafetyDecision(INSULIN_BLOCK, "insulin_prescription")),
        patch("ai.api.v1.ai.track"),
        patch("companion.core.IAmina") as forbidden,
    ):
        response = chat_stream.__wrapped__(_request(), ChatRequest(message="synthetic dose"))
        output = b"".join(response.streaming_content).decode()
    assert "data: [DONE]" in output
    assert response["Cache-Control"] == "no-store"
    forbidden.assert_not_called()


def test_deferred_generator_scopes_each_patient_and_resets_between_yields():
    from ai.api.v1.ai import ChatRequest, chat_stream
    from core.ai_egress import _CURRENT_EGRESS

    observed = []
    class FakeCompanion:
        def __init__(self, user, language):
            self.user = user
            self.deep = MagicMock()

        def stream_chat(self, message, context_days=14):
            scope = _CURRENT_EGRESS.get()
            observed.append((self.user.id, scope.patient_id, scope.purpose))
            yield "Bonjour."
            scope = _CURRENT_EGRESS.get()
            observed.append((self.user.id, scope.patient_id, scope.purpose))

    with (
        patch("ai.api.v1.ai._get_patient_language", return_value="fr"),
        patch("ai.api.v1.ai.LogEntry.objects.filter", return_value=_fake_entries()),
        patch("ai.api.v1.ai.track"),
        patch("companion.core.IAmina", FakeCompanion),
        patch("companion.router.route"),
        patch("companion.advice_filter.contains_medical_advice", return_value=False),
    ):
        a = chat_stream.__wrapped__(_request(17), ChatRequest(message="synthetic A"))
        b = chat_stream.__wrapped__(_request(23), ChatRequest(message="synthetic B"))
        assert _CURRENT_EGRESS.get() is None
        a_stream, b_stream = iter(a.streaming_content), iter(b.streaming_content)
        assert b"Bonjour." in next(a_stream)
        assert _CURRENT_EGRESS.get() is None
        assert b"Bonjour." in next(b_stream)
        assert _CURRENT_EGRESS.get() is None
        assert next(a_stream) == b"data: [DONE]\n\n"
        assert next(b_stream) == b"data: [DONE]\n\n"
        a.close()
        b.close()
    assert (17, 17, "companion_chat") in observed
    assert (23, 23, "companion_chat") in observed
    assert all(a == b for a, b, _ in observed)
    assert _CURRENT_EGRESS.get() is None


def test_without_consent_provider_cannot_enter_even_inside_deferred_scope():
    from ai.api.v1.ai import ChatRequest, chat_stream
    from core.ai_egress import AIConsentRequired, TEXT, _CURRENT_EGRESS, assert_ai_egress_allowed

    entered_provider = MagicMock()
    class FakeCompanion:
        def __init__(self, user, language):
            self.deep = MagicMock()

        def stream_chat(self, message, context_days=14):
            assert_ai_egress_allowed(TEXT)
            entered_provider()
            yield "must never be sent"

    with (
        patch("ai.api.v1.ai._get_patient_language", return_value="fr"),
        patch("ai.api.v1.ai.LogEntry.objects.filter", return_value=_fake_entries()),
        patch("ai.api.v1.ai.track"),
        patch("companion.core.IAmina", FakeCompanion),
        patch("companion.router.route"),
        patch("core.ai_egress._load_current_consent_profile",
              side_effect=AIConsentRequired("synthetic no consent")),
    ):
        response = chat_stream.__wrapped__(_request(), ChatRequest(message="synthetic chat"))
        body = b"".join(response.streaming_content).decode()
    entered_provider.assert_not_called()
    assert "Une erreur est survenue." in body
    assert "data: [DONE]" in body
    assert _CURRENT_EGRESS.get() is None
