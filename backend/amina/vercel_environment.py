"""Small helpers for Vercel environment-specific policy."""
from __future__ import annotations

import os


def is_vercel_production() -> bool:
    """Return True only for an explicitly production IAMINA runtime on Vercel.

    Vercel's own "production" target is also used for the shared dev/test app,
    so it must not by itself enable production-only IAMINA requirements.
    """
    vercel_env = os.environ.get("VERCEL_ENV", "").strip().lower()
    iamina_env = os.environ.get("IAMINA_ENV", "development").strip().lower()
    return vercel_env == "production" and iamina_env == "production"
