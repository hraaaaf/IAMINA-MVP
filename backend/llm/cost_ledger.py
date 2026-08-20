"""Pure monthly FinOps reconciliation helpers for privacy-safe cost telemetry."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MonthlyCostSnapshot:
    active_users: int
    billed_microusd: int
    explained_microusd: int

    def validate(self) -> None:
        if self.active_users <= 0:
            raise ValueError("active_users must be positive")
        if self.billed_microusd < 0 or self.explained_microusd < 0:
            raise ValueError("costs cannot be negative")
        if self.explained_microusd > self.billed_microusd:
            raise ValueError("explained cost cannot exceed billed cost")

    @property
    def unexplained_microusd(self) -> int:
        self.validate()
        return self.billed_microusd - self.explained_microusd

    @property
    def reconciliation_ratio(self) -> float:
        self.validate()
        if self.billed_microusd == 0:
            return 1.0
        return self.explained_microusd / self.billed_microusd

    @property
    def billed_microusd_per_mau(self) -> float:
        self.validate()
        return self.billed_microusd / self.active_users

    def meets_reconciliation_floor(self, floor: float = 0.95) -> bool:
        if not 0 < floor <= 1:
            raise ValueError("floor must be in (0, 1]")
        return self.reconciliation_ratio >= floor


def reconcile_month(
    *,
    active_users: int,
    billed_microusd: int,
    workload_costs_microusd: dict[str, int],
) -> MonthlyCostSnapshot:
    """Reconcile controlled workload estimates/settlements against provider billing.

    Only aggregate cost numbers enter this helper. It intentionally accepts no
    patient identifiers, prompt/media content, object keys or document text.
    """
    if any(not name.strip() for name in workload_costs_microusd):
        raise ValueError("workload names must be non-empty")
    if any(cost < 0 for cost in workload_costs_microusd.values()):
        raise ValueError("workload costs cannot be negative")
    snapshot = MonthlyCostSnapshot(
        active_users=active_users,
        billed_microusd=billed_microusd,
        explained_microusd=sum(workload_costs_microusd.values()),
    )
    snapshot.validate()
    return snapshot
