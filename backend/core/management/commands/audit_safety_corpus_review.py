"""Audit the restricted native and clinical safety corpus review manifest."""

from __future__ import annotations

import json

from django.core.management.base import BaseCommand, CommandError

from core.safety_corpus_review import native_review_readiness_payload


class Command(BaseCommand):
    help = (
        "Validate native/clinical safety review coverage. Use --require-approved "
        "as the fail-closed gate before a real patient pilot."
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
            "--require-approved",
            action="store_true",
            help="Fail if any locale, case or parity dimension lacks approval.",
        )

    def handle(self, *args, **options):
        try:
            payload = native_review_readiness_payload(
                manifest_path=options.get("manifest"),
                require_approved=bool(options["require_approved"]),
            )
        except ValueError as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(json.dumps(payload, ensure_ascii=False, indent=2))
