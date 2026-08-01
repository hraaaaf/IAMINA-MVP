"""Fail-closed manifest for live text-provider benchmark execution."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, slots=True)
class TextProviderManifest:
    provider: str
    model: str
    credential_env_var: str
    evidence_owner: str
    evidence_source: str
    verified_on: date
    review_due_on: date
    no_training_confirmed: bool
    retention_confirmed: bool
    residency_confirmed: bool
    subprocessors_confirmed: bool
    approved_for_synthetic_benchmark: bool

    def validate(self, *, today: date) -> None:
        required_text = {
            "provider": self.provider,
            "model": self.model,
            "credential_env_var": self.credential_env_var,
            "evidence_owner": self.evidence_owner,
            "evidence_source": self.evidence_source,
        }
        missing = tuple(name for name, value in required_text.items() if not value.strip())
        if missing:
            raise ValueError("missing text benchmark manifest fields: " + ", ".join(missing))
        if self.review_due_on < today:
            raise ValueError("provider evidence is stale")
        if self.verified_on > today:
            raise ValueError("provider evidence verification date is in the future")
        approvals = (
            self.no_training_confirmed,
            self.retention_confirmed,
            self.residency_confirmed,
            self.subprocessors_confirmed,
            self.approved_for_synthetic_benchmark,
        )
        if not all(approvals):
            raise ValueError("provider is not eligible for live text benchmarking")
