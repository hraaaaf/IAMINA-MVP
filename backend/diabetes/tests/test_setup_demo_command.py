from datetime import UTC, datetime, timedelta

import pytest
from django.core.management import call_command

from diabetes.models import LogEntry


@pytest.mark.django_db
def test_setup_demo_keeps_fresh_data_then_refreshes_stale_history(monkeypatch, capsys):
    from diabetes.management.commands import setup_demo

    initial_now = datetime(2026, 9, 1, 23, 0, tzinfo=UTC)
    monkeypatch.setattr(setup_demo.timezone, "now", lambda: initial_now)
    call_command("setup_demo")

    initial_entries = list(
        LogEntry.objects.filter(patient__username="patient1")
        .order_by("logged_at")
        .values_list("logged_at", flat=True)
    )
    assert initial_entries
    initial_latest = initial_entries[-1]

    # A normal rerun while the demo is still recent must be idempotent.
    monkeypatch.setattr(
        setup_demo.timezone,
        "now",
        lambda: initial_now + timedelta(days=1),
    )
    call_command("setup_demo")
    fresh_rerun_entries = list(
        LogEntry.objects.filter(patient__username="patient1")
        .order_by("logged_at")
        .values_list("logged_at", flat=True)
    )
    assert fresh_rerun_entries == initial_entries

    # A later rerun must move the synthetic window forward automatically.
    stale_now = initial_now + timedelta(days=30)
    monkeypatch.setattr(setup_demo.timezone, "now", lambda: stale_now)
    call_command("setup_demo")
    refreshed_entries = list(
        LogEntry.objects.filter(patient__username="patient1")
        .order_by("logged_at")
        .values_list("logged_at", flat=True)
    )

    assert refreshed_entries
    assert refreshed_entries[-1] > initial_latest + timedelta(days=20)
    assert refreshed_entries[-1] >= stale_now - setup_demo.DEMO_FRESHNESS_MAX_AGE
    assert "Données de démo périmées" in capsys.readouterr().out
