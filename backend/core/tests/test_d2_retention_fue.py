"""Synthetic D2 retention FUE: dry-run, bounded physical deletion and owner cascade.

Tests the real management command against an isolated test database.
A passing result does not prove any production schedule or backup erasure.
"""
from datetime import timedelta
from io import StringIO

import pytest
from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import CommandError
from django.utils import timezone

from core.models.d2_notification import (
    D2Notification,
    D2NotificationPreference,
    D2ProactiveEmissionReceipt,
)


@pytest.mark.django_db
def test_d2_retention_fue_manual_dry_run_bounded_drain_preserves_live_rows():
    a = User.objects.create_user(username="fue_d2_retention_a")
    b = User.objects.create_user(username="fue_d2_retention_b")
    now = timezone.now()
    # Three expired account notices, one live notice belonging to B.
    for idx in range(3):
        D2Notification.objects.create(
            patient=a, event_key=f"{idx + 1:064x}",
            kind="event", code="ai_consent_given",
            created_at=now - timedelta(days=9),
            expires_at=now - timedelta(days=1),
        )
    live = D2Notification.objects.create(
        patient=b, event_key="d" * 64,
        kind="event", code="ai_consent_given", created_at=now,
        expires_at=now + timedelta(days=1),
    )
    # Receipts older than 7d should go; fresh 6d receipt must survive.
    for idx in range(2):
        D2ProactiveEmissionReceipt.objects.create(
            patient=a, event_key=f"{100 + idx:064x}",
            emitted_at=now - timedelta(days=9),
        )
    recent = D2ProactiveEmissionReceipt.objects.create(
        patient=b, event_key="e" * 64,
        emitted_at=now - timedelta(days=6),
    )

    dry = StringIO()
    call_command("purge_d2_notifications", limit=2, stdout=dry)
    assert "DRY_RUN expired=3 receipts_expired=2 max_batch=2" in dry.getvalue()
    assert D2Notification.objects.count() == 4
    assert D2ProactiveEmissionReceipt.objects.count() == 3

    first = StringIO()
    call_command("purge_d2_notifications", apply=True, limit=2, stdout=first)
    assert "APPLIED deleted=2 receipts_deleted=0 max_batch=2" in first.getvalue()

    second = StringIO()
    call_command("purge_d2_notifications", apply=True, limit=2, stdout=second)
    assert "APPLIED deleted=1 receipts_deleted=1 max_batch=2" in second.getvalue()

    third = StringIO()
    call_command("purge_d2_notifications", apply=True, limit=2, stdout=third)
    assert "APPLIED deleted=0 receipts_deleted=1 max_batch=2" in third.getvalue()

    assert list(D2Notification.objects.values_list("pk", flat=True)) == [live.pk]
    assert list(D2ProactiveEmissionReceipt.objects.values_list("pk", flat=True)) == [recent.pk]
    dry_after = StringIO()
    call_command("purge_d2_notifications", stdout=dry_after)
    assert "DRY_RUN expired=0 receipts_expired=0" in dry_after.getvalue()

    with pytest.raises(CommandError, match="within 1..200"):
        call_command("purge_d2_notifications", apply=True, limit=0)
    with pytest.raises(CommandError, match="within 1..200"):
        call_command("purge_d2_notifications", apply=True, limit=201)


@pytest.mark.django_db
def test_d2_retention_fue_account_delete_cascades_notification_data():
    a = User.objects.create_user(username="fue_d2_erasure_a")
    b = User.objects.create_user(username="fue_d2_erasure_b")
    now = timezone.now()
    D2NotificationPreference.objects.create(
        patient=a, proactive_opt_in=True,
        notice_version="synthetic", notice_digest="a" * 64, granted_at=now,
    )
    D2Notification.objects.create(
        patient=a, event_key="a" * 64, kind="event",
        code="ai_consent_given", created_at=now,
        expires_at=now + timedelta(days=2),
    )
    D2ProactiveEmissionReceipt.objects.create(
        patient=a, event_key="b" * 64, emitted_at=now,
    )
    survivor = D2Notification.objects.create(
        patient=b, event_key="c" * 64, kind="event",
        code="ai_consent_given", created_at=now,
        expires_at=now + timedelta(days=2),
    )
    a_id = a.pk  # Django clears model.pk on delete; assert against original owner ID.
    a.delete()
    assert not D2NotificationPreference.objects.filter(patient_id=a_id).exists()
    assert not D2Notification.objects.filter(patient_id=a_id).exists()
    assert not D2ProactiveEmissionReceipt.objects.filter(patient_id=a_id).exists()
    assert D2Notification.objects.filter(pk=survivor.pk, patient=b).exists()


