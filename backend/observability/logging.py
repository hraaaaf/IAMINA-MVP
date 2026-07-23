"""
JSON structured logger — placeholder for Phase 5.

When Phase 5 lands this module will expose:

- `JsonFormatter` — emits one JSON object per log record with a fixed
  schema (timestamp, level, logger, message, request_id, user_id,
  context). No PHI in logs, ever (cf. TEAM.md Security + Compliance).
- `configure_logging(LOGGING)` — mutates Django's LOGGING dict to plug
  the formatter into the console and file handlers.
- `bind_request_id(request_id)` — context-local getter/setter used by
  `amina/middleware/request_id.py`.

For now the module just holds a constant other code can reference so we
don't ship unused imports.
"""

#: Header name used to propagate request IDs between services and the client.
REQUEST_ID_HEADER = "X-Request-ID"
