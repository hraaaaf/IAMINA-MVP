"""Pure monthly FinOps reconciliation helpers for privacy-safe cost telemetry."""

from __future__ import annotations

import re
from dataclasses import dataclass

_BILLING_EVIDENCE_KINDS = frozenset(
    {"invoice", "provider_statement", "dashboard_export"}
)
_BILLING_PERIOD_RE = re.compile(r"^\d{4}-(?:0[1-9]|1[0-2])$")


@dataclass(frozen=True, slots=True)
class BillingEvidence:
    """Traceable aggregate billing proof without patient or payload content."""

    provider: str
    billing_period: str
    source_kind: str
    reference: str

    def validate(self) -> None:
        if not self.provider.strip():
            raise ValueError("billing provider is required")
        if not _BILLING_PERIOD_RE.fullmatch(self.billing_period):
            raise ValueError("billing_period must be YYYY-MM")
        if self.source_kind not in _BILLING_EVIDENCE_KINDS:
            raise ValueError(f"unsupported billing evidence kind: {self.source_kind}")
        if not self.reference.strip():
            raise ValueError("billing evidence reference is required")


@dataclass(frozen=True, slots=True)
class MonthlyCostSnapshot:
    active_users: int
    billed_microusd: int
    explained_microusd: int
    workload_costs_microusd: tuple[tuple[str, int], ...]
    billing_evidence: BillingEvidence | None = None

    def validate(self) -> None:
        if self.active_users <= 0:
            raise ValueError("active_users must be positive")
        if self.billed_microusd < 0 or self.explained_microusd < 0:
            raise ValueError("costs cannot be negative")
        if self.explained_microusd > self.billed_microusd:
            raise ValueError("explained cost cannot exceed billed cost")

        names = [name for name, _ in self.workload_costs_microusd]
        if any(not name.strip() for name in names):
            raise ValueError("workload names must be non-empty")
        if len(names) != len(set(names)):
            raise ValueError("workload names must be unique")
        if any(cost < 0 for _, cost in self.workload_costs_microusd):
            raise ValueError("workload costs cannot be negative")
        if sum(cost for _, cost in self.workload_costs_microusd) != self.explained_microusd:
            raise ValueError("workload costs must reconcile to explained cost")

        if self.billing_evidence is not None:
            self.billing_evidence.validate()

    @property
    def unexplained_microusd(self) -> int:
        self.validate()
        return self.billed_microusd - self.explained_microusd

    @property
    def reconciliation_ratio(self) -> float:
        """Mathematical coverage ratio; certification still requires billing evidence."""
        self.validate()
        if self.billed_microusd == 0:
            return 1.0
        return self.explained_microusd / self.billed_microusd

    @property
    def billed_microusd_per_mau(self) -> float:
        self.validate()
        return self.billed_microusd / self.active_users

    @property
    def costs_by_workload_microusd(self) -> dict[str, int]:
        self.validate()
        return dict(self.workload_costs_microusd)

    def reconciliation_status(self, floor: float = 0.95) -> str:
        if not 0 < floor <= 1:
            raise ValueError("floor must be in (0, 1]")
        if self.billing_evidence is None:
            return "unresolved_without_billing_evidence"
        if self.reconciliation_ratio >= floor:
            return "reconciled"
        return "below_reconciliation_floor"

    def meets_reconciliation_floor(self, floor: float = 0.95) -> bool:
        return self.reconciliation_status(floor) == "reconciled"


def reconcile_month(
    *,
    active_users: int,
    billed_microusd: int,
    workload_costs_microusd: dict[str, int],
    billing_evidence: BillingEvidence | None = None,
) -> MonthlyCostSnapshot:
    """Reconcile workload costs against a traceable provider billing aggregate.

    Only aggregate cost numbers and non-sensitive billing metadata enter this helper.
    It intentionally accepts no patient identifiers, prompt/media content, object
    keys, document text, account secrets or payment-card data.
    """
    if any(not name.strip() for name in workload_costs_microusd):
        raise ValueError("workload names must be non-empty")
    if any(cost < 0 for cost in workload_costs_microusd.values()):
        raise ValueError("workload costs cannot be negative")

    workload_items = tuple(sorted(workload_costs_microusd.items()))
    snapshot = MonthlyCostSnapshot(
        active_users=active_users,
        billed_microusd=billed_microusd,
        explained_microusd=sum(cost for _, cost in workload_items),
        workload_costs_microusd=workload_items,
        billing_evidence=billing_evidence,
    )
    snapshot.validate()
    return snapshot
