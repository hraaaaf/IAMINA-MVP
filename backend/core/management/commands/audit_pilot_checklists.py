"""Validate the canonical pilot lifecycle checklist registry."""

from __future__ import annotations

import json
from datetime import date

from django.core.management.base import BaseCommand, CommandError

from core.pilot_lifecycle import checklist_registry_payload


class Command(BaseCommand):
    help = "Fail if the pilot lifecycle checklist registry is incomplete or stale."

    def handle(self, *args, **options):
        try:
            payload = checklist_registry_payload()
            today = date.today()
            effective_on = date.fromisoformat(payload["effective_on"])
            review_due_on = date.fromisoformat(payload["review_due_on"])
            if effective_on > today:
                raise ValueError("pilot checklist policy is not effective")
            if review_due_on < today:
                raise ValueError("pilot checklist policy is stale")
        except (TypeError, ValueError) as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(json.dumps(payload, ensure_ascii=False, indent=2))
