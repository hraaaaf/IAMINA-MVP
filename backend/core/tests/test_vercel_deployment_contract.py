import json
import os
import subprocess
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[2]

_EMAIL_ENV_KEYS = {
    "EMAIL_BACKEND",
    "EMAIL_HOST",
    "EMAIL_PORT",
    "EMAIL_HOST_USER",
    "EMAIL_HOST_PASSWORD",
    "DEFAULT_FROM_EMAIL",
    "PASSWORD_RESET_FRONTEND_URL",
    "EMAIL_USE_TLS",
    "EMAIL_USE_SSL",
}


def _import_vercel_settings(
    database_url: str | None,
    *,
    cors_origins: str = "https://iamina-review.vercel.app",
    csrf_origins: str = "https://iamina-review.vercel.app",
    email_overrides: dict[str, str | None] | None = None,
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    for key in _EMAIL_ENV_KEYS:
        env.pop(key, None)
    env.update(
        {
            "SECRET_KEY": "test-only-secret-key",
            "DEBUG": "False",
            "ALLOWED_HOSTS": "iamina-certified.vercel.app",
            "CORS_ALLOWED_ORIGINS": cors_origins,
            "CSRF_TRUSTED_ORIGINS": csrf_origins,
            "VERCEL": "1",
            "VERCEL_URL": "iamina-certified.vercel.app",
            "EMAIL_BACKEND": "django.core.mail.backends.smtp.EmailBackend",
            "EMAIL_HOST": "smtp.example.test",
            "EMAIL_PORT": "587",
            "EMAIL_HOST_USER": "iamina-test",
            "EMAIL_HOST_PASSWORD": "test-only-password",
            "DEFAULT_FROM_EMAIL": "noreply@iamina.health",
            "PASSWORD_RESET_FRONTEND_URL": "iamina://reset-password",
            "EMAIL_USE_TLS": "True",
            "EMAIL_USE_SSL": "False",
        }
    )
    if email_overrides:
        for key, value in email_overrides.items():
            if value is None:
                env.pop(key, None)
            else:
                env[key] = value
    if database_url is None:
        env.pop("DATABASE_URL", None)
    else:
        env["DATABASE_URL"] = database_url

    return subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import amina.vercel_settings as s; "
                "print(s.DATABASES['default']['ENGINE']); "
                "print(s.ALLOWED_HOSTS); "
                "print(s.EMAIL_BACKEND); "
                "print(s.PASSWORD_RESET_FRONTEND_URL)"
            ),
        ],
        cwd=BACKEND_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def test_vercel_settings_fail_closed_without_database_url():
    result = _import_vercel_settings(None)

    assert result.returncode != 0
    assert "DATABASE_URL is required on Vercel" in result.stderr


def test_vercel_settings_reject_sqlite_database_url():
    result = _import_vercel_settings("sqlite:///tmp/iamina.db")

    assert result.returncode != 0
    assert "requires PostgreSQL DATABASE_URL" in result.stderr


def test_vercel_settings_reject_non_https_cors_origin():
    result = _import_vercel_settings(
        "postgresql://user:pass@127.0.0.1:5432/iamina",
        cors_origins="http://iamina-review.vercel.app",
    )

    assert result.returncode != 0
    assert "CORS_ALLOWED_ORIGINS must contain only valid HTTPS origins" in result.stderr


def test_vercel_settings_reject_non_https_csrf_origin():
    result = _import_vercel_settings(
        "postgresql://user:pass@127.0.0.1:5432/iamina",
        csrf_origins="http://localhost:8000",
    )

    assert result.returncode != 0
    assert "CSRF_TRUSTED_ORIGINS must contain only valid HTTPS origins" in result.stderr


def test_vercel_settings_fail_closed_without_email_host():
    result = _import_vercel_settings(
        "postgresql://user:pass@127.0.0.1:5432/iamina",
        email_overrides={"EMAIL_HOST": None},
    )

    assert result.returncode != 0
    assert "password recovery requires" in result.stderr
    assert "EMAIL_HOST" in result.stderr


def test_vercel_settings_reject_non_smtp_email_backend():
    result = _import_vercel_settings(
        "postgresql://user:pass@127.0.0.1:5432/iamina",
        email_overrides={
            "EMAIL_BACKEND": "django.core.mail.backends.console.EmailBackend"
        },
    )

    assert result.returncode != 0
    assert "requires SMTP EMAIL_BACKEND" in result.stderr


def test_vercel_settings_accept_postgres_without_connecting():
    result = _import_vercel_settings("postgresql://user:pass@127.0.0.1:5432/iamina")

    assert result.returncode == 0, result.stderr
    assert "django.db.backends.postgresql" in result.stdout
    assert "iamina-certified.vercel.app" in result.stdout
    assert "django.core.mail.backends.smtp.EmailBackend" in result.stdout
    assert "iamina://reset-password" in result.stdout


def test_vercel_config_keeps_deployments_manual_and_targets_python_bridge():
    config = json.loads((BACKEND_ROOT / "vercel.json").read_text(encoding="utf-8"))

    assert config["git"]["deploymentEnabled"] is False
    assert config["regions"] == ["cdg1"]
    assert config["functions"]["api/index.py"]["maxDuration"] == 60
    assert config["rewrites"] == [
        {"source": "/(.*)", "destination": "/api/index.py"}
    ]
    assert (BACKEND_ROOT / "api" / "index.py").read_text(encoding="utf-8") == (
        "from amina.wsgi import application\n\napp = application\n"
    )
    assert (BACKEND_ROOT / ".python-version").read_text(encoding="utf-8").strip() == "3.12"
