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

    Any hook exception is collected and, after all hooks run, a RuntimeError
    is raised with the full error list (RGPD Article 17 — hook failure blocks deletion).
    """
    errors: list[str] = []
    for hook in _hooks:
        try:
            hook(patient_id, firebase_uid)
        except Exception as e:
            logger.error(
                "account_delete_hook_failed hook=%s err=%s",
                hook.__name__ if hasattr(hook, "__name__") else repr(hook),
                e,
            )
            errors.append(str(e))
    if errors:
        raise RuntimeError(f"Account delete hooks failed: {errors}")
