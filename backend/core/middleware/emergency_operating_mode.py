"""Response-boundary enforcement of the pilot emergency operating mode."""

from __future__ import annotations

import json
from collections.abc import Iterable, Iterator

from django.http import HttpResponse, StreamingHttpResponse

from core.emergency_operating_mode import (
    PILOT_EMERGENCY_POLICY,
    append_emergency_disclosure,
    decorate_emergency_payload,
)
from core.input_safety import URGENT, evaluate_input_safety


class EmergencyOperatingModeMiddleware:
    """Decorate every user-facing emergency response with truthful mode details."""

    def __init__(self, get_response) -> None:
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if isinstance(response, StreamingHttpResponse):
            if self._is_urgent_stream(request, response):
                response.streaming_content = self._decorate_stream(
                    response.streaming_content,
                    language=self._language_for_message(request.GET.get("message", "")),
                )
            return response

        if self._is_json(response):
            self._decorate_json_response(response, request)
        return response

    @staticmethod
    def _is_json(response: HttpResponse) -> bool:
        return response.get("Content-Type", "").split(";", 1)[0] == "application/json"

    @staticmethod
    def _is_urgent_stream(request, response: StreamingHttpResponse) -> bool:
        content_type = response.get("Content-Type", "").split(";", 1)[0]
        if content_type != "text/event-stream":
            return False
        message = request.GET.get("message", "")
        return evaluate_input_safety(message).action == URGENT

    def _decorate_json_response(self, response: HttpResponse, request) -> None:
        try:
            payload = json.loads(response.content.decode(response.charset or "utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError, AttributeError):
            return
        if not isinstance(payload, dict) or payload.get("is_emergency") is not True:
            return

        language = self._language_for_message(
            str(payload.get("transcript") or self._request_message(request))
        )
        decorated = decorate_emergency_payload(payload, language=language)
        encoded = json.dumps(decorated, ensure_ascii=False).encode(response.charset or "utf-8")
        response.content = encoded
        response["Content-Length"] = str(len(encoded))

    @staticmethod
    def _request_message(request) -> str:
        if request.method == "GET":
            return request.GET.get("message", "")
        try:
            payload = json.loads(request.body or b"{}")
        except (json.JSONDecodeError, UnicodeDecodeError):
            return ""
        return str(payload.get("message", "")) if isinstance(payload, dict) else ""

    @staticmethod
    def _language_for_message(message: str) -> str:
        if any("\u0600" <= char <= "\u06ff" for char in message):
            return "ar"
        lowered = message.lower()
        if any(token in lowered.split() for token in ("wach", "ch7al", "sukkar", "dyal")):
            return "ar-MA"
        return "fr"

    @staticmethod
    def _decorate_stream(
        chunks: Iterable[bytes | str],
        *,
        language: str,
    ) -> Iterator[bytes | str]:
        decorated_first_json = False
        for chunk in chunks:
            is_bytes = isinstance(chunk, bytes)
            text = chunk.decode("utf-8") if is_bytes else str(chunk)
            if not decorated_first_json and text.startswith("data: {"):
                raw = text[len("data: ") :].strip()
                try:
                    event = json.loads(raw)
                except json.JSONDecodeError:
                    pass
                else:
                    if isinstance(event, dict) and isinstance(event.get("token"), str):
                        event["token"] = append_emergency_disclosure(event["token"], language)
                        event["emergency_operating_mode"] = PILOT_EMERGENCY_POLICY.mode
                        event["human_monitoring"] = PILOT_EMERGENCY_POLICY.human_monitoring
                        text = f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
                        decorated_first_json = True
            yield text.encode("utf-8") if is_bytes else text
