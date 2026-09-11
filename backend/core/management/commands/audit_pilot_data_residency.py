"""Audit the restricted Morocco pilot deployment-residency manifest."""

from __future__ import annotations

import json

from django.core.management.base import BaseCommand, CommandError

from core.pilot_data_residency import residency_readiness_payload
from core.release_evidence_binding import require_matching_source_sha


class Command(BaseCommand):
    help = (
        "Validate production data locations and foreign-transfer evidence. "
        "Use --require-approved with the exact candidate SHA before a real patient pilot."
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
            "--expected-source-sha",
            help=(
                "Exact candidate Git SHA. Defaults to PILOT_RELEASE_SOURCE_SHA and is "
                "mandatory with --require-approved."
            ),
        )
        parser.add_argument(
            "--require-approved",
            action="store_true",
            help="Fail if the manifest is missing, stale, incomplete, unapproved or SHA-mismatched.",
        )

    def handle(self, *args, **options):
        try:
            payload = residency_readiness_payload(
                manifest_path=options.get("manifest"),
                require_approved=bool(options["require_approved"]),
            )
            if options["require_approved"]:
                require_matching_source_sha(
                    payload,
                    expected_source_sha=options.get("expected_source_sha"),
                    gate="pilot data residency",
                )
        except ValueError as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(json.dumps(payload, ensure_ascii=False, indent=2))
