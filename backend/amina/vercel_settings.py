"""Vercel-specific production settings for IAMINA backend."""
from __future__ import annotations

import os

import dj_database_url

from .settings import *  # noqa: F403,F401

if DEBUG:  # noqa: F405
    raise ValueError("IAMINA Vercel backend requires DEBUG=False")

_database_url = os.environ.get("DATABASE_URL", "").strip()
if not _database_url:
    raise ValueError("DATABASE_URL is required on Vercel; SQLite fallback is forbidden")

DATABASES = {  # noqa: F405
    "default": dj_database_url.parse(
        _database_url,
        conn_max_age=0,
    )
}

# Vercel terminates TLS before invoking the Django function.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Admit only the deployment host Vercel exposes for this exact deployment.
_vercel_url = os.environ.get("VERCEL_URL", "").strip().lower()
if _vercel_url:
    if not _vercel_url.endswith(".vercel.app"):
        raise ValueError("Unexpected VERCEL_URL host")
    if _vercel_url not in ALLOWED_HOSTS:  # noqa: F405
        ALLOWED_HOSTS.append(_vercel_url)  # noqa: F405

# The stable production alias remains explicit through ALLOWED_HOSTS env.
