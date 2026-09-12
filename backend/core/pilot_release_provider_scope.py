"""Release-scoped processor governance for P5-6.

The full provider registry remains fail-closed and auditable.  A concrete pilot
release may explicitly enable only a subset of external processors; disabled
processors do not become release blockers.  Morocco health-data authorization
remains a global blocker even for a local-only release.
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import date

from core.ai_processor_policy import registered_processor_policies
from core.pilot_consent_governance import consent_governance_payload

GLOBAL_HEALTH_PROCESSING_BLOCKER = "cndp_health_processing_authorization:pending"


def release_scoped_consent_governance_payload(
    *,
    enabled_external_providers: Iterable[str],
    today: date | None = None,
    require_approved: bool = False,
) -> dict[str, object]:
    enabled = frozenset(enabled_external_providers)
    runtime = registered_processor_policies()
    unknown = sorted(enabled - set(runtime))
    if unknown:
        raise ValueError(f"unknown enabled external providers: {unknown}")
    non_external = sorted(
        provider for provider in enabled if not runtime[provider].external_egress
    )
    if non_external:
        raise ValueError(
            "enabled_external_providers contains local providers: "
            f"{non_external}"
        )

    payload = consent_governance_payload(today=today, require_approved=False)
    scoped_blockers = [GLOBAL_HEALTH_PROCESSING_BLOCKER]
    processor_rows = []
    for row in payload["processors"]:
        release_enabled = bool(row["external_egress"] and row["provider"] in enabled)
        row = {**row, "release_enabled": release_enabled}
        if release_enabled:
            scoped_blockers.extend(
                blocker
                for blocker in row["blockers"]
                if "cndp_health_processing_authorization" not in blocker
            )
        processor_rows.append(row)

    blockers = sorted(set(scoped_blockers))
    if require_approved and blockers:
        raise ValueError(
            "pilot release consent/processor governance is not approved: "
            + ", ".join(blockers)
        )

    return {
        **payload,
        "schema_version": "2026-09-12.1",
        "status": "approved" if not blockers else "pending_external_approval",
        "release_mode": "local_only" if not enabled else "external_processors_enabled",
        "enabled_external_providers": sorted(enabled),
        "processors": processor_rows,
        "blockers": blockers,
        "non_claim": (
            "Release scoping does not constitute CNDP, legal, processor, security "
            "or privacy approval. Disabled processors remain runtime-denied."
        ),
    }
