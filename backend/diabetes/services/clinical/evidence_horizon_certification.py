"""Deterministic certification boundary for evidence-horizon scan outputs."""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from diabetes.services.clinical.evidence_horizon_contract import (
    HorizonFinality,
    HorizonVerification,
)
from diabetes.services.clinical.evidence_horizon_scanner import (
    HorizonScanBatch,
    HorizonScanState,
)


class HorizonCertificationStatus(StrEnum):
    PASS = "pass"
    REVIEW_REQUIRED = "review_required"
    INCOMPLETE = "incomplete"


@dataclass(frozen=True, slots=True)
class HorizonCertification:
    status: HorizonCertificationStatus
    reasons: tuple[str, ...]

    @property
    def can_claim_clean_scan(self) -> bool:
        return self.status == HorizonCertificationStatus.PASS


def certify_horizon_batch(batch: HorizonScanBatch) -> HorizonCertification:
    reasons: list[str] = []

    if batch.state == HorizonScanState.INCOMPLETE:
        reasons.append("scan_incomplete")
        return HorizonCertification(HorizonCertificationStatus.INCOMPLETE, tuple(reasons))

    for candidate in batch.candidates:
        if candidate.verification_status != HorizonVerification.VERIFIED:
            reasons.append("candidate_unverified")
        if candidate.finality_status != HorizonFinality.FINAL:
            reasons.append("candidate_not_final")
        if not candidate.identifier.strip():
            reasons.append("candidate_identifier_missing")

    if reasons:
        return HorizonCertification(
            HorizonCertificationStatus.REVIEW_REQUIRED,
            tuple(sorted(set(reasons))),
        )

    return HorizonCertification(HorizonCertificationStatus.PASS, ())
