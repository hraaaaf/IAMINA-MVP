"""Dry-run or purge expired patient export staging files."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

_RETENTION_DAYS = 7
_PATTERN = "iamina-patient-*.json"


class Command(BaseCommand):
    help = "Find or remove IAmina export staging files older than seven days."

    def add_arguments(self, parser) -> None:
        parser.add_argument("--directory", required=True)
        parser.add_argument("--execute", action="store_true")

    def handle(self, *args, **options):
        directory = Path(options["directory"]).expanduser().resolve()
        execute = options["execute"]
        if not directory.is_dir():
            raise CommandError("Export staging directory does not exist")

        cutoff = datetime.now(timezone.utc) - timedelta(days=_RETENTION_DAYS)
        candidates: list[dict[str, object]] = []
        for path in sorted(directory.glob(_PATTERN)):
            if path.is_symlink() or not path.is_file():
                continue
            modified_at = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
            if modified_at >= cutoff:
                continue
            candidates.append(
                {
                    "name": path.name,
                    "modified_at": modified_at.isoformat(),
                    "size_bytes": path.stat().st_size,
                }
            )
            if execute:
                path.unlink()

        result = {
            "schema_version": "1.0",
            "directory": str(directory),
            "retention_days": _RETENTION_DAYS,
            "cutoff": cutoff.isoformat(),
            "action": "PURGED" if execute else "DRY_RUN",
            "candidate_count": len(candidates),
            "files": candidates,
        }
        self.stdout.write(json.dumps(result, ensure_ascii=False, indent=2))
