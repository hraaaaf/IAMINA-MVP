"""
RGPD Art. 17 — account deletion hook registry.

Modules register cleanup callbacks here. All hooks are called before the
Django User is deleted. Any hook failure blocks the deletion (RGPD compliance).
"""
from __future__ import annotations

import logging
from typing import Callable

logger = logging.getLogger(__name__)

_hooks: list[Callable[[int, str], None]] = []


def register_account_delete_hook(fn: Callable[[int, str], None]) -> None:
    """Append a cleanup hook. Hooks run in registration order on account deletion."""
    _hooks.append(fn)


def run_account_delete_hooks(patient_id: int, firebase_uid: str) -> None:
    """
    Execute all registered hooks.

    Any failed hook blocks erasure, but exception details are never written
    to logs or included in a response; upstream errors may contain patient data.
    Continue trying independent hooks, then raise a sanitized failure count.
    """
    failures = 0
    for index, hook in enumerate(_hooks):
        try:
            hook(patient_id, firebase_uid)
        except Exception:
            failures += 1
            # Only a stable registry index is logged. Never include hook repr,
            # exception string, traceback, Firebase UID, or patient content.
            logger.error("account_delete_hook_failed index=%d", index)
    if failures:
        raise RuntimeError(f"Account delete hooks failed (count={failures})")
