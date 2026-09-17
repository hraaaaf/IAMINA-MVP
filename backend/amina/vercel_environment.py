"""Small helpers for Vercel environment-specific policy."""
from __future__ import annotations

import os


def is_vercel_production() -> bool:
    """Return True only for Vercel's production environment."""
    return os.environ.get("VERCEL_ENV", "").strip().lower() == "production"
