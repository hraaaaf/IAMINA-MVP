"""W01-B: fail-closed Vercel Django settings preflight, with fake PostgreSQL URL.

Only imports settings in isolated subprocesses. No cloud connection, SQL,
patient data, SMTP message or deployment occurs.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
FAKE_PG = "postgresql://w01_synthetic:w01_synthetic@127.0.0.1:5432/w01_synthetic"

DEFAULT_ENV = {
    "SECRET_KEY": "w01-ci-not-for-prod",
    "DEBUG": "False",
    "DATABASE_URL": FAKE_PG,
    "ALLOWED_HOSTS": "iamina-certified.vercel.app",
    "CORS_ALLOWED_ORIGINS": "https://iamina-review.vercel.app",
    "CSRF_TRUSTED_ORIGINS": "https://iamina-review.vercel.app",
    "VERCEL": "1",
    "VERCEL_ENV": "production",
    # Vercel target=production != IAMINA production authorization.
    "IAMINA_ENV": "development",
}
PROBE = (
    "from amina import vercel_settings as s; "
    "assert s.DATABASES['default']['ENGINE'] == 'django.db.backends.postgresql'; "
    "assert s.DATABASES['default']['CONN_MAX_AGE'] == 0; "
    "assert s.DATABASES['default']['NAME'] == 'w01_synthetic'; "
    "assert s.DEBUG is False; "
    "assert s.SECURE_SSL_REDIRECT is True; "
    "print('W01-B Vercel settings import OK')"
)


def _check_settings(overrides: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    # Do not inherit sensitive runtime or SMTP config into preflight.
    for key in [
        "IAMINA_ENV", "VERCEL_ENV", "VERCEL", "DATABASE_URL",
        "DEBUG", "SECRET_KEY", "ALLOWED_HOSTS", "CORS_ALLOWED_ORIGINS",
        "CSRF_TRUSTED_ORIGINS", "EMAIL_BACKEND", "EMAIL_HOST",
        "EMAIL_PORT", "EMAIL_HOST_USER", "EMAIL_HOST_PASSWORD",
        "DEFAULT_FROM_EMAIL", "PASSWORD_RESET_FRONTEND_URL",
    ]:
        env.pop(key, None)
    env.update(DEFAULT_ENV)
    env.update(overrides or {})
    return subprocess.run(
        [sys.executable, "-c", PROBE],
        cwd=BACKEND,
        env=env,
        text=True,
        capture_output=True,
        timeout=15,
        check=False,
    )


def test_valid_backend_vercel_settings_use_short_postgres_connections():
    result = _check_settings()
    assert result.returncode == 0, result.stderr
    assert "W01-B Vercel settings import OK" in result.stdout


def test_missing_database_url_fails_closed():
    result = _check_settings({"DATABASE_URL": ""})
    assert result.returncode != 0
    assert "DATABASE_URL is required" in result.stderr


def test_sqlite_database_url_fails_closed():
    result = _check_settings({"DATABASE_URL": "sqlite:///temp.sqlite3"})
    assert result.returncode != 0
    assert "PostgreSQL DATABASE_URL" in result.stderr


def test_debug_true_fails_closed():
    result = _check_settings({"DEBUG": "True"})
    assert result.returncode != 0
    assert "requires DEBUG=False" in result.stderr


def test_http_cors_origin_fails_closed():
    result = _check_settings({"CORS_ALLOWED_ORIGINS": "http://iamina-review.vercel.app"})
    assert result.returncode != 0
    assert "CORS_ALLOWED_ORIGINS must contain only valid HTTPS origins" in result.stderr


def test_wildcard_hosts_fail_closed():
    result = _check_settings({"ALLOWED_HOSTS": "*"})
    assert result.returncode != 0
    assert "Wildcard ALLOWED_HOSTS" in result.stderr


def test_iamina_production_runtime_requires_mail_recovery_gate():
    # IAMINA_ENV=production is deliberately NOT enabled on the shared dev stack.
    # A future production runtime must pass all independent SMTP + reset gates.
    result = _check_settings({"IAMINA_ENV": "production"})
    assert result.returncode != 0
    assert "requires SMTP EMAIL_BACKEND" in result.stderr
