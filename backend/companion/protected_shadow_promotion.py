"""Fail-closed promotion assessment for protected narration shadow.

This module does not approve processor governance, activate provider traffic, or change
patient-visible output. It only evaluates explicit evidence supplied by the caller.
"""
from __future__ import annotations

from dataclasses import dataclass

from companion.protected_shadow_campaign import ProtectedShadowCampaignSummary


@dataclass(frozen=True, slots=True)
class ProtectedShadowPromotionEvidence:
    processor_governance_approved: bool
    payload_boundary_verified: bool
    adversarial_gate_green: bool
    kill_switch_verified: bool
    deterministic_fallback_verified: bool
    clinical_authority_unchanged: bool
    campaign_summary: ProtectedShadowCampaignSummary


@dataclass(frozen=True, slots=True)
class ProtectedShadowPromotionDecision:
    promotable: bool
    blockers: tuple[str, ...]


def assess_protected_shadow_promotion(
    evidence: ProtectedShadowPromotionEvidence,
) -> ProtectedShadowPromotionDecision:
    """Return a deterministic decision; missing prerequisites always block promotion."""

    blockers: list[str] = []
    if not evidence.processor_governance_approved:
        blockers.append("processor_governance_not_approved")
    if not evidence.payload_boundary_verified:
        blockers.append("payload_boundary_not_verified")
    if not evidence.adversarial_gate_green:
        blockers.append("adversarial_gate_not_green")
    if not evidence.kill_switch_verified:
        blockers.append("kill_switch_not_verified")
    if not evidence.deterministic_fallback_verified:
        blockers.append("deterministic_fallback_not_verified")
    if not evidence.clinical_authority_unchanged:
        blockers.append("clinical_authority_changed")

    summary = evidence.campaign_summary
    if summary.observed_turns == 0:
        blockers.append("campaign_has_no_observations")
    if summary.blocked:
        blockers.append("campaign_contains_blocked_turns")
    if summary.error:
        blockers.append("campaign_contains_errors")
    if summary.rejected:
        blockers.append("campaign_contains_unresolved_rejections")
    if summary.accepted != summary.observed_turns:
        blockers.append("campaign_not_fully_accepted")

    return ProtectedShadowPromotionDecision(
        promotable=not blockers,
        blockers=tuple(blockers),
    )


__all__ = [
    "ProtectedShadowPromotionDecision",
    "ProtectedShadowPromotionEvidence",
    "assess_protected_shadow_promotion",
]
