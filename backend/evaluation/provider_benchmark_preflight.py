"""Fail-closed preflight contract for paid/network provider benchmarks.

This module never invokes a provider and never stores credential values. It only
validates that an explicit authorization, bounded spend, exact model identity,
controlled pricing evidence and minimized synthetic dataset are present before a
network benchmark may be attempted elsewhere.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

ENV_REFERENCE_RE = re.compile(r"^env:[A-Z][A-Z0-9_]*$")


class ProviderBenchmarkBlocked(RuntimeError):
    """Raised when a paid/network benchmark is not explicitly authorized."""


@dataclass(frozen=True, slots=True)
class ProviderBenchmarkPreflight:
    provider: str
    model: str
    modality: str
    dataset_id: str
    credential_reference: str
    pricing_evidence_reference: str
    network_authorized: bool
    spend_ceiling_microusd: int
    patient_data: bool

    def validate(self) -> None:
        required = {
            "provider": self.provider,
            "model": self.model,
            "modality": self.modality,
            "dataset_id": self.dataset_id,
            "credential_reference": self.credential_reference,
            "pricing_evidence_reference": self.pricing_evidence_reference,
        }
        missing = tuple(name for name, value in required.items() if not value.strip())
        if missing:
            raise ProviderBenchmarkBlocked(
                "provider benchmark preflight incomplete: " + ", ".join(missing)
            )
        if self.patient_data:
            raise ProviderBenchmarkBlocked("provider benchmark must not use patient data")
        if not self.network_authorized:
            raise ProviderBenchmarkBlocked("explicit network/API authorization is required")
        if self.spend_ceiling_microusd <= 0:
            raise ProviderBenchmarkBlocked("positive explicit spend ceiling is required")
        if not ENV_REFERENCE_RE.fullmatch(self.credential_reference):
            raise ProviderBenchmarkBlocked(
                "credential_reference must be an env:VARIABLE name, never a secret value"
            )