@pytest.mark.django_db
def test_d2_retention_fue_guard_and_bounded_drain_fail_closed():
    """A scheduler candidate must fail when capped, never report false success."""
    a = User.objects.create_user(username="fue_d2_drain_a")
    b = User.objects.create_user(username="fue_d2_drain_b")
    now = timezone.now()
    for idx in range(5):
        D2Notification.objects.create(
            patient=a, event_key=f"{idx + 300:064x}", kind="event",
            code="ai_consent_given", created_at=now - timedelta(days=8),
            expires_at=now - timedelta(days=1),
        )
    for idx in range(3):
        D2ProactiveEmissionReceipt.objects.create(
            patient=a, event_key=f"{idx + 400:064x}",
            emitted_at=now - timedelta(days=9),
        )
    live = D2Notification.objects.create(
        patient=b, event_key="f" * 64, kind="event",
        code="ai_consent_given", created_at=now,
        expires_at=now + timedelta(days=2),
    )

    with pytest.raises(CommandError, match="requires explicit --apply"):
        call_command("purge_d2_notifications", drain=True, limit=2)
    assert D2Notification.objects.filter(patient=a).count() == 5

    with pytest.raises(CommandError, match="RETENTION_CHECK FAIL"):
        call_command("purge_d2_notifications", require_empty=True)
    assert D2ProactiveEmissionReceipt.objects.filter(patient=a).count() == 3

    with pytest.raises(CommandError, match="INCOMPLETE.*") as capped:
        call_command(
            "purge_d2_notifications", apply=True, drain=True,
            limit=2, max_batches=2,
        )
    assert "batches=2" in str(capped.value)
    assert "expired_remaining=1" in str(capped.value)
    assert "receipts_remaining=3" in str(capped.value)
    assert D2Notification.objects.filter(patient=a).count() == 1

    output = StringIO()
    call_command(
        "purge_d2_notifications", apply=True, drain=True,
        limit=2, max_batches=2, stdout=output,
    )
    assert "D2 DRAIN batches=2 deleted=1 receipts_deleted=3" in output.getvalue()
    assert "expired_remaining=0 receipts_remaining=0" in output.getvalue()
    assert "COMPLETE" in output.getvalue()
    assert D2Notification.objects.filter(pk=live.pk).exists()
    assert not D2Notification.objects.filter(patient=a).exists()
    assert not D2ProactiveEmissionReceipt.objects.filter(patient=a).exists()

    gate = StringIO()
    call_command("purge_d2_notifications", require_empty=True, stdout=gate)
    assert gate.getvalue().strip() == (
        "D2 RETENTION_CHECK PASS expired=0 receipts_expired=0"
    )


@pytest.mark.django_db
def test_d2_retention_fue_restore_guard_detects_old_stale_row():
    """Represents reintroduction of stale rows by an older restored snapshot.

    No actual production backup, database restore or scheduler is exercised.
    """
    a = User.objects.create_user(username="fue_d2_restore_old")
    now = timezone.now()
    out = StringIO()
    call_command("purge_d2_notifications", require_empty=True, stdout=out)
    assert "RETENTION_CHECK PASS" in out.getvalue()

    D2Notification.objects.create(
        patient=a, event_key="9" * 64, kind="event",
        code="ai_consent_given", created_at=now - timedelta(days=9),
        expires_at=now - timedelta(days=1),
    )
    with pytest.raises(CommandError, match="RETENTION_CHECK FAIL"):
        call_command("purge_d2_notifications", require_empty=True)
    assert D2Notification.objects.filter(patient=a).count() == 1

    purge = StringIO()
    call_command(
        "purge_d2_notifications", apply=True, drain=True,
        limit=2, max_batches=2, stdout=purge,
    )
    assert "COMPLETE" in purge.getvalue()
    gate = StringIO()
    call_command("purge_d2_notifications", require_empty=True, stdout=gate)
    assert "RETENTION_CHECK PASS" in gate.getvalue()
    assert not D2Notification.objects.filter(patient=a).exists()


@pytest.mark.django_db
def test_d2_retention_fue_invalid_control_combinations_never_delete():
    a = User.objects.create_user(username="fue_d2_invalid_ops")
    now = timezone.now()
    D2Notification.objects.create(
        patient=a, event_key="8" * 64, kind="event",
        code="ai_consent_given", created_at=now - timedelta(days=9),
        expires_at=now - timedelta(days=1),
    )
    for opts in (
        {"apply": True, "require_empty": True},
        {"drain": True},
        {"apply": True, "drain": True, "max_batches": 0},
        {"apply": True, "drain": True, "max_batches": 101},
    ):
        with pytest.raises(CommandError):
            call_command("purge_d2_notifications", **opts)
    assert D2Notification.objects.filter(patient=a).count() == 1
