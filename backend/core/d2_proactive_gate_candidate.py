"""D2 Web: inert, synthetic-only eligibility gate for proactive *in-app* candidates.

NO runtime consumer, API, persistence, scheduler, push, or notification dispatch.
A positive verdict authorizes a dry-run fixture only, never patient contact.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum

# Candidate policy values, not an approved patient-delivery SLA.
MAX_PROACTIVE_PER_ROLLING_WEEK = 2
MIN_GAP_BETWEEN_PROACTIVE = timedelta(hours=24)
DEDUP_WINDOW = timedelta(days=7)
MAX_EVIDENCE_AGE = timedelta(days=7)
EXPECTED_CONTRACT_VERSION = "d2.inapp.synthetic.v1"

# Strictly non-clinical event hypotheses. No actual producer is connected.
CANDIDATE_SOURCES = frozenset({"weekly_report_ready", "profile_completion_available"})


class D2DryRunVerdict(StrEnum):
    CANDIDATE_ONLY = "candidate_only_not_delivery"
    WRONG_SURFACE = "wrong_surface"
    NOT_AUTHORIZED = "not_authorized"
    STALE_SESSION = "stale_session"
    CONSENT_MISSING = "consent_missing"
    UNVERIFIED_SOURCE = "unverified_source"
    CLINICAL_SCOPE = "clinical_scope_forbidden"
    INVALID_TIMELINE = "invalid_timeline"
    DUPLICATE = "duplicate"
    DAILY_CAP = "daily_cap"
    WEEKLY_CAP = "weekly_cap"


@dataclass(frozen=True, slots=True)
class D2ProactiveCandidate:
    # Identity/epoch must be authenticated server facts, not caller-supplied ids.
    patient_id: int | None
    record_patient_id: int | None
    auth_epoch: int
    current_auth_epoch: int
    unlocked: bool
    # Current explicit preference AND authoritative stored consent are required.
    proactive_opt_in: bool
    server_consent_confirmed: bool
    category_enabled: bool
    global_ai_opt_out: bool
    # Only D2 proactive in-app, never D3 reminders or companion messages.
    channel: str
    kind: str
    event_type: str
    source_contract_version: str
    source_verified: bool
    evidence_id: str
    event_signature: str
    evidence_at: datetime
    now: datetime
    # Server-owned history in the SAME patient's scoped transaction, not browser.
    previous_proactive_at: tuple[datetime, ...] = ()
    last_same_event_at: datetime | None = None
    claims_urgent: bool = False
    suggests_treatment: bool = False
    contains_sensitive_preview: bool = False


def _aware(value: datetime) -> bool:
    return isinstance(value, datetime) and value.tzinfo is not None and value.utcoffset() is not None


def evaluate_d2_proactive_dry_run(c: D2ProactiveCandidate) -> D2DryRunVerdict:
    """Pure eligibility check. Must NOT be wired to delivery without human gates.

    Source validation, ownership, consent, and rate limits must be rechecked
    atomically by a future server-side integration. Boolean fixture flags here
    do not independently prove any external event or user permission.
    """
    if c.channel != "in_app_notification" or c.kind != "proactive":
        return D2DryRunVerdict.WRONG_SURFACE
    if (
        c.patient_id is None or c.patient_id <= 0
        or c.record_patient_id != c.patient_id or not c.unlocked
    ):
        return D2DryRunVerdict.NOT_AUTHORIZED
    if c.auth_epoch != c.current_auth_epoch or c.current_auth_epoch < 0:
        return D2DryRunVerdict.STALE_SESSION
    if (
        not c.proactive_opt_in or not c.server_consent_confirmed
        or not c.category_enabled or c.global_ai_opt_out
    ):
        return D2DryRunVerdict.CONSENT_MISSING
    if (
        not c.source_verified
        or c.event_type not in CANDIDATE_SOURCES
        or c.source_contract_version != EXPECTED_CONTRACT_VERSION
        or not c.evidence_id.strip() or not c.event_signature.strip()
    ):
        return D2DryRunVerdict.UNVERIFIED_SOURCE
    if c.claims_urgent or c.suggests_treatment or c.contains_sensitive_preview:
        return D2DryRunVerdict.CLINICAL_SCOPE
    if not _aware(c.now) or not _aware(c.evidence_at):
        return D2DryRunVerdict.INVALID_TIMELINE
    if not (c.now - MAX_EVIDENCE_AGE <= c.evidence_at <= c.now):
        return D2DryRunVerdict.INVALID_TIMELINE
    timestamps = c.previous_proactive_at
    if c.last_same_event_at is not None:
        timestamps = (*timestamps, c.last_same_event_at)
    if any(not _aware(ts) or ts > c.now for ts in timestamps):
        return D2DryRunVerdict.INVALID_TIMELINE
    if (
        c.last_same_event_at is not None
        and c.last_same_event_at > c.now - DEDUP_WINDOW
    ):
        return D2DryRunVerdict.DUPLICATE
    # Count only previous generated proactive items, never security or user-
    # initiated status events; the latter must reflect real source events.
    recent = [ts for ts in c.previous_proactive_at if ts > c.now - DEDUP_WINDOW]
    if any(ts > c.now - MIN_GAP_BETWEEN_PROACTIVE for ts in recent):
        return D2DryRunVerdict.DAILY_CAP
    if len(recent) >= MAX_PROACTIVE_PER_ROLLING_WEEK:
        return D2DryRunVerdict.WEEKLY_CAP
    return D2DryRunVerdict.CANDIDATE_ONLY
