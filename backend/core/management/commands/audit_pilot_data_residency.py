"""Audit the restricted Morocco pilot deployment-residency manifest."""

from __future__ import annotations

import json

from django.core.management.base import BaseCommand, CommandError

from core.pilot_data_residency import residency_readiness_payload


class Command(BaseCommand):
    help = (
        "Validate production data locations and foreign-transfer evidence. "
        "Use --require-approved before a real patient pilot."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--manifest",
            help=(
                "Path to the restricted deployment manifest. Defaults to "
                "PILOT_RESIDENCY_MANIFEST_PATH."
            ),
        )
        parser.add_argument(
            "--require-approved",
            action="store_true",
            help="Fail if the manifest is missing, stale, incomplete or unapproved.",
        )

    def handle(self, *args, **options):
        try:
            payload = residency_readiness_payload(
                manifest_path=options.get("manifest"),
                require_approved=bool(options["require_approved"]),
            )
        except ValueError as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(json.dumps(payload, ensure_ascii=False, indent=2))
