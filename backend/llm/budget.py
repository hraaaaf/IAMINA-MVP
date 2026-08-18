"""Provider-neutral fail-closed AI budget reservation contract.

This module intentionally does not guess provider prices. Callers must supply
explicit micro-USD reservation/settlement amounts derived from controlled price
configuration before this contract is wired into runtime egress.
"""

from __future__ import annotations

from dataclasses import dataclass
from threading import Lock
from uuid import uuid4


class BudgetExceeded(RuntimeError):
    """Raised before a paid operation when its reservation would exceed budget."""


class BudgetAccountingError(RuntimeError):
    """Raised when settlement cannot be reconciled safely."""


@dataclass(frozen=True, slots=True)
class BudgetPolicy:
    monthly_limit_microusd: int
    max_single_reservation_microusd: int

    def validate(self) -> None:
        if self.monthly_limit_microusd <= 0:
            raise ValueError("monthly_limit_microusd must be positive")
        if self.max_single_reservation_microusd <= 0:
            raise ValueError("max_single_reservation_microusd must be positive")
        if self.max_single_reservation_microusd > self.monthly_limit_microusd:
            raise ValueError("single-call reservation cannot exceed monthly budget")


@dataclass(frozen=True, slots=True)
class BudgetReservation:
    reservation_id: str
    subject_key: str
    month_key: str
    reserved_microusd: int


@dataclass(slots=True)
class _ReservationState:
    reservation: BudgetReservation
    settled_microusd: int | None = None
    cancelled: bool = False


class InMemoryBudgetLedger:
    """Thread-safe reference ledger used by tests and non-persistent evaluation.

    Production wiring should provide a persistent atomic ledger with the same
    semantics. This class is deliberately not presented as production storage.
    """

    def __init__(self) -> None:
        self._lock = Lock()
        self._states: dict[str, _ReservationState] = {}

    def _committed_microusd(self, subject_key: str, month_key: str) -> int:
        total = 0
        for state in self._states.values():
            reservation = state.reservation
            if reservation.subject_key != subject_key or reservation.month_key != month_key:
                continue
            if state.cancelled:
                continue
            total += (
                state.settled_microusd
                if state.settled_microusd is not None
                else reservation.reserved_microusd
            )
        return total

    def committed_microusd(self, subject_key: str, month_key: str) -> int:
        with self._lock:
            return self._committed_microusd(subject_key, month_key)

    def reserve_if_within(
        self,
        *,
        subject_key: str,
        month_key: str,
        amount_microusd: int,
        monthly_limit_microusd: int,
    ) -> BudgetReservation:
        with self._lock:
            committed = self._committed_microusd(subject_key, month_key)
            if committed + amount_microusd > monthly_limit_microusd:
                raise BudgetExceeded("AI monthly budget would be exceeded")
            reservation = BudgetReservation(
                reservation_id=uuid4().hex,
                subject_key=subject_key,
                month_key=month_key,
                reserved_microusd=amount_microusd,
            )
            self._states[reservation.reservation_id] = _ReservationState(reservation)
            return reservation

    def settle(self, reservation_id: str, actual_microusd: int) -> None:
        with self._lock:
            state = self._states.get(reservation_id)
            if state is None or state.cancelled:
                raise BudgetAccountingError("unknown or cancelled budget reservation")
            if state.settled_microusd is not None:
                raise BudgetAccountingError("budget reservation already settled")
            if actual_microusd < 0:
                raise BudgetAccountingError("actual cost cannot be negative")
            if actual_microusd > state.reservation.reserved_microusd:
                raise BudgetAccountingError(
                    "actual cost exceeds the pre-authorized reservation"
                )
            state.settled_microusd = actual_microusd

    def cancel(self, reservation_id: str) -> None:
        with self._lock:
            state = self._states.get(reservation_id)
            if state is None or state.settled_microusd is not None:
                raise BudgetAccountingError("reservation cannot be cancelled")
            state.cancelled = True


class BudgetController:
    """Reserve before paid work; settle only against explicit actual cost."""

    def __init__(self, policy: BudgetPolicy, ledger: InMemoryBudgetLedger) -> None:
        policy.validate()
        self.policy = policy
        self.ledger = ledger

    def authorize(
        self,
        *,
        subject_key: str,
        month_key: str,
        reserved_microusd: int,
    ) -> BudgetReservation:
        if not subject_key.strip() or not month_key.strip():
            raise ValueError("subject_key and month_key are required")
        if reserved_microusd <= 0:
            raise ValueError("reserved_microusd must be positive")
        if reserved_microusd > self.policy.max_single_reservation_microusd:
            raise BudgetExceeded("AI call reservation exceeds the single-call ceiling")
        return self.ledger.reserve_if_within(
            subject_key=subject_key,
            month_key=month_key,
            amount_microusd=reserved_microusd,
            monthly_limit_microusd=self.policy.monthly_limit_microusd,
        )

    def settle(self, reservation: BudgetReservation, actual_microusd: int) -> None:
        self.ledger.settle(reservation.reservation_id, actual_microusd)

    def cancel(self, reservation: BudgetReservation) -> None:
        self.ledger.cancel(reservation.reservation_id)
