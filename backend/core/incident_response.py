"""Versioned incident-response and escalation policy for the pilot."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from datetime import date, datetime
from uuid import uuid4

from django.utils import timezone

SEV1 = "SEV1"
SEV2 = "SEV2"
SEV3 = "SEV3"
SEV4 = "SEV4"

CATEGORIES = frozenset(
    {
        "patient_safety",
        "data_exposure",
        "authentication_compromise",
        "provider_outage",
        "incorrect_clinical_output",
        "availability",
        "other",
    }
)


@dataclass(frozen=True, slots=True)
class SeverityRule:
    severity: str
    acknowledgement_minutes: int
    incident_commander_minutes: int
    containment_target_minutes: int
    executive_escalation: bool
    clinical_safety_escalation: bool

    def validate(self) -> None:
        if self.severity not in {SEV1, SEV2, SEV3, SEV4}:
            raise ValueError("unknown incident severity")
        durations = (
            self.acknowledgement_minutes,
            self.incident_commander_minutes,
            self.containment_target_minutes,
        )
        if any(value <= 0 for value in durations):
            raise ValueError(f"invalid response duration for {self.severity}")
        if self.incident_commander_minutes < self.acknowledgement_minutes:
            raise ValueError(f"incident commander target precedes acknowledgement for {self.severity}")


@dataclass(frozen=True, slots=True)
class IncidentResponsePolicy:
    owner: str
    effective_on: date
    review_due_on: date
    required_roles: tuple[str, ...]
    severity_rules: tuple[SeverityRule, ...]

    def validate(self, *, today: date | None = None) -> None:
        current = today or date.today()
        if not self.owner.strip():
            raise ValueError("incident policy owner is required")
        if self.effective_on > current:
            raise ValueError("incident policy is not effective")
        if self.review_due_on < current:
            raise ValueError("incident policy is stale")
        required = {
            "incident_commander",
            "clinical_safety_lead",
            "security_lead",
            "privacy_lead",
            "communications_owner",
        }
        missing = sorted(required.difference(self.required_roles))
        if missing:
            raise ValueError("incident roles missing: " + ", ".join(missing))
        severities = [rule.severity for rule in self.severity_rules]
        if len(severities) != len(set(severities)):
            raise ValueError("duplicate incident severity")
        if set(severities) != {SEV1, SEV2, SEV3, SEV4}:
            raise ValueError("incident severity matrix is incomplete")
        for rule in self.severity_rules:
            rule.validate()


POLICY = IncidentResponsePolicy(
    owner="IAmina Safety & Security",
    effective_on=date(2026, 8, 2),
    review_due_on=date(2026, 11, 2),
    required_roles=(
        "incident_commander",
        "clinical_safety_lead",
        "security_lead",
        "privacy_lead",
        "communications_owner",
    ),
    severity_rules=(
        SeverityRule(SEV1, 15, 30, 60, True, True),
        SeverityRule(SEV2, 60, 120, 240, True, True),
        SeverityRule(SEV3, 240, 480, 1440, False, False),
        SeverityRule(SEV4, 1440, 2880, 4320, False, False),
    ),
)

_DEFAULT_SEVERITY = {
    "patient_safety": SEV1,
    "data_exposure": SEV1,
    "authentication_compromise": SEV1,
    "incorrect_clinical_output": SEV1,
    "provider_outage": SEV2,
    "availability": SEV2,
    "other": SEV3,
}

_FORBIDDEN_METADATA = (
    re.compile(r"\b[^\s@]+@[^\s@]+\.[^\s@]+\b", re.IGNORECASE),
    re.compile(r"(?<!\d)(?:\+?212|0)[5-7]\d{8}(?!\d)"),
    re.compile(r"\b(?:patient|user)[-_ ]?id\s*[:=]\s*\d+\b", re.IGNORECASE),
)


def assert_minimized_incident_text(value: str) -> None:
    """Reject common direct identifiers from incident metadata."""
    if not value.strip():
        raise ValueError("incident text cannot be empty")
    if any(pattern.search(value) for pattern in _FORBIDDEN_METADATA):
        raise ValueError("incident metadata contains a direct identifier")


def severity_rule(severity: str) -> SeverityRule:
    POLICY.validate()
    for rule in POLICY.severity_rules:
        if rule.severity == severity:
            return rule
    raise ValueError("unknown incident severity")


def create_incident_payload(
    *,
    category: str,
    summary: str,
    affected_systems: tuple[str, ...],
    severity: str | None = None,
    opened_at: datetime | None = None,
) -> dict[str, object]:
    POLICY.validate()
    if category not in CATEGORIES:
        raise ValueError("unknown incident category")
    assert_minimized_incident_text(summary)
    if not affected_systems or any(not item.strip() for item in affected_systems):
        raise ValueError("at least one affected system is required")
    for item in affected_systems:
        assert_minimized_incident_text(item)

    selected_severity = severity or _DEFAULT_SEVERITY[category]
    rule = severity_rule(selected_severity)
    timestamp = opened_at or timezone.now()
    if timezone.is_naive(timestamp):
        raise ValueError("opened_at must be timezone-aware")

    return {
        "schema_version": "1.0",
        "incident_id": f"INC-{timestamp:%Y%m%d}-{uuid4().hex[:12].upper()}",
        "opened_at": timestamp.isoformat(),
        "category": category,
        "severity": selected_severity,
        "summary": summary,
        "affected_systems": list(affected_systems),
        "patient_safety_impact": "UNKNOWN",
        "data_exposure_status": "UNKNOWN",
        "status": "OPEN",
        "roles": {role: "UNASSIGNED" for role in POLICY.required_roles},
        "targets": asdict(rule),
        "timeline": [
            {
                "at": timestamp.isoformat(),
                "event": "incident_opened",
                "actor_role": "reporter",
            }
        ],
        "containment_actions": [],
        "evidence_references": [],
        "notification_assessment": "PENDING",
        "postmortem_due": None,
    }


def policy_payload(*, today: date | None = None) -> dict[str, object]:
    POLICY.validate(today=today)
    return {
        "schema_version": "1.0",
        "owner": POLICY.owner,
        "effective_on": POLICY.effective_on.isoformat(),
        "review_due_on": POLICY.review_due_on.isoformat(),
        "required_roles": list(POLICY.required_roles),
        "severity_rules": [asdict(rule) for rule in POLICY.severity_rules],
        "categories": sorted(CATEGORIES),
    }
