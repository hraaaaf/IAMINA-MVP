import json
import os
import subprocess
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[2]


def _import_vercel_settings(database_url: str | None) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.update(
        {
            "SECRET_KEY": "test-only-secret-key",
            "DEBUG": "False",
            "ALLOWED_HOSTS": "iamina-certified.vercel.app",
            "CORS_ALLOWED_ORIGINS": "https://iamina-review.vercel.app",
            "CSRF_TRUSTED_ORIGINS": "https://iamina-review.vercel.app",
            "VERCEL": "1",
            "VERCEL_URL": "iamina-certified.vercel.app",
        }
    )
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
                "print(s.ALLOWED_HOSTS)"
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


def test_vercel_settings_accept_postgres_without_connecting():
    result = _import_vercel_settings("postgresql://user:pass@127.0.0.1:5432/iamina")

    assert result.returncode == 0, result.stderr
    assert "django.db.backends.postgresql" in result.stdout
    assert "iamina-certified.vercel.app" in result.stdout


def test_vercel_config_keeps_deployments_manual_and_targets_wsgi():
    config = json.loads((BACKEND_ROOT / "vercel.json").read_text(encoding="utf-8"))

    assert config["git"]["deploymentEnabled"] is False
    assert config["functions"]["amina/wsgi.py"]["maxDuration"] == 60
