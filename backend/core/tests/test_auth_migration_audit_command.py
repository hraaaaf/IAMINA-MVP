"""Executable cutover-readiness audit tests."""

from io import StringIO

import pytest
from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import CommandError

from core.models import BasePatientProfile


@pytest.mark.django_db
def test_audit_passes_for_unambiguous_profiled_django_users():
    user = User.objects.create_user(username="patient", email="patient@example.test")
    BasePatientProfile.objects.create(patient=user)
    output = StringIO()

    call_command("audit_auth_migration", stdout=output)

    assert "auth_migration_ready" in output.getvalue()


@pytest.mark.django_db
def test_audit_fails_when_user_has_no_base_profile():
    User.objects.create_user(username="orphan", email="orphan@example.test")

    with pytest.raises(CommandError, match="users_without_profile"):
        call_command("audit_auth_migration", stdout=StringIO())


@pytest.mark.django_db
def test_audit_fails_on_case_insensitive_email_collision():
    first = User.objects.create_user(username="first", email="same@example.test")
    second = User.objects.create_user(username="second", email="SAME@example.test")
    BasePatientProfile.objects.create(patient=first)
    BasePatientProfile.objects.create(patient=second)

    with pytest.raises(CommandError, match="duplicate_normalized_emails"):
        call_command("audit_auth_migration", stdout=StringIO())


@pytest.mark.django_db
def test_final_cutover_mode_fails_while_firebase_links_remain():
    user = User.objects.create_user(username="linked", email="linked@example.test")
    BasePatientProfile.objects.create(patient=user, firebase_uid="firebase-linked")

    with pytest.raises(CommandError, match="firebase_links_remain"):
        call_command(
            "audit_auth_migration",
            require_zero_firebase=True,
            stdout=StringIO(),
        )
