"""G3 recovery CLI: fail closed outside expressly opted-in local SQLite.

All records are synthetic. Calls into account erasure are intercepted; this
suite must never access Firebase, Neon, Vercel, or production systems.
"""
import json
from io import StringIO

import pytest
from django.conf import settings
from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import CommandError

from core.models.erasure_attempt import ErasureAttempt


@pytest.mark.django_db
def test_recovery_command_defaults_to_read_only_dry_run(monkeypatch):
    user = User.objects.create_user(username="cli-dryrun", password="SyntheticOnly!1")
    ErasureAttempt.objects.create(
        patient_id_snapshot=user.pk,
        firebase_uid_snapshot="synthetic-not-to-leak",
    )
    monkeypatch.delenv("IAMINA_G3_LOCAL_SYNTHETIC_RECOVERY", raising=False)
    def must_not_erase(user):
        pytest.fail("Dry-run called erasure")
    monkeypatch.setattr(
        "core.management.commands.reconcile_synthetic_erasure._erase_account_data",
        must_not_erase,
    )
    out = StringIO()
    call_command("reconcile_synthetic_erasure", patient_id=user.pk, stdout=out)
    payload = json.loads(out.getvalue())
    assert payload == {"patient_id": user.pk, "state": "pending", "action": "DRY_RUN"}
    assert "synthetic-not-to-leak" not in out.getvalue()
    assert User.objects.filter(pk=user.pk).exists()


@pytest.mark.django_db
def test_execute_disallowed_without_opt_in_before_reading_db(monkeypatch):
    monkeypatch.delenv("IAMINA_G3_LOCAL_SYNTHETIC_RECOVERY", raising=False)
    monkeypatch.setattr(
        "core.management.commands.reconcile_synthetic_erasure.ErasureAttempt.objects.filter",
        lambda **kwargs: pytest.fail("Denied execute queried database"),
    )
    with pytest.raises(CommandError, match="disabled"):
        call_command(
            "reconcile_synthetic_erasure",
            patient_id=77,
            execute=True,
            confirm="ERASE-SYNTHETIC-77",
        )


@pytest.mark.django_db
def test_execute_rejects_postgresql_even_when_opted_in_without_any_db_lookup(
    monkeypatch
):
    monkeypatch.setenv("IAMINA_G3_LOCAL_SYNTHETIC_RECOVERY", "1")
    monkeypatch.delenv("VERCEL", raising=False)
    monkeypatch.delenv("VERCEL_ENV", raising=False)
    monkeypatch.setattr(settings, "DEBUG", True)
    monkeypatch.setitem(
        settings.DATABASES["default"], "ENGINE", "django.db.backends.postgresql"
    )
    monkeypatch.setattr(
        "core.management.commands.reconcile_synthetic_erasure.ErasureAttempt.objects.filter",
        lambda **kwargs: pytest.fail("PostgreSQL execute queried database"),
    )
    with pytest.raises(CommandError, match="disabled"):
        call_command(
            "reconcile_synthetic_erasure",
            patient_id=78,
            execute=True,
            confirm="ERASE-SYNTHETIC-78",
        )


@pytest.mark.django_db
def test_execute_rejects_vercel_even_on_sqlite(monkeypatch):
    monkeypatch.setenv("IAMINA_G3_LOCAL_SYNTHETIC_RECOVERY", "1")
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.setattr(settings, "DEBUG", True)
    with pytest.raises(CommandError, match="disabled"):
        call_command(
            "reconcile_synthetic_erasure",
            patient_id=79,
            execute=True,
            confirm="ERASE-SYNTHETIC-79",
        )


@pytest.mark.django_db
def test_execute_needs_exact_confirmation(monkeypatch):
    user = User.objects.create_user(username="cli-confirm", password="SyntheticOnly!1")
    ErasureAttempt.objects.create(patient_id_snapshot=user.pk)
    monkeypatch.setenv("IAMINA_G3_LOCAL_SYNTHETIC_RECOVERY", "1")
    monkeypatch.delenv("VERCEL", raising=False)
    monkeypatch.delenv("VERCEL_ENV", raising=False)
    monkeypatch.setattr(settings, "DEBUG", True)
    with pytest.raises(CommandError, match="confirmation"):
        call_command(
            "reconcile_synthetic_erasure",
            patient_id=user.pk,
            execute=True,
            confirm="wrong",
        )


@pytest.mark.django_db
def test_execute_local_sqlite_calls_only_explicit_synthetic_recovery(monkeypatch):
    user = User.objects.create_user(username="cli-execute", password="SyntheticOnly!1")
    ErasureAttempt.objects.create(patient_id_snapshot=user.pk)
    monkeypatch.setenv("IAMINA_G3_LOCAL_SYNTHETIC_RECOVERY", "1")
    monkeypatch.delenv("VERCEL", raising=False)
    monkeypatch.delenv("VERCEL_ENV", raising=False)
    monkeypatch.setattr(settings, "DEBUG", True)
    assert settings.DATABASES["default"]["ENGINE"] == "django.db.backends.sqlite3"
    seen = []
    monkeypatch.setattr(
        "core.management.commands.reconcile_synthetic_erasure._erase_account_data",
        lambda selected: seen.append(selected.pk),
    )
    out = StringIO()
    call_command(
        "reconcile_synthetic_erasure",
        patient_id=user.pk,
        execute=True,
        confirm=f"ERASE-SYNTHETIC-{user.pk}",
        stdout=out,
    )
    assert seen == [user.pk]
    assert json.loads(out.getvalue()) == {
        "patient_id": user.pk,
        "state": "completed",
        "action": "EXECUTE",
    }
