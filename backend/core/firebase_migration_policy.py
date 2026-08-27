"""Fail-closed policy for the temporary Firebase migration bridge.

Firebase is not IAMINA's canonical identity provider. Native Django/IAMINA auth
is authoritative. The migration bridge is disabled unless an operator opts in
explicitly for a controlled legacy-account migration window.
"""
from __future__ import annotations

import os

_TRUTHY = {"1", "true", "yes", "on"}


def firebase_migration_enabled() -> bool:
    """Return True only for an explicit operator opt-in."""
    return os.environ.get("ENABLE_FIREBASE_MIGRATION", "false").strip().lower() in _TRUTHY
