import json

from django.http import JsonResponse, StreamingHttpResponse
from django.test import RequestFactory, override_settings

from core.emergency_operating_mode import SELF_CARE_ONLY, emergency_disclosure
from core.middleware.emergency_operating_mode import EmergencyOperatingModeMiddleware


def test_json_emergency_response_is_decorated():
    request = RequestFactory().post(
        "/api/v1/ai/voice",
        data=json.dumps({"message": "glycémie 35"}),
        content_type="application/json",
    )
    middleware = EmergencyOperatingModeMiddleware(
        lambda req: JsonResponse({"reply": "Urgence.", "is_emergency": True})
    )

    response = middleware(request)
    payload = json.loads(response.content)
    assert payload["emergency_operating_mode"] == SELF_CARE_ONLY
    assert payload["human_monitoring"] is False
    assert emergency_disclosure("fr") in payload["reply"]


def test_non_emergency_json_response_is_untouched():
    request = RequestFactory().get("/health")
    middleware = EmergencyOperatingModeMiddleware(
        lambda req: JsonResponse({"status": "ok", "is_emergency": False})
    )

    response = middleware(request)
    assert json.loads(response.content) == {"status": "ok", "is_emergency": False}


def test_urgent_sse_first_event_gets_disclosure_and_metadata():
    request = RequestFactory().get(
        "/api/v1/ai/chat/stream",
        {"message": "glycémie 35"},
    )

    def get_response(req):
        return StreamingHttpResponse(
            iter(
                (
                    'data: {"token": "Alerte critique."}\n\n',
                    "data: [DONE]\n\n",
                )
            ),
            content_type="text/event-stream",
        )

    response = EmergencyOperatingModeMiddleware(get_response)(request)
    body = b"".join(response.streaming_content).decode()
    first = next(line for line in body.splitlines() if line.startswith("data: {"))
    event = json.loads(first.removeprefix("data: "))
    assert emergency_disclosure("fr") in event["token"]
    assert event["emergency_operating_mode"] == SELF_CARE_ONLY
    assert event["human_monitoring"] is False


def test_nonurgent_sse_is_not_modified():
    request = RequestFactory().get(
        "/api/v1/ai/chat/stream",
        {"message": "Comment conserver l'insuline ?"},
    )
    original = 'data: {"token": "Réponse."}\n\n'
    middleware = EmergencyOperatingModeMiddleware(
        lambda req: StreamingHttpResponse(iter((original,)), content_type="text/event-stream")
    )

    response = middleware(request)
    assert b"".join(response.streaming_content).decode() == original


def test_middleware_is_registered_outside_triage_boundary(settings):
    emergency_path = "core.middleware.emergency_operating_mode.EmergencyOperatingModeMiddleware"
    triage_path = "core.middleware.triage_vital.TriageVitalMiddleware"
    assert emergency_path in settings.MIDDLEWARE
    assert settings.MIDDLEWARE.index(emergency_path) < settings.MIDDLEWARE.index(triage_path)
