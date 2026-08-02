"""Versioned onboarding, monitoring, escalation and exit checklists."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from datetime import date, datetime
from typing import Final

from django.utils import timezone

ONBOARDING: Final = "onboarding"
MONITORING: Final = "monitoring"
ESCALATION: Final = "escalation"
EXIT: Final = "exit"

PENDING: Final = "PENDING"
PASS: Final = "PASS"
NOT_APPLICABLE: Final = "NOT_APPLICABLE"

_PHASES = (ONBOARDING, MONITORING, ESCALATION, EXIT)
_STATUSES = frozenset({PENDING, PASS, NOT_APPLICABLE})
_OPAQUE_COHORT_ID = re.compile(r"^[A-Z0-9][A-Z0-9_-]{2,31}$")
_OPAQUE_EVIDENCE_ID = re.compile(r"^[A-Z0-9][A-Z0-9_.:/-]{2,127}$")


@dataclass(frozen=True, slots=True)
class ChecklistItem:
    item_id: str
    phase: str
    title: str
    owner_role: str
    evidence_kind: str
    blocking: bool
    cadence: str

    def validate(self) -> None:
        if not re.fullmatch(r"[A-Z]{2,8}-\d{2}", self.item_id):
            raise ValueError(f"invalid checklist item id: {self.item_id}")
        if self.phase not in _PHASES:
            raise ValueError(f"unknown checklist phase: {self.phase}")
        required = {
            "title": self.title,
            "owner_role": self.owner_role,
            "evidence_kind": self.evidence_kind,
            "cadence": self.cadence,
        }
        missing = sorted(name for name, value in required.items() if not value.strip())
        if missing:
            raise ValueError(
                f"missing checklist fields for {self.item_id}: {', '.join(missing)}"
            )


CHECKLIST_ITEMS: tuple[ChecklistItem, ...] = (
    ChecklistItem(
        "ONB-01",
        ONBOARDING,
        "Confirm cohort owner, scope, start and stop criteria",
        "pilot_owner",
        "approved_cohort_charter",
        True,
        "once_before_enrolment",
    ),
    ChecklistItem(
        "ONB-02",
        ONBOARDING,
        "Verify participant identity and eligibility",
        "onboarding_owner",
        "identity_and_eligibility_attestation",
        True,
        "per_participant",
    ),
    ChecklistItem(
        "ONB-03",
        ONBOARDING,
        "Capture approved consent matrix and active media permissions",
        "privacy_lead",
        "consent_snapshot",
        True,
        "per_participant_and_on_change",
    ),
    ChecklistItem(
        "ONB-04",
        ONBOARDING,
        "Confirm country, UI language, response language and emergency resources",
        "onboarding_owner",
        "locale_confirmation_snapshot",
        True,
        "per_participant",
    ),
    ChecklistItem(
        "ONB-05",
        ONBOARDING,
        "Disclose companion limits and self-care-only emergency mode",
        "clinical_safety_lead",
        "participant_acknowledgement",
        True,
        "per_participant",
    ),
    ChecklistItem(
        "ONB-06",
        ONBOARDING,
        "Verify processor, retention, incident and export gates are current",
        "pilot_owner",
        "readiness_audit_bundle",
        True,
        "before_first_participant",
    ),
    ChecklistItem(
        "ONB-07",
        ONBOARDING,
        "Complete baseline safety and support-channel test",
        "clinical_safety_lead",
        "synthetic_safety_test_record",
        True,
        "before_first_participant",
    ),
    ChecklistItem(
        "MON-01",
        MONITORING,
        "Review service health, failed requests and provider availability",
        "operations_owner",
        "service_health_review",
        True,
        "daily",
    ),
    ChecklistItem(
        "MON-02",
        MONITORING,
        "Review safety refusals, emergency detections and unexpected clinical output",
        "clinical_safety_lead",
        "safety_event_review",
        True,
        "daily",
    ),
    ChecklistItem(
        "MON-03",
        MONITORING,
        "Review consent revocations and processor-policy changes",
        "privacy_lead",
        "consent_and_processor_review",
        True,
        "daily",
    ),
    ChecklistItem(
        "MON-04",
        MONITORING,
        "Run retention, authentication and secret-hygiene audits",
        "security_lead",
        "automated_control_bundle",
        True,
        "weekly",
    ),
    ChecklistItem(
        "MON-05",
        MONITORING,
        "Review participant support requests and unresolved issues",
        "support_owner",
        "support_queue_review",
        False,
        "daily",
    ),
    ChecklistItem(
        "MON-06",
        MONITORING,
        "Review pilot outcomes, withdrawals and stop criteria",
        "pilot_owner",
        "pilot_outcome_review",
        True,
        "weekly",
    ),
    ChecklistItem(
        "ESC-01",
        ESCALATION,
        "Classify severity and open minimized incident record",
        "incident_commander",
        "incident_record",
        True,
        "per_incident",
    ),
    ChecklistItem(
        "ESC-02",
        ESCALATION,
        "Assign clinical, security, privacy and communications roles",
        "incident_commander",
        "role_assignment_record",
        True,
        "per_incident",
    ),
    ChecklistItem(
        "ESC-03",
        ESCALATION,
        "Apply fail-closed containment without removing deterministic safety",
        "security_lead",
        "containment_record",
        True,
        "per_incident",
    ),
    ChecklistItem(
        "ESC-04",
        ESCALATION,
        "Assess patient outreach and notification obligations",
        "privacy_lead",
        "notification_assessment",
        True,
        "per_incident",
    ),
    ChecklistItem(
        "ESC-05",
        ESCALATION,
        "Approve recovery, recurrence monitoring and postmortem actions",
        "incident_commander",
        "recovery_and_postmortem_record",
        True,
        "per_incident",
    ),
    ChecklistItem(
        "EXIT-01",
        EXIT,
        "Record withdrawal, completion or pilot-stop reason",
        "pilot_owner",
        "exit_reason_record",
        True,
        "per_participant_or_cohort",
    ),
    ChecklistItem(
        "EXIT-02",
        EXIT,
        "Offer and, when requested, deliver patient data export",
        "privacy_lead",
        "export_offer_and_delivery_record",
        True,
        "per_participant",
    ),
    ChecklistItem(
        "EXIT-03",
        EXIT,
        "Revoke pilot access, sessions and temporary permissions",
        "security_lead",
        "access_revocation_record",
        True,
        "per_participant_or_cohort",
    ),
    ChecklistItem(
        "EXIT-04",
        EXIT,
        "Apply retention, deletion or legal-hold decision",
        "privacy_lead",
        "retention_deletion_decision",
        True,
        "per_participant",
    ),
    ChecklistItem(
        "EXIT-05",
        EXIT,
        "Freeze outcome data and document known limitations",
        "pilot_owner",
        "outcome_lock_record",
        True,
        "once_at_cohort_close",
    ),
    ChecklistItem(
        "EXIT-06",
        EXIT,
        "Complete clinical, security, privacy and product debrief",
        "pilot_owner",
        "pilot_debrief",
        True,
        "once_at_cohort_close",
    ),
)


def validated_checklist_registry() -> tuple[ChecklistItem, ...]:
    seen: set[str] = set()
    phases: set[str] = set()
    for item in CHECKLIST_ITEMS:
        item.validate()
        if item.item_id in seen:
            raise ValueError(f"duplicate checklist item: {item.item_id}")
        seen.add(item.item_id)
        phases.add(item.phase)
    if phases != set(_PHASES):
        raise ValueError("pilot checklist phases are incomplete")
    if not all(any(item.phase == phase and item.blocking for item in CHECKLIST_ITEMS) for phase in _PHASES):
        raise ValueError("every pilot checklist phase requires a blocking item")
    return CHECKLIST_ITEMS


def checklist_registry_payload() -> dict[str, object]:
    items = validated_checklist_registry()
    return {
        "schema_version": "1.0",
        "policy_owner": "IAmina Pilot Operations",
        "effective_on": "2026-08-02",
        "review_due_on": "2026-11-02",
        "phases": list(_PHASES),
        "items": [asdict(item) for item in items],
    }


def build_cohort_checklist(
    cohort_id: str,
    *,
    generated_at: datetime | None = None,
) -> dict[str, object]:
    if not _OPAQUE_COHORT_ID.fullmatch(cohort_id):
        raise ValueError("cohort_id must be an opaque uppercase identifier")
    timestamp = generated_at or timezone.now()
    if timezone.is_naive(timestamp):
        raise ValueError("generated_at must be timezone-aware")
    items = validated_checklist_registry()
    return {
        "schema_version": "1.0",
        "cohort_id": cohort_id,
        "generated_at": timestamp.isoformat(),
        "status": PENDING,
        "items": [
            {
                **asdict(item),
                "status": PENDING,
                "evidence_reference": None,
                "reviewed_by_role": None,
                "reviewed_at": None,
                "not_applicable_rationale": None,
            }
            for item in items
        ],
    }


def validate_completed_checklist(payload: dict[str, object]) -> None:
    """Fail unless every blocking item has approved evidence."""
    registry = {item.item_id: item for item in validated_checklist_registry()}
    if payload.get("schema_version") != "1.0":
        raise ValueError("unsupported checklist schema version")
    cohort_id = payload.get("cohort_id")
    if not isinstance(cohort_id, str) or not _OPAQUE_COHORT_ID.fullmatch(cohort_id):
        raise ValueError("invalid cohort_id")
    raw_items = payload.get("items")
    if not isinstance(raw_items, list):
        raise ValueError("checklist items are required")
    supplied: set[str] = set()
    for raw in raw_items:
        if not isinstance(raw, dict):
            raise ValueError("invalid checklist item payload")
        item_id = raw.get("item_id")
        if not isinstance(item_id, str) or item_id not in registry:
            raise ValueError(f"unknown checklist item: {item_id}")
        if item_id in supplied:
            raise ValueError(f"duplicate checklist result: {item_id}")
        supplied.add(item_id)
        status = raw.get("status")
        if status not in _STATUSES:
            raise ValueError(f"invalid status for {item_id}")
        evidence = raw.get("evidence_reference")
        role = raw.get("reviewed_by_role")
        reviewed_at = raw.get("reviewed_at")
        rationale = raw.get("not_applicable_rationale")
        if status == PASS:
            if not isinstance(evidence, str) or not _OPAQUE_EVIDENCE_ID.fullmatch(evidence):
                raise ValueError(f"approved evidence reference required for {item_id}")
            if role != registry[item_id].owner_role:
                raise ValueError(f"owner role must approve {item_id}")
            if not isinstance(reviewed_at, str) or not reviewed_at.strip():
                raise ValueError(f"review timestamp required for {item_id}")
        elif status == NOT_APPLICABLE:
            if registry[item_id].blocking:
                raise ValueError(f"blocking item cannot be not applicable: {item_id}")
            if not isinstance(rationale, str) or len(rationale.strip()) < 20:
                raise ValueError(f"not-applicable rationale required for {item_id}")
        elif registry[item_id].blocking:
            raise ValueError(f"blocking checklist item remains pending: {item_id}")
    missing = sorted(set(registry).difference(supplied))
    if missing:
        raise ValueError("checklist results missing: " + ", ".join(missing))
