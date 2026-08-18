"""Fail-closed preflight contract for paid/network provider benchmarks.

This module never invokes a provider and never stores credential values. It only
validates that an explicit authorization, bounded spend, exact model identity,
controlled pricing evidence and minimized synthetic dataset are present before a
network benchmark may be attempted elsewhere.
"""

from __future__ import annotations

from dataclasses import dataclass


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
        if not self.credential_reference.startswith("env:"):
            raise ProviderBenchmarkBlocked(
                "credential_reference must name an out-of-source-control env secret"
            )
