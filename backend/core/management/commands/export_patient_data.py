"""Create a secure, audited JSON export for one patient account."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from core.data_portability import build_patient_export
from core.models import AuditLog


class Command(BaseCommand):
    help = "Export one patient's IAmina data to a mode-0600 JSON file."

    def add_arguments(self, parser) -> None:
        parser.add_argument("--user-id", type=int, required=True)
        parser.add_argument("--output", required=True)
        parser.add_argument("--overwrite", action="store_true")

    def handle(self, *args, **options):
        user_id = options["user_id"]
        output = Path(options["output"]).expanduser().resolve()
        overwrite = options["overwrite"]

        if output.exists() and not overwrite:
            raise CommandError("Output already exists; use --overwrite explicitly")
        if not output.parent.exists() or not output.parent.is_dir():
            raise CommandError("Output parent directory does not exist")

        user_model = get_user_model()
        try:
            user = user_model.objects.get(pk=user_id)
        except user_model.DoesNotExist as exc:
            raise CommandError("Patient account not found") from exc

        bundle = build_patient_export(user)
        encoded = json.dumps(bundle, ensure_ascii=False, indent=2).encode("utf-8")
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
            raise CommandError("Unable to write patient export") from exc

        AuditLog.objects.create(
            actor=user,
            action="export",
            resource_type="PatientDataExport",
            resource_id=str(user.pk),
            metadata={
                "schema_version": bundle["schema_version"],
                "sha256": bundle["sha256"],
                "record_count": bundle["manifest"]["record_count"],
            },
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"Export written to {output} "
                f"(records={bundle['manifest']['record_count']}, sha256={bundle['sha256']})"
            )
        )
