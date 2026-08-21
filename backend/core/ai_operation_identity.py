"""Request-scoped, privacy-minimized identity for paid AI operations."""

from __future__ import annotations

import hashlib
import re
import secrets
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Iterator

_IDEMPOTENCY_RE = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")
_CURRENT_REQUEST_SEED: ContextVar[str | None] = ContextVar(
    "iamina_ai_operation_request_seed",
    default=None,
)
_CURRENT_CALL_INDEX: ContextVar[int] = ContextVar(
    "iamina_ai_operation_call_index",
    default=0,
)


class AIOperationIdentityDenied(ValueError):
    """Raised when a paid operation has no safe request identity."""


class InvalidIdempotencyKey(AIOperationIdentityDenied):
    """Raised only when the client-supplied idempotency header is invalid."""


@contextmanager
def ai_operation_request_scope(idempotency_key: str | None) -> Iterator[str]:
    """Bind one opaque request seed without retaining the raw client key."""
    if idempotency_key:
        if not _IDEMPOTENCY_RE.fullmatch(idempotency_key):
            raise InvalidIdempotencyKey("invalid Idempotency-Key header")
        seed = "client-sha256:" + hashlib.sha256(
            idempotency_key.encode("utf-8")
        ).hexdigest()
    else:
        seed = "server-nonce:" + secrets.token_hex(16)

    seed_token = _CURRENT_REQUEST_SEED.set(seed)
    index_token = _CURRENT_CALL_INDEX.set(0)
    try:
        yield seed
    finally:
        _CURRENT_CALL_INDEX.reset(index_token)
        _CURRENT_REQUEST_SEED.reset(seed_token)


def next_operation_reference(*, patient_id: int, purpose: str) -> str:
    """Return a stable-per-request call reference; raw inputs are never persisted."""
    seed = _CURRENT_REQUEST_SEED.get()
    if seed is None:
        raise AIOperationIdentityDenied(
            "paid AI operation attempted outside request identity scope"
        )
    if not isinstance(patient_id, int) or patient_id <= 0 or not purpose.strip():
        raise AIOperationIdentityDenied("valid patient and purpose are required")

    call_index = _CURRENT_CALL_INDEX.get() + 1
    _CURRENT_CALL_INDEX.set(call_index)
    return (
        f"patient={patient_id}|purpose={purpose}|request={seed}|call={call_index}"
    )
