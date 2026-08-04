"""Audit the pilot consent matrix and processor evidence registry."""

from __future__ import annotations

import json

from django.core.management.base import BaseCommand, CommandError

from core.pilot_consent_governance import consent_governance_payload


class Command(BaseCommand):
    help = (
        "Validate consent/processor governance. Use --require-approved as the "
        "fail-closed gate before a real patient pilot."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--require-approved",
            action="store_true",
            help="Fail while any external processor or regulatory evidence is pending.",
        )

    def handle(self, *args, **options):
        try:
            payload = consent_governance_payload(
                require_approved=bool(options["require_approved"]),
            )
        except ValueError as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(json.dumps(payload, ensure_ascii=False, indent=2))
