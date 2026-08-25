from __future__ import annotations

import io
import json
from datetime import datetime, timezone

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from core.finops_events import FinOpsTelemetryEvent


class Frug0MonthlyLedgerCommandTests(TestCase):
    def _run(self, month: str) -> dict:
        stdout = io.StringIO()
        call_command("frug0_monthly_ledger", month=month, stdout=stdout)
        return json.loads(stdout.getvalue())

    def test_empty_month_preserves_missing_denominators(self) -> None:
        report = self._run("2026-08")
        assert report["event_count"] == 0
        assert report["metrics"]["interactions"] == 0
        assert report["metrics"]["llm_call_rate_per_interaction"] is None
        assert report["metrics"]["zero_model_rate_per_interaction"] is None
        assert report["media_metrics"]["media_events"] == 0
        assert report["media_metrics"]["uploaded_bytes_per_mau"] is None
        assert report["media_metrics"]["downloaded_bytes_per_mau"] is None
        assert report["media_metrics"]["storage_occupancy_bytes"] is None

    def test_month_filters_and_aggregates_persisted_events(self) -> None:
        august = FinOpsTelemetryEvent.objects.create(
            event_type="companion_route",
            payload={"event": "companion_route", "route": "llm"},
        )
        september = FinOpsTelemetryEvent.objects.create(
            event_type="companion_route",
            payload={"event": "companion_route", "route": "zero_model"},
        )
        FinOpsTelemetryEvent.objects.filter(pk=august.pk).update(
            timestamp=datetime(2026, 8, 25, 12, 0, tzinfo=timezone.utc)
        )
        FinOpsTelemetryEvent.objects.filter(pk=september.pk).update(
            timestamp=datetime(2026, 9, 1, 0, 0, tzinfo=timezone.utc)
        )

        report = self._run("2026-08")
        assert report["event_count"] == 1
        assert report["metrics"]["route_counts"]["llm"] == 1
        assert report["metrics"]["route_counts"]["zero_model"] == 0
        assert report["metrics"]["llm_call_rate_per_interaction"] == 1.0

    def test_month_filters_and_aggregates_media_bytes(self) -> None:
        august = FinOpsTelemetryEvent.objects.create(
            event_type="media_bytes",
            payload={
                "event": "media_bytes",
                "action": "uploaded",
                "workload": "document_import",
                "bytes": 2048,
                "retention_class": "TRANSIENT_EXTRACTION",
            },
        )
        september = FinOpsTelemetryEvent.objects.create(
            event_type="media_bytes",
            payload={
                "event": "media_bytes",
                "action": "downloaded",
                "workload": "document_import",
                "bytes": 512,
                "retention_class": "PATIENT_RETAINED",
            },
        )
        FinOpsTelemetryEvent.objects.filter(pk=august.pk).update(
            timestamp=datetime(2026, 8, 31, 23, 59, tzinfo=timezone.utc)
        )
        FinOpsTelemetryEvent.objects.filter(pk=september.pk).update(
            timestamp=datetime(2026, 9, 1, 0, 0, tzinfo=timezone.utc)
        )

        report = self._run("2026-08")
        media = report["media_metrics"]
        assert report["event_count"] == 1
        assert media["media_events"] == 1
        assert media["bytes_by_action"]["uploaded"] == 2048
        assert media["bytes_by_action"]["downloaded"] == 0
        assert media["uploaded_bytes_per_mau"] is None
        assert media["downloaded_bytes_per_mau"] is None
        assert media["storage_occupancy_bytes"] is None
        assert media["storage_cost_per_mau"] is None
        assert media["egress_cost_per_mau"] is None

    def test_invalid_month_fails_closed(self) -> None:
        with self.assertRaises(CommandError):
            self._run("2026-13")
