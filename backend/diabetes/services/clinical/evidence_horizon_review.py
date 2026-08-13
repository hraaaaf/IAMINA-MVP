"""Read-only comparison between horizon candidates and registered source records."""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from diabetes.services.clinical.evidence_horizon_contract import HorizonCandidate
from diabetes.services.clinical.evidence_registry import EVIDENCE_REGISTRY, RecordKind


class HorizonRelation(StrEnum):
    IDENTIFIER_MATCH = "identifier_match"
    POSSIBLE_SUCCESSOR = "possible_successor"
    TOPIC_OVERLAP = "topic_overlap"
    NEW_CANDIDATE = "new_candidate"


@dataclass(frozen=True, slots=True)
class HorizonReviewItem:
    candidate: HorizonCandidate
    relation: HorizonRelation
    matched_evidence_ids: tuple[str, ...]
    ready_for_review: bool


def _norm(value: str) -> str:
    return " ".join(value.split()).casefold()


def compare_candidate(candidate: HorizonCandidate) -> HorizonReviewItem:
    sources = tuple(
        record for record in EVIDENCE_REGISTRY.values() if record.kind == RecordKind.SOURCE
    )
    identifier = _norm(candidate.identifier)
    topic = _norm(candidate.topic)
    organization = _norm(candidate.source_organization)

    matches = tuple(
        record.evidence_id
        for record in sources
        if identifier and _norm(record.identifier) == identifier
    )
    if matches:
        relation = HorizonRelation.IDENTIFIER_MATCH
    else:
        matches = tuple(
            record.evidence_id
            for record in sources
            if _norm(record.source_organization) == organization
            and _norm(record.topic) == topic
        )
        if matches:
            relation = HorizonRelation.POSSIBLE_SUCCESSOR
        else:
            matches = tuple(
                record.evidence_id for record in sources if _norm(record.topic) == topic
            )
            relation = HorizonRelation.TOPIC_OVERLAP if matches else HorizonRelation.NEW_CANDIDATE

    return HorizonReviewItem(
        candidate=candidate,
        relation=relation,
        matched_evidence_ids=matches,
        ready_for_review=candidate.eligible_for_registry_review,
    )
