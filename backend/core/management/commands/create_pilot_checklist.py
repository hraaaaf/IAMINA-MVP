"""Create a restricted pilot lifecycle checklist for one opaque cohort ID."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from core.pilot_lifecycle import build_cohort_checklist


class Command(BaseCommand):
    help = "Create a mode-0600 onboarding, monitoring, escalation and exit checklist."

    def add_arguments(self, parser) -> None:
        parser.add_argument("--cohort-id", required=True)
        parser.add_argument("--output", required=True)

    def handle(self, *args, **options):
        output = Path(options["output"]).expanduser().resolve()
        if output.exists():
            raise CommandError("Checklist output already exists")
        if not output.parent.is_dir():
            raise CommandError("Checklist output parent directory does not exist")
        try:
            payload = build_cohort_checklist(options["cohort_id"])
        except ValueError as exc:
            raise CommandError(str(exc)) from exc

        encoded = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        temp_name: str | None = None
        try:
            fd, temp_name = tempfile.mkstemp(
                prefix=f".{output.name}.",
                suffix=".tmp",
                dir=output.parent,
            )
            os.fchmod(fd, 0o600)
            with os.fdopen(fd, "wb") as handle:
                handle.write(encoded)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_name, output)
            os.chmod(output, 0o600)
        except OSError as exc:
            if temp_name:
                Path(temp_name).unlink(missing_ok=True)
            raise CommandError("Unable to write pilot checklist") from exc

        self.stdout.write(
            self.style.SUCCESS(
                f"Pilot checklist written to {output} "
                f"(cohort={payload['cohort_id']}, items={len(payload['items'])})"
            )
        )
