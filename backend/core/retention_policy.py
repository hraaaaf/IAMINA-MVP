"""Versioned pilot retention and deletion schedule.

The values are IAmina operating rules for the pilot, not statements of statutory
minimums. Legal holds and approved contractual obligations always suspend deletion.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date

ROLLING = "rolling"
ACCOUNT_DELETION = "account_deletion"
CRYPTOGRAPHIC_EXPIRY = "cryptographic_expiry"
NOT_PERSISTED = "not_persisted"
INFRASTRUCTURE_EXPIRY = "infrastructure_expiry"


@dataclass(frozen=True, slots=True)
class RetentionRule:
    dataset: str
    trigger: str
    retention_days: int
    deletion_action: str
    owner: str
    effective_on: date
    review_due_on: date
    legal_hold_supported: bool
    notes: str = ""

    def validate(self, *, today: date | None = None) -> None:
        current = today or date.today()
        if not self.dataset.strip() or not self.owner.strip():
            raise ValueError("retention dataset and owner are required")
        if self.trigger not in {
            ROLLING,
            ACCOUNT_DELETION,
            CRYPTOGRAPHIC_EXPIRY,
            NOT_PERSISTED,
            INFRASTRUCTURE_EXPIRY,
        }:
            raise ValueError(f"unknown retention trigger for {self.dataset}")
        if self.retention_days < 0:
            raise ValueError(f"negative retention for {self.dataset}")
        if self.effective_on > current:
            raise ValueError(f"retention rule not effective for {self.dataset}")
        if self.review_due_on < current:
            raise ValueError(f"retention rule stale for {self.dataset}")
        if not self.deletion_action.strip():
            raise ValueError(f"deletion action missing for {self.dataset}")
        if self.trigger == NOT_PERSISTED and self.retention_days != 0:
            raise ValueError(f"non-persisted dataset must have zero retention: {self.dataset}")


_POLICY_OWNER = "IAmina Privacy & Security"
_EFFECTIVE = date(2026, 8, 2)
_REVIEW_DUE = date(2026, 11, 2)

RETENTION_RULES: tuple[RetentionRule, ...] = (
    RetentionRule(
        dataset="raw_ai_media_in_application",
        trigger=NOT_PERSISTED,
        retention_days=0,
        deletion_action="discard after bounded request processing",
        owner=_POLICY_OWNER,
        effective_on=_EFFECTIVE,
        review_due_on=_REVIEW_DUE,
        legal_hold_supported=False,
        notes="The application does not persist uploaded audio, images or documents after processing.",
    ),
    RetentionRule(
        dataset="patient_export_staging_files",
        trigger=ROLLING,
        retention_days=7,
        deletion_action="securely remove restricted staging file",
        owner=_POLICY_OWNER,
        effective_on=_EFFECTIVE,
        review_due_on=_REVIEW_DUE,
        legal_hold_supported=True,
        notes="Delivery copies must be removed sooner when delivery is confirmed.",
    ),
    RetentionRule(
        dataset="password_reset_tokens",
        trigger=CRYPTOGRAPHIC_EXPIRY,
        retention_days=1,
        deletion_action="invalidate by expiry and token-version rotation",
        owner=_POLICY_OWNER,
        effective_on=_EFFECTIVE,
        review_due_on=_REVIEW_DUE,
        legal_hold_supported=False,
    ),
    RetentionRule(
        dataset="patient_application_records",
        trigger=ACCOUNT_DELETION,
        retention_days=30,
        deletion_action="delete owned records through Django relational cascade",
        owner=_POLICY_OWNER,
        effective_on=_EFFECTIVE,
        review_due_on=_REVIEW_DUE,
        legal_hold_supported=True,
        notes="Thirty-day grace period starts after verified deletion request and export offer.",
    ),
    RetentionRule(
        dataset="security_audit_logs",
        trigger=ROLLING,
        retention_days=2190,
        deletion_action="delete expired event or retain under documented legal hold",
        owner=_POLICY_OWNER,
        effective_on=_EFFECTIVE,
        review_due_on=_REVIEW_DUE,
        legal_hold_supported=True,
        notes="Account deletion detaches the actor while retaining the security event.",
    ),
    RetentionRule(
        dataset="encrypted_backups",
        trigger=INFRASTRUCTURE_EXPIRY,
        retention_days=35,
        deletion_action="expire immutable backup according to provider lifecycle policy",
        owner=_POLICY_OWNER,
        effective_on=_EFFECTIVE,
        review_due_on=_REVIEW_DUE,
        legal_hold_supported=True,
        notes="Restored data remains subject to deletion tombstone replay.",
    ),
)


def validated_retention_schedule(*, today: date | None = None) -> tuple[RetentionRule, ...]:
    seen: set[str] = set()
    for rule in RETENTION_RULES:
        rule.validate(today=today)
        if rule.dataset in seen:
            raise ValueError(f"duplicate retention dataset: {rule.dataset}")
        seen.add(rule.dataset)
    return RETENTION_RULES


def retention_schedule_payload(*, today: date | None = None) -> dict[str, object]:
    rules = validated_retention_schedule(today=today)
    return {
        "schema_version": "1.0",
        "policy_owner": _POLICY_OWNER,
        "rules": [
            {
                **asdict(rule),
                "effective_on": rule.effective_on.isoformat(),
                "review_due_on": rule.review_due_on.isoformat(),
            }
            for rule in rules
        ],
    }
