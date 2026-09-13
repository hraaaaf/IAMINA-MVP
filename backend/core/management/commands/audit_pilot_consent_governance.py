"""Audit the pilot consent matrix and processor evidence registry."""

from __future__ import annotations

import json

from django.core.management.base import BaseCommand, CommandError

from core.pilot_consent_governance import consent_governance_payload
from core.pilot_data_residency import residency_readiness_payload
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
            "--residency-manifest",
            help=(
                "Restricted deployment-residency manifest that carries the approved "
                "CNDP health-processing evidence for a local-only release."
            ),
        )
        parser.add_argument(
            "--expected-source-commit-sha",
            help="Exact 40-character Git SHA for the candidate release being audited.",
        )

    def handle(self, *args, **options):
        require_approved = bool(options["require_approved"])
        local_only = bool(options["local_only"])
        residency_manifest = options.get("residency_manifest")
        expected_sha = options.get("expected_source_commit_sha")

        try:
            if residency_manifest and not local_only:
                raise ValueError("--residency-manifest requires --local-only")

            if local_only:
                health_references: tuple[str, ...] = ()
                residency_source_sha = ""
                if residency_manifest:
                    residency_payload = residency_readiness_payload(
                        manifest_path=residency_manifest,
                        require_approved=True,
                    )
                    if require_approved:
                        residency_payload = bind_payload_to_expected_source_commit(
                            residency_payload,
                            expected_source_commit_sha=expected_sha,
                            require_manifest_match=True,
                        )
                    health_references = tuple(
                        sorted(
                            {
                                str(flow["cndp_health_processing_reference"]).strip()
                                for flow in residency_payload["flows"]
                                if flow["enabled"]
                                and "health_data" in flow["data_categories"]
                                and str(
                                    flow["cndp_health_processing_reference"]
                                ).strip()
                            }
                        )
                    )
                    if not health_references:
                        raise ValueError(
                            "residency manifest has no approved enabled health-data evidence"
                        )
                    residency_source_sha = str(
                        residency_payload.get("source_commit_sha") or ""
                    ).strip()

                payload = release_scoped_consent_governance_payload(
                    enabled_external_providers=(),
                    global_health_processing_references=health_references,
                    require_approved=require_approved,
                )
                if residency_source_sha:
                    payload = {**payload, "source_commit_sha": residency_source_sha}
            else:
                payload = consent_governance_payload(require_approved=require_approved)

            if require_approved:
                payload = bind_payload_to_expected_source_commit(
                    payload,
                    expected_source_commit_sha=expected_sha,
                    require_manifest_match=bool(local_only and residency_manifest),
                )
        except ValueError as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(json.dumps(payload, ensure_ascii=False, indent=2))
