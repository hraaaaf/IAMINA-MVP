"""Audit the restricted native and clinical safety corpus review manifest."""

from __future__ import annotations

import json

from django.core.management.base import BaseCommand, CommandError

from core.release_evidence_binding import require_matching_source_sha
from core.safety_corpus_review import native_review_readiness_payload


class Command(BaseCommand):
    help = (
        "Validate native/clinical safety review coverage. Use --require-approved "
        "with the exact candidate SHA before a real patient pilot."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--manifest",
            help=(
                "Path to the restricted review manifest. Defaults to "
                "SAFETY_CORPUS_REVIEW_MANIFEST_PATH."
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
            help="Fail if any locale, case or parity dimension lacks approval or SHA binding.",
        )

    def handle(self, *args, **options):
        try:
            payload = native_review_readiness_payload(
                manifest_path=options.get("manifest"),
                require_approved=bool(options["require_approved"]),
            )
            if options["require_approved"]:
                require_matching_source_sha(
                    payload,
                    expected_source_sha=options.get("expected_source_sha"),
                    gate="native safety review",
                )
        except ValueError as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(json.dumps(payload, ensure_ascii=False, indent=2))
