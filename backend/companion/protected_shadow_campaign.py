"""Bounded, content-free reporting helpers for protected narration shadow campaigns.

This module deliberately does not call a provider, change processor policy, or persist
patient content. It only validates and summarizes the allowlisted telemetry emitted by
protected_shadow_telemetry.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

_ALLOWED_STATUSES = ("disabled", "blocked", "accepted", "rejected", "error")
_EXPECTED_KEYS = frozenset({"event", "status", "provider", "family"})


@dataclass(frozen=True, slots=True)
class ProtectedShadowCampaignProtocol:
    """Local campaign bounds. This object is not persisted as patient telemetry."""

    campaign_id: str
    max_turns: int
    locales: tuple[str, ...]
    family: str = "clinician_prep"
    provider: str = "groq"

    def __post_init__(self) -> None:
        if not self.campaign_id.strip():
            raise ValueError("campaign_id must be non-empty")
        if not 1 <= self.max_turns <= 500:
            raise ValueError("max_turns must be between 1 and 500")
        if not self.locales or any(not item.strip() for item in self.locales):
            raise ValueError("locales must contain non-empty values")
        if self.family != "clinician_prep":
            raise ValueError("only clinician_prep is allowed in this campaign phase")
        if self.provider != "groq":
            raise ValueError("only groq is allowed in this campaign phase")


@dataclass(frozen=True, slots=True)
class ProtectedShadowCampaignSummary:
    observed_turns: int
    disabled: int
    blocked: int
    accepted: int
    rejected: int
    error: int

    @property
    def provider_attempted_turns(self) -> int:
        return self.accepted + self.rejected + self.error


def _validate_event(event: Mapping[str, object]) -> str:
    if frozenset(event) != _EXPECTED_KEYS:
        raise ValueError("protected shadow telemetry contains non-allowlisted fields")
    if event.get("event") != "protected_narration_shadow":
        raise ValueError("unexpected telemetry event")
    if event.get("provider") != "groq":
        raise ValueError("unexpected protected shadow provider")
    if event.get("family") != "clinician_prep":
        raise ValueError("unexpected protected shadow family")
    status = event.get("status")
    if status not in _ALLOWED_STATUSES:
        raise ValueError("unexpected protected shadow status")
    return str(status)


def summarize_protected_shadow_campaign(
    protocol: ProtectedShadowCampaignProtocol,
    events: Iterable[Mapping[str, object]],
) -> ProtectedShadowCampaignSummary:
    """Validate the bounded event set and return content-free status counts."""

    counts = {status: 0 for status in _ALLOWED_STATUSES}
    observed = 0
    for event in events:
        observed += 1
        if observed > protocol.max_turns:
            raise ValueError("campaign exceeded max_turns")
        counts[_validate_event(event)] += 1

    return ProtectedShadowCampaignSummary(
        observed_turns=observed,
        disabled=counts["disabled"],
        blocked=counts["blocked"],
        accepted=counts["accepted"],
        rejected=counts["rejected"],
        error=counts["error"],
    )


__all__ = [
    "ProtectedShadowCampaignProtocol",
    "ProtectedShadowCampaignSummary",
    "summarize_protected_shadow_campaign",
]
