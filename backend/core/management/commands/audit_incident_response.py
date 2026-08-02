"""Validate and print the current incident-response policy."""

from __future__ import annotations

import json

from django.core.management.base import BaseCommand, CommandError

from core.incident_response import policy_payload


class Command(BaseCommand):
    help = "Fail if the pilot incident-response policy is stale or incomplete."

    def handle(self, *args, **options):
        try:
            payload = policy_payload()
        except ValueError as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(json.dumps(payload, ensure_ascii=False, indent=2))
