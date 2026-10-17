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

def validate_vercel_database_identity(database_url: str) -> None:
    """Fail closed before Django can use a mismapped Neon DATABASE_URL.

    Expected host/database are *non-secret* independent Vercel per-target
    settings. The URL (including credentials) must never appear in exceptions.
    Existing deployments retain their old environment until redeployed.
    """
    from urllib.parse import parse_qs, urlsplit

    iamina_env = os.environ.get("IAMINA_ENV", "").strip().lower()
    if iamina_env not in {"development", "production"}:
        raise ValueError("IAMINA_ENV must explicitly be development or production on Vercel")

    vercel_env = os.environ.get("VERCEL_ENV", "").strip().lower()
    if vercel_env not in {"production", "preview", "development"}:
        raise ValueError("VERCEL_ENV must explicitly identify the deployment target")

    expected_host = os.environ.get("IAMINA_EXPECTED_DB_HOST", "").strip().lower()
    expected_name = os.environ.get("IAMINA_EXPECTED_DB_NAME", "").strip()
    if not expected_host or not expected_name:
        raise ValueError("IAMINA_EXPECTED_DB_HOST and IAMINA_EXPECTED_DB_NAME are required")

    parsed = urlsplit(database_url)
    host = (parsed.hostname or "").lower()
    dbname = parsed.path.lstrip("/")
    # Neon offers direct and transaction-pooler names for the same compute.
    pooled_host = expected_host.replace(".c-", "-pooler.c-", 1)
    if host not in {expected_host, pooled_host} or dbname != expected_name:
        raise ValueError("DATABASE_URL does not match the expected Neon environment")

    tls_mode = parse_qs(parsed.query).get("sslmode", [])
    if len(tls_mode) != 1 or tls_mode[0] not in {"require", "verify-ca", "verify-full"}:
        raise ValueError("DATABASE_URL must explicitly enforce PostgreSQL TLS")

    # Clinical/patient production must authenticate the PostgreSQL server too.
    # sslmode=require encrypts, but does not ensure server identity (MITM).
    # The production connection additionally uses the system-trusted CA set.
    if iamina_env == "production":
        if vercel_env != "production":
            raise ValueError("IAMINA patient production cannot run on a Vercel preview")
        if tls_mode[0] != "verify-full":
            raise ValueError("IAMINA patient production requires sslmode=verify-full")
        if parse_qs(parsed.query).get("sslrootcert") != ["system"]:
            raise ValueError("IAMINA patient production requires sslrootcert=system")
