"""Provider-neutral retention policy contracts for patient data lifecycles."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class RetentionClass(StrEnum):
    TRANSIENT_EXTRACTION = "TRANSIENT_EXTRACTION"
    USER_RETAINED_ORIGINAL = "USER_RETAINED_ORIGINAL"
    GOVERNED_EVIDENCE = "GOVERNED_EVIDENCE"
    STRUCTURED_VERIFIED_FACTS = "STRUCTURED_VERIFIED_FACTS"


@dataclass(frozen=True)
class RetentionPolicy:
    storage_key: str
    retention_class: RetentionClass
    policy_basis: str
    destructive_ttl_seconds: int | None = None
    human_gate_required: bool = False
    approval_reference: str | None = None

    def __post_init__(self) -> None:
        if not self.storage_key.strip():
            raise ValueError("storage_key must be explicit")
        if not self.policy_basis.strip():
            raise ValueError("policy_basis must be explicit")
        if self.destructive_ttl_seconds is not None and self.destructive_ttl_seconds <= 0:
            raise ValueError("destructive_ttl_seconds must be positive")
        if (
            self.retention_class is RetentionClass.TRANSIENT_EXTRACTION
            and self.destructive_ttl_seconds is None
        ):
            raise ValueError("transient extraction data must have a bounded TTL")
        if (
            self.human_gate_required
            and self.destructive_ttl_seconds is not None
            and not (self.approval_reference or "").strip()
        ):
            raise ValueError(
                "destructive TTL behind a human/legal gate requires an approval_reference"
            )
