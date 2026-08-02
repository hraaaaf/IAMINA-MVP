"""Validate and print the current pilot retention schedule."""

from __future__ import annotations

import json

from django.core.management.base import BaseCommand, CommandError

from core.retention_policy import retention_schedule_payload


class Command(BaseCommand):
    help = "Fail if the pilot retention schedule is missing, stale or inconsistent."

    def handle(self, *args, **options):
        try:
            payload = retention_schedule_payload()
        except ValueError as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(json.dumps(payload, ensure_ascii=False, indent=2))
