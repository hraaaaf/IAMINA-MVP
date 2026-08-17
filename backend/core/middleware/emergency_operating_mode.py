"""Response-boundary enforcement of patient-visible emergency and AI safety.

P0.6 makes this middleware a compatibility boundary, not a second wording owner:
any urgent JSON or SSE response is re-composed by ``core.emergency_response``.

Companion Convergence P0 also treats this boundary as the final pre-emission
safety gate for SSE tokens. Generated medical text is therefore sanitized before
it is yielded to the patient, regardless of the upstream streaming implementation.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Iterator

from django.http import HttpResponse, StreamingHttpResponse

from core.emergency_operating_mode import decorate_emergency_payload
from core.emergency_response import compose_emergency_for_patient
from core.input_safety import URGENT, evaluate_input_safety
from core.medical_safety import apply_no_prescription_policy


class EmergencyOperatingModeMiddleware:
    """Guarantee canonical emergency output and safe SSE at the final HTTP boundary."""

    def __init__(self, get_response) -> None:
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if isinstance(response, StreamingHttpResponse):
            message = request.GET.get("message", "")
            language = self._language_for_message(message)
            chunks: Iterable[bytes | str] = response.streaming_content
            if self._is_urgent_stream(response, message):
                chunks = self._decorate_stream(
                    chunks,
                    request=request,
                    message=message,
                )
            if self._is_sse(response):
                chunks = self._sanitize_stream(chunks, language=language)
            response.streaming_content = chunks
            return response

        if self._is_json(response):
            self._decorate_json_response(response, request)
        return response

    @staticmethod
    def _is_json(response: HttpResponse) -> bool:
        return response.get("Content-Type", "").split(";", 1)[0] == "application/json"

    @staticmethod
    def _is_sse(response: StreamingHttpResponse) -> bool:
        return response.get("Content-Type", "").split(";", 1)[0] == "text/event-stream"

    @classmethod
    def _is_urgent_stream(cls, response: StreamingHttpResponse, message: str) -> bool:
        return cls._is_sse(response) and evaluate_input_safety(message).action == URGENT

    def _decorate_json_response(self, response: HttpResponse, request) -> None:
        try:
            payload = json.loads(response.content.decode(response.charset or "utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError, AttributeError):
            return
        if not isinstance(payload, dict) or payload.get("is_emergency") is not True:
            return

        message = str(payload.get("transcript") or self._request_message(request))
        language = str(payload.get("reply_language") or self._language_for_message(message))
        decision = evaluate_input_safety(message)

        if decision.action == URGENT:
            canonical = compose_emergency_for_patient(
                decision,
                patient=getattr(request, "user", None),
                language=language,
                message=message,
            )
            timestamp = payload.get("timestamp")
            canonical_payload = canonical.as_payload(
                timestamp=str(timestamp) if timestamp is not None else None
            )
            decorated = dict(payload)
            decorated.update(canonical_payload)
        else:
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
            return "ar-MA"
        lowered = message.lower()
        if any(token in lowered.split() for token in ("wach", "ch7al", "sukkar", "dyal")):
            return "ar-MA"
        return "fr"

    @staticmethod
    def _decode_chunk(chunk: bytes | str) -> tuple[str, bool]:
        if isinstance(chunk, bytes):
            return chunk.decode("utf-8"), True
        return str(chunk), False

    def _sanitize_stream(
        self,
        chunks: Iterable[bytes | str],
        *,
        language: str,
    ) -> Iterator[bytes | str]:
        """Sanitize each patient-visible SSE token before it leaves Django."""
        for chunk in chunks:
            text, is_bytes = self._decode_chunk(chunk)
            if text.startswith("data: {"):
                raw = text[len("data: ") :].strip()
                try:
                    event = json.loads(raw)
                except json.JSONDecodeError:
                    pass
                else:
                    if isinstance(event, dict) and isinstance(event.get("token"), str):
                        safe_token = apply_no_prescription_policy(event["token"], language)
                        if safe_token != event["token"]:
                            event = dict(event)
                            event["token"] = safe_token
                            text = f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
            yield text.encode("utf-8") if is_bytes else text

    def _decorate_stream(
        self,
        chunks: Iterable[bytes | str],
        *,
        request,
        message: str,
    ) -> Iterator[bytes | str]:
        decision = evaluate_input_safety(message)
        if decision.action != URGENT:
            yield from chunks
            return

        canonical = compose_emergency_for_patient(
            decision,
            patient=getattr(request, "user", None),
            language=self._language_for_message(message),
            message=message,
        )
        canonical_event = canonical.as_stream_event()
        replaced_first_json = False

        for chunk in chunks:
            text, is_bytes = self._decode_chunk(chunk)
            if not replaced_first_json and text.startswith("data: {"):
                raw = text[len("data: ") :].strip()
                try:
                    event = json.loads(raw)
                except json.JSONDecodeError:
                    pass
                else:
                    if isinstance(event, dict) and isinstance(event.get("token"), str):
                        merged = dict(event)
                        merged.update(canonical_event)
                        text = f"data: {json.dumps(merged, ensure_ascii=False)}\n\n"
                        replaced_first_json = True
            yield text.encode("utf-8") if is_bytes else text