"""Production cutover gate for benchmark-derived provider proposals."""

from __future__ import annotations

from dataclasses import dataclass

from .decision import ProviderDecision


@dataclass(frozen=True, slots=True)
class CutoverEvidence:
    benchmark_report_id: str
    dataset_version: str
    processor_policy_approved: bool
    human_safety_review_approved: bool
    rollback_documented: bool
    rejected_alternatives_documented: bool


def authorize_cutover(
    decision: ProviderDecision,
    evidence: CutoverEvidence,
) -> str:
    if decision.selected_provider is None:
        raise ValueError("no eligible provider selected")
    missing: list[str] = []
    if not evidence.benchmark_report_id:
        missing.append("benchmark_report")
    if not evidence.dataset_version:
        missing.append("dataset_version")
    if not evidence.processor_policy_approved:
        missing.append("processor_policy")
    if not evidence.human_safety_review_approved:
        missing.append("human_safety_review")
    if not evidence.rollback_documented:
        missing.append("rollback")
    if not evidence.rejected_alternatives_documented:
        missing.append("rejected_alternatives")
    if missing:
        raise ValueError("cutover evidence incomplete: " + ", ".join(missing))
    return decision.selected_provider
