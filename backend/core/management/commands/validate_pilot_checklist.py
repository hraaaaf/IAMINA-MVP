"""Validate that a cohort checklist has complete blocking evidence."""

from __future__ import annotations

import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from core.pilot_lifecycle import validate_completed_checklist


class Command(BaseCommand):
    help = "Fail unless every blocking pilot lifecycle item has approved evidence."

    def add_arguments(self, parser) -> None:
        parser.add_argument("--file", required=True)

    def handle(self, *args, **options):
        path = Path(options["file"]).expanduser().resolve()
        if not path.is_file() or path.is_symlink():
            raise CommandError("Checklist file must be a regular non-symlink file")
        try:
            payload = json.loads(path.read_text())
            if not isinstance(payload, dict):
                raise ValueError("checklist root must be an object")
            validate_completed_checklist(payload)
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(
            self.style.SUCCESS(
                f"Checklist validated for cohort {payload['cohort_id']}"
            )
        )
