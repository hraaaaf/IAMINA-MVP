import json
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from django.http import JsonResponse, StreamingHttpResponse
from django.test import RequestFactory

from companion.core import IAmina
from core.emergency_operating_mode import SELF_CARE_ONLY, emergency_disclosure
from core.emergency_response import (
    compose_emergency_for_patient,
    compose_emergency_response,
    fallback_emergency_locale,
)
from core.input_safety import ALLOW, URGENT, InputSafetyDecision, evaluate_input_safety
from core.locale import ResolvedLocale
from core.middleware.emergency_operating_mode import EmergencyOperatingModeMiddleware


def _confirmed_ma_locale() -> ResolvedLocale:
    return ResolvedLocale(
        country_code="MA",
        ui_language="fr",
        response_language="fr",
        script_preference="latin",
        transliteration_preference="none",
        dialect=None,
        glucose_unit="mg/dL",
        timezone=None,
        country_confirmed=True,
        timezone_confirmed=False,
    )


def test_canonical_composer_fails_closed_without_confirmed_country():
    response = compose_emergency_response(
        InputSafetyDecision(URGENT, "glycemic_emergency"),
        locale=fallback_emergency_locale("fr"),
    )

    assert response.is_emergency is True
    assert response.emergency_operating_mode == SELF_CARE_ONLY
    assert response.human_monitoring is False
    assert response.resources.country_specific is False
    assert response.resources.safe_message_code == "country_unconfirmed"
    assert response.resources.contacts == ()
    assert "pas de numéro d'urgence confirmé" in response.reply
    assert response.reply.count(emergency_disclosure("fr")) == 1


def test_canonical_composer_uses_only_confirmed_versioned_resources():
    response = compose_emergency_response(
        InputSafetyDecision(URGENT, "glycemic_emergency"),
        locale=_confirmed_ma_locale(),
    )

    assert response.resources.country_specific is True
    assert [(item.service, item.number) for item in response.resources.contacts] == [
        ("ambulance", "150"),
        ("fire", "150"),
        ("police", "190"),
        ("gendarmerie", "177"),
    ]
    assert "150" in response.reply
    assert "141" not in response.reply


def test_canonical_composer_rejects_nonurgent_decision():
    with pytest.raises(ValueError):
        compose_emergency_response(
            InputSafetyDecision(ALLOW),
            locale=fallback_emergency_locale("fr"),
        )


def test_json_boundary_replaces_legacy_emergency_reply_with_canonical_reply():
    request = RequestFactory().post(
        "/api/v1/ai/chat",
        data=json.dumps({"message": "glycémie 35"}),
        content_type="application/json",
    )
    middleware = EmergencyOperatingModeMiddleware(
        lambda req: JsonResponse(
            {
                "reply": "LEGACY EMERGENCY COPY",
                "is_emergency": True,
                "timestamp": "2026-08-12T10:00:00+01:00",
            }
        )
    )

    payload = json.loads(middleware(request).content)

    assert payload["reply"] != "LEGACY EMERGENCY COPY"
    assert payload["reply"].count(emergency_disclosure("fr")) == 1
    assert payload["emergency_operating_mode"] == SELF_CARE_ONLY
    assert payload["human_monitoring"] is False
    assert payload["emergency_reason"] == "glycemic_emergency"
    assert payload["emergency_resource_code"] == "country_unconfirmed"


def test_sse_boundary_replaces_legacy_first_event_with_canonical_event():
    request = RequestFactory().get(
        "/api/v1/ai/chat/stream",
        {"message": "glycémie 35"},
    )

    def get_response(req):
        return StreamingHttpResponse(
            iter(
                (
                    'data: {"token": "LEGACY EMERGENCY COPY"}\n\n',
                    "data: [DONE]\n\n",
                )
            ),
            content_type="text/event-stream",
        )

    response = EmergencyOperatingModeMiddleware(get_response)(request)
    body = b"".join(response.streaming_content).decode()
    first = next(line for line in body.splitlines() if line.startswith("data: {"))
    event = json.loads(first.removeprefix("data: "))

    assert event["token"] != "LEGACY EMERGENCY COPY"
    assert event["token"].count(emergency_disclosure("fr")) == 1
    assert event["emergency_operating_mode"] == SELF_CARE_ONLY
    assert event["human_monitoring"] is False
    assert event["emergency_reason"] == "glycemic_emergency"
    assert event["emergency_resource_code"] == "country_unconfirmed"


class _FakeDeep:
    def __init__(self):
        self.total_interactions = 0

    def evolve_relationship(self, signals):
        return None

    def save(self):
        return None


class _FakeMemory:
    emotional_signals = []

    def __init__(self):
        self.last_update = None

    def update_from_chat(self, message, reply):
        self.last_update = (message, reply)


def _direct_iamina() -> IAmina:
    instance = object.__new__(IAmina)
    instance.patient = SimpleNamespace(id=991)
    instance.language = "fr"
    instance.memory = _FakeMemory()
    instance.deep = _FakeDeep()
    return instance


def test_direct_companion_chat_uses_canonical_authority_before_legacy_conversation():
    instance = _direct_iamina()
    message = "glycémie 35"
    decision = evaluate_input_safety(message)
    expected = compose_emergency_for_patient(
        decision,
        patient=instance.patient,
        language="fr",
        message=message,
    ).reply

    with (
        patch("companion.core.get_conversation_store", return_value=None),
        patch("companion.core.chat", side_effect=AssertionError("legacy chat reached")),
    ):
        reply = instance.chat(message)

    assert reply == expected
    assert instance.memory.last_update == (message, expected)


def test_direct_companion_stream_uses_canonical_authority_before_legacy_stream():
    instance = _direct_iamina()
    message = "glycémie 35"
    decision = evaluate_input_safety(message)
    expected = compose_emergency_for_patient(
        decision,
        patient=instance.patient,
        language="fr",
        message=message,
    ).reply

    with (
        patch("companion.core.get_conversation_store", return_value=None),
        patch("companion.core.stream_chat", side_effect=AssertionError("legacy stream reached")),
    ):
        chunks = list(instance.stream_chat(message))

    assert chunks == [expected]
