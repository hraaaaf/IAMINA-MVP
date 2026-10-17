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
FAKE_HOST = "ep-w01-synthetic.c-7.eu-central-1.aws.neon.tech"
FAKE_PG = f"postgresql://w01_synthetic:w01_synthetic@{FAKE_HOST}/w01_synthetic?sslmode=require"

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
    "IAMINA_EXPECTED_DB_HOST": FAKE_HOST,
    "IAMINA_EXPECTED_DB_NAME": "w01_synthetic",
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
        "IAMINA_ENV", "IAMINA_EXPECTED_DB_HOST", "IAMINA_EXPECTED_DB_NAME",
        "VERCEL_ENV", "VERCEL", "DATABASE_URL",
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

def test_missing_iamina_env_fails_closed():
    result = _check_settings({"IAMINA_ENV": ""})
    assert result.returncode != 0
    assert "IAMINA_ENV must explicitly" in result.stderr


def test_invalid_iamina_env_fails_closed():
    result = _check_settings({"IAMINA_ENV": "produciton"})
    assert result.returncode != 0
    assert "IAMINA_ENV must explicitly" in result.stderr


def test_missing_database_identity_marker_fails_closed():
    result = _check_settings({"IAMINA_EXPECTED_DB_HOST": ""})
    assert result.returncode != 0
    assert "IAMINA_EXPECTED_DB_HOST" in result.stderr


def test_wrong_neon_endpoint_fails_closed_without_leaking_password():
    wrong = FAKE_PG.replace(FAKE_HOST, "ep-unrelated.c-7.eu-central-1.aws.neon.tech")
    result = _check_settings({"DATABASE_URL": wrong})
    assert result.returncode != 0
    assert "does not match the expected Neon environment" in result.stderr
    assert "w01_synthetic:w01_synthetic" not in result.stderr


def test_wrong_neon_database_fails_closed():
    result = _check_settings({"IAMINA_EXPECTED_DB_NAME": "another_db"})
    assert result.returncode != 0
    assert "does not match the expected Neon environment" in result.stderr


def test_missing_tls_requirement_fails_closed():
    result = _check_settings({"DATABASE_URL": FAKE_PG.replace("?sslmode=require", "")})
    assert result.returncode != 0
    assert "must explicitly enforce PostgreSQL TLS" in result.stderr


def test_preview_must_match_its_own_declared_neon_identity():
    result = _check_settings({"VERCEL_ENV": "preview", "IAMINA_ENV": "development"})
    assert result.returncode == 0, result.stderr

    mismatch = _check_settings({"VERCEL_ENV": "preview", "IAMINA_EXPECTED_DB_HOST": "ep-prod.c-5.eu-central-1.aws.neon.tech"})
    assert mismatch.returncode != 0
    assert "does not match the expected Neon environment" in mismatch.stderr


def test_matching_neon_pooler_host_is_accepted():
    pooled = FAKE_HOST.replace(".c-", "-pooler.c-", 1)
    result = _check_settings({"DATABASE_URL": FAKE_PG.replace(FAKE_HOST, pooled)})
    assert result.returncode == 0, result.stderr

def test_patient_production_rejects_tls_without_server_verification():
    result = _check_settings({"IAMINA_ENV": "production"})
    assert result.returncode != 0
    assert "requires sslmode=verify-full" in result.stderr


def test_patient_production_rejects_verify_full_without_system_ca():
    result = _check_settings({
        "IAMINA_ENV": "production",
        "DATABASE_URL": FAKE_PG.replace("sslmode=require", "sslmode=verify-full"),
    })
    assert result.returncode != 0
    assert "requires sslrootcert=system" in result.stderr


def test_patient_production_rejects_preview_target_even_with_verified_tls():
    verified = FAKE_PG.replace(
        "sslmode=require", "sslmode=verify-full&sslrootcert=system"
    )
    result = _check_settings({
        "IAMINA_ENV": "production",
        "VERCEL_ENV": "preview",
        "DATABASE_URL": verified,
    })
    assert result.returncode != 0
    assert "cannot run on a Vercel preview" in result.stderr


def test_verified_production_tls_passes_identity_gate_to_smtp_gate():
    verified = FAKE_PG.replace(
        "sslmode=require", "sslmode=verify-full&sslrootcert=system"
    )
    result = _check_settings({
        "IAMINA_ENV": "production",
        "DATABASE_URL": verified,
    })
    assert result.returncode != 0
    assert "requires SMTP EMAIL_BACKEND" in result.stderr

