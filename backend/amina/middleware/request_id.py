"""
Request-ID middleware — not yet active.

Phase 5 scaffolding. When wired, the middleware will:

- Read `X-Request-ID` from the incoming request or generate a UUID4.
- Stash it in a `contextvars.ContextVar` so the JSON logger
  (`observability.logging.JsonFormatter`) picks it up for every
  record produced during the request.
- Echo it back on the response so browser devtools and downstream
  services can correlate the same call end-to-end.

Leave the class here but unregistered in `settings.MIDDLEWARE` — Phase 5
turns it on alongside the JSON formatter.
"""

import uuid

from observability.logging import REQUEST_ID_HEADER


class RequestIdMiddleware:
    """No-op until Phase 5. Structure kept so settings wiring is trivial later."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request_id = request.headers.get(REQUEST_ID_HEADER) or uuid.uuid4().hex
        request.request_id = request_id
        response = self.get_response(request)
        response[REQUEST_ID_HEADER] = request_id
        return response
