"""Create a restricted, minimized incident record bundle."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from core.incident_response import CATEGORIES, SEV1, SEV2, SEV3, SEV4, create_incident_payload


class Command(BaseCommand):
    help = "Create a mode-0600 incident record without patient identifiers."

    def add_arguments(self, parser) -> None:
        parser.add_argument("--category", choices=sorted(CATEGORIES), required=True)
        parser.add_argument("--summary", required=True)
        parser.add_argument("--systems", required=True)
        parser.add_argument("--severity", choices=(SEV1, SEV2, SEV3, SEV4))
        parser.add_argument("--output", required=True)

    def handle(self, *args, **options):
        output = Path(options["output"]).expanduser().resolve()
        if output.exists():
            raise CommandError("Incident output already exists")
        if not output.parent.is_dir():
            raise CommandError("Incident output parent directory does not exist")

        systems = tuple(
            item.strip() for item in options["systems"].split(",") if item.strip()
        )
        try:
            payload = create_incident_payload(
                category=options["category"],
                summary=options["summary"],
                affected_systems=systems,
                severity=options["severity"],
            )
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
            raise CommandError("Unable to write incident record") from exc

        self.stdout.write(
            self.style.SUCCESS(
                f"Incident {payload['incident_id']} written to {output} "
                f"(severity={payload['severity']})"
            )
        )
