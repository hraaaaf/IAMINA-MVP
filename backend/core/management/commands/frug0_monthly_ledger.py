"""Export one privacy-safe FRUG-0 monthly usage ledger as JSON."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone

from django.core.management.base import BaseCommand, CommandError

from llm.cost_event_store import load_cost_events
from llm.cost_metrics import aggregate_cost_events
from media.usage_metrics import aggregate_media_usage

_MONTH_RE = re.compile(r"^(\d{4})-(0[1-9]|1[0-2])$")


def _month_bounds(value: str) -> tuple[datetime, datetime]:
    match = _MONTH_RE.fullmatch(value)
    if match is None:
        raise CommandError("--month must use YYYY-MM")
    year, month = (int(part) for part in match.groups())
    start = datetime(year, month, 1, tzinfo=timezone.utc)
    if month == 12:
        end = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
    else:
        end = datetime(year, month + 1, 1, tzinfo=timezone.utc)
    return start, end


class Command(BaseCommand):
    help = "Export the persisted FRUG-0 monthly aggregate; never emits patient/content data."

    def add_arguments(self, parser) -> None:
        parser.add_argument("--month", required=True, help="UTC reporting month as YYYY-MM")

    def handle(self, *args, **options) -> None:
        month = options["month"]
        start, end = _month_bounds(month)
        events = load_cost_events(start=start, end=end)
        report = {
            "period": month,
            "event_count": len(events),
            "metrics": aggregate_cost_events(events),
            "media_metrics": aggregate_media_usage(events),
        }
        self.stdout.write(json.dumps(report, sort_keys=True, separators=(",", ":")))
