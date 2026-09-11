"""Audit the pilot consent matrix and candidate-bound processor approvals."""

from __future__ import annotations

import json

from django.core.management.base import BaseCommand, CommandError

from core.pilot_consent_governance import consent_governance_payload
from core.release_evidence_binding import consent_release_approval_payload


class Command(BaseCommand):
    help = (
        "Validate consent/processor governance. Use --require-approved with a "
        "restricted approval manifest and exact source SHA before a real patient pilot."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--manifest",
            help=(
                "Path to the restricted consent/processor approval manifest. Defaults "
                "to PILOT_CONSENT_GOVERNANCE_MANIFEST_PATH."
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
            help="Fail unless candidate-bound consent and applicable processor approvals pass.",
        )

    def handle(self, *args, **options):
        try:
            inventory = consent_governance_payload(require_approved=False)
            if not options["require_approved"]:
                self.stdout.write(
                    json.dumps(inventory, ensure_ascii=False, indent=2)
                )
                return

            approval = consent_release_approval_payload(
                manifest_path=options.get("manifest"),
                expected_source_sha=options.get("expected_source_sha"),
            )
            payload = {
                "schema_version": approval["schema_version"],
                "status": "approved_for_candidate",
                "source_commit_sha": approval["source_commit_sha"],
                "release_approval": approval,
                "consent_matrix": inventory["consent_matrix"],
                "processor_inventory_status": inventory["status"],
                "processor_inventory_blockers": inventory["blockers"],
                "blockers": [],
                "non_claim": (
                    "Candidate-bound release evidence is recorded, but real-patient "
                    "enablement still requires every P5-6 external and human gate."
                ),
            }
        except ValueError as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(json.dumps(payload, ensure_ascii=False, indent=2))
