"""Audit the pilot consent matrix and processor evidence registry."""

from __future__ import annotations

import json

from django.core.management.base import BaseCommand, CommandError

from core.pilot_consent_governance import consent_governance_payload
from core.pilot_release_binding import bind_payload_to_expected_source_commit
from core.pilot_release_provider_scope import release_scoped_consent_governance_payload


class Command(BaseCommand):
    help = (
        "Validate consent/processor governance. Use --require-approved as the "
        "fail-closed gate before a real patient pilot."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--require-approved",
            action="store_true",
            help="Fail while release-applicable regulatory or processor evidence is pending.",
        )
        parser.add_argument(
            "--local-only",
            action="store_true",
            help=(
                "Audit a release with zero external processors enabled. Disabled "
                "network providers do not block it; global health-data authorization still does."
            ),
        )
        parser.add_argument(
            "--expected-source-commit-sha",
            help="Exact 40-character Git SHA for the candidate release being audited.",
        )

    def handle(self, *args, **options):
        require_approved = bool(options["require_approved"])
        try:
            if options["local_only"]:
                payload = release_scoped_consent_governance_payload(
                    enabled_external_providers=(),
                    require_approved=require_approved,
                )
            else:
                payload = consent_governance_payload(require_approved=require_approved)
            if require_approved:
                payload = bind_payload_to_expected_source_commit(
                    payload,
                    expected_source_commit_sha=options.get("expected_source_commit_sha"),
                    require_manifest_match=False,
                )
        except ValueError as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(json.dumps(payload, ensure_ascii=False, indent=2))
