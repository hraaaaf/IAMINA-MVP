"""Audit the restricted Morocco pilot deployment-residency manifest."""

from __future__ import annotations

import json

from django.core.management.base import BaseCommand, CommandError

from core.pilot_data_residency import residency_readiness_payload
from core.pilot_release_binding import bind_payload_to_expected_source_commit


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
        parser.add_argument(
            "--expected-source-commit-sha",
            help="Exact 40-character Git SHA for the candidate release being audited.",
        )

    def handle(self, *args, **options):
        require_approved = bool(options["require_approved"])
        try:
            payload = residency_readiness_payload(
                manifest_path=options.get("manifest"),
                require_approved=require_approved,
            )
            if require_approved:
                payload = bind_payload_to_expected_source_commit(
                    payload,
                    expected_source_commit_sha=options.get("expected_source_commit_sha"),
                    require_manifest_match=True,
                )
        except ValueError as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(json.dumps(payload, ensure_ascii=False, indent=2))
