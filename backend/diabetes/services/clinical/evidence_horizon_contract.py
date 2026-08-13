"""Read-only candidate contract for P3-HORIZON evidence discovery."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from hashlib import sha256

from diabetes.services.clinical.evidence_registry import EvidenceMaturity


class HorizonFinality(StrEnum):
    FINAL = "final"
    DRAFT = "draft"
    PREPRINT = "preprint"
    ABSTRACT_ONLY = "abstract_only"
    UNKNOWN = "unknown"


class HorizonVerification(StrEnum):
    UNVERIFIED = "unverified"
    VERIFIED = "verified"


@dataclass(frozen=True, slots=True)
class HorizonCandidate:
    topic: str
    source_organization: str
    source_title: str
    identifier: str
    publication_or_version_date: str
    finality_status: HorizonFinality
    proposed_maturity: EvidenceMaturity
    population: tuple[str, ...]
    modality: tuple[str, ...]
    jurisdiction: str
    regulatory_status: str
    retrieved_at: datetime
    source_locator: str
    verification_status: HorizonVerification = HorizonVerification.UNVERIFIED
    limitations: tuple[str, ...] = ()
    known_evidence_id: str | None = None

    def __post_init__(self) -> None:
        for field_name in (
            "topic",
            "source_organization",
            "source_title",
            "publication_or_version_date",
            "jurisdiction",
            "regulatory_status",
            "source_locator",
        ):
            if not str(getattr(self, field_name)).strip():
                raise ValueError(f"{field_name} must be non-empty")
        if self.retrieved_at.tzinfo is None or self.retrieved_at.utcoffset() is None:
            raise ValueError("retrieved_at must be timezone-aware")
        if self.proposed_maturity == EvidenceMaturity.INTERNAL_GOVERNED_RULE:
            raise ValueError("horizon candidates cannot propose internal governed rules")
        if self.verification_status == HorizonVerification.VERIFIED and not self.identifier.strip():
            raise ValueError("verified candidates require a canonical identifier")

    @property
    def candidate_fingerprint(self) -> str:
        payload = "\x1f".join(
            (
                self.source_organization.strip().casefold(),
                self.source_title.strip().casefold(),
                self.identifier.strip().casefold(),
                self.publication_or_version_date.strip(),
            )
        )
        return sha256(payload.encode("utf-8")).hexdigest()

    @property
    def eligible_for_registry_review(self) -> bool:
        return (
            self.verification_status == HorizonVerification.VERIFIED
            and self.finality_status == HorizonFinality.FINAL
            and bool(self.identifier.strip())
        )
