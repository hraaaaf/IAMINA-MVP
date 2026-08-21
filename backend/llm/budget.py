"""Provider-neutral fail-closed AI budget reservation contract.

This module intentionally does not guess provider prices. Callers must supply
explicit micro-USD reservation/settlement amounts derived from controlled price
configuration before this contract is wired into runtime egress.
"""

from __future__ import annotations

from dataclasses import dataclass
from threading import Lock
from typing import Protocol
from uuid import uuid4


class BudgetExceeded(RuntimeError):
    """Raised before a paid operation when its reservation would exceed budget."""


class BudgetAccountingError(RuntimeError):
    """Raised when settlement cannot be reconciled safely."""


class BudgetConfigurationError(ValueError):
    """Raised when a fail-closed budget policy is incomplete or ambiguous."""


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
class BudgetScopeLimit:
    """One atomic accounting scope with soft and hard monthly thresholds."""

    subject_key: str
    monthly_limit_microusd: int
    soft_alert_threshold_microusd: int

    def validate(self) -> None:
        if not self.subject_key.strip():
            raise BudgetConfigurationError("budget scope subject_key is required")
        if self.monthly_limit_microusd <= 0:
            raise BudgetConfigurationError("scope monthly limit must be positive")
        if self.soft_alert_threshold_microusd <= 0:
            raise BudgetConfigurationError("scope soft alert threshold must be positive")
        if self.soft_alert_threshold_microusd > self.monthly_limit_microusd:
            raise BudgetConfigurationError("soft alert threshold cannot exceed hard limit")


@dataclass(frozen=True, slots=True)
class BudgetReservation:
    reservation_id: str
    subject_key: str
    month_key: str
    reserved_microusd: int
    idempotency_key: str | None = None


@dataclass(frozen=True, slots=True)
class BudgetReservationBundle:
    """One paid operation reserved against every required budget dimension."""

    reservations: tuple[BudgetReservation, ...]
    soft_alert_subject_keys: tuple[str, ...] = ()

    def validate(self) -> None:
        if not self.reservations:
            raise BudgetAccountingError("budget reservation bundle cannot be empty")
        ids = tuple(item.reservation_id for item in self.reservations)
        if len(ids) != len(set(ids)):
            raise BudgetAccountingError("budget reservation bundle contains duplicate ids")


class BudgetLedger(Protocol):
    """Storage contract for atomic budget reservation and reconciliation."""

    def committed_microusd(self, subject_key: str, month_key: str) -> int: ...

    def reserve_if_within(
        self,
        *,
        subject_key: str,
        month_key: str,
        amount_microusd: int,
        monthly_limit_microusd: int,
        idempotency_key: str | None = None,
    ) -> BudgetReservation: ...

    def reserve_bundle_if_within(
        self,
        *,
        scopes: tuple[BudgetScopeLimit, ...],
        month_key: str,
        amount_microusd: int,
        idempotency_key: str,
    ) -> BudgetReservationBundle: ...

    def settle(self, reservation_id: str, actual_microusd: int) -> None: ...

    def settle_bundle(
        self, bundle: BudgetReservationBundle, actual_microusd: int
    ) -> None: ...

    def cancel(self, reservation_id: str) -> None: ...

    def cancel_bundle(self, bundle: BudgetReservationBundle) -> None: ...


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

    def _idempotent_reservation(
        self,
        *,
        subject_key: str,
        month_key: str,
        amount_microusd: int,
        idempotency_key: str,
    ) -> BudgetReservation | None:
        for state in self._states.values():
            reservation = state.reservation
            if (
                reservation.subject_key == subject_key
                and reservation.month_key == month_key
                and reservation.idempotency_key == idempotency_key
            ):
                if state.cancelled:
                    raise BudgetAccountingError(
                        "idempotency key belongs to a cancelled reservation"
                    )
                if reservation.reserved_microusd != amount_microusd:
                    raise BudgetAccountingError(
                        "idempotency key cannot authorize a different amount"
                    )
                return reservation
        return None

    @staticmethod
    def _validated_scopes(
        scopes: tuple[BudgetScopeLimit, ...],
    ) -> tuple[BudgetScopeLimit, ...]:
        if not scopes:
            raise BudgetConfigurationError("at least one budget scope is required")
        for scope in scopes:
            scope.validate()
        subject_keys = tuple(scope.subject_key for scope in scopes)
        if len(subject_keys) != len(set(subject_keys)):
            raise BudgetConfigurationError("budget scopes must have unique subject keys")
        return tuple(sorted(scopes, key=lambda item: item.subject_key))

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
        idempotency_key: str | None = None,
    ) -> BudgetReservation:
        with self._lock:
            if idempotency_key is not None:
                existing = self._idempotent_reservation(
                    subject_key=subject_key,
                    month_key=month_key,
                    amount_microusd=amount_microusd,
                    idempotency_key=idempotency_key,
                )
                if existing is not None:
                    return existing

            committed = self._committed_microusd(subject_key, month_key)
            if committed + amount_microusd > monthly_limit_microusd:
                raise BudgetExceeded("AI monthly budget would be exceeded")
            reservation = BudgetReservation(
                reservation_id=uuid4().hex,
                subject_key=subject_key,
                month_key=month_key,
                reserved_microusd=amount_microusd,
                idempotency_key=idempotency_key,
            )
            self._states[reservation.reservation_id] = _ReservationState(reservation)
            return reservation

    def reserve_bundle_if_within(
        self,
        *,
        scopes: tuple[BudgetScopeLimit, ...],
        month_key: str,
        amount_microusd: int,
        idempotency_key: str,
    ) -> BudgetReservationBundle:
        ordered = self._validated_scopes(scopes)
        if amount_microusd <= 0:
            raise ValueError("amount_microusd must be positive")
        if not idempotency_key.strip():
            raise ValueError("bundle idempotency_key is required")

        with self._lock:
            existing = tuple(
                self._idempotent_reservation(
                    subject_key=scope.subject_key,
                    month_key=month_key,
                    amount_microusd=amount_microusd,
                    idempotency_key=idempotency_key,
                )
                for scope in ordered
            )
            existing_count = sum(item is not None for item in existing)
            if existing_count not in (0, len(ordered)):
                raise BudgetAccountingError("partial idempotent bundle state detected")
            if existing_count == len(ordered):
                reservations = tuple(item for item in existing if item is not None)
                soft = tuple(
                    scope.subject_key
                    for scope in ordered
                    if self._committed_microusd(scope.subject_key, month_key)
                    >= scope.soft_alert_threshold_microusd
                )
                return BudgetReservationBundle(reservations, soft)

            for scope in ordered:
                committed = self._committed_microusd(scope.subject_key, month_key)
                if committed + amount_microusd > scope.monthly_limit_microusd:
                    raise BudgetExceeded(
                        f"AI monthly budget would be exceeded for scope {scope.subject_key}"
                    )

            reservations: list[BudgetReservation] = []
            for scope in ordered:
                reservation = BudgetReservation(
                    reservation_id=uuid4().hex,
                    subject_key=scope.subject_key,
                    month_key=month_key,
                    reserved_microusd=amount_microusd,
                    idempotency_key=idempotency_key,
                )
                self._states[reservation.reservation_id] = _ReservationState(reservation)
                reservations.append(reservation)

            soft = tuple(
                scope.subject_key
                for scope in ordered
                if self._committed_microusd(scope.subject_key, month_key)
                >= scope.soft_alert_threshold_microusd
            )
            return BudgetReservationBundle(tuple(reservations), soft)

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

    def settle_bundle(
        self, bundle: BudgetReservationBundle, actual_microusd: int
    ) -> None:
        bundle.validate()
        if actual_microusd < 0:
            raise BudgetAccountingError("actual cost cannot be negative")
        with self._lock:
            states: list[_ReservationState] = []
            for reservation in bundle.reservations:
                state = self._states.get(reservation.reservation_id)
                if state is None or state.cancelled:
                    raise BudgetAccountingError("unknown or cancelled budget reservation")
                if state.settled_microusd is not None:
                    raise BudgetAccountingError("budget reservation already settled")
                if actual_microusd > state.reservation.reserved_microusd:
                    raise BudgetAccountingError(
                        "actual cost exceeds the pre-authorized reservation"
                    )
                states.append(state)
            for state in states:
                state.settled_microusd = actual_microusd

    def cancel(self, reservation_id: str) -> None:
        with self._lock:
            state = self._states.get(reservation_id)
            if state is None or state.settled_microusd is not None:
                raise BudgetAccountingError("reservation cannot be cancelled")
            state.cancelled = True

    def cancel_bundle(self, bundle: BudgetReservationBundle) -> None:
        bundle.validate()
        with self._lock:
            states: list[_ReservationState] = []
            for reservation in bundle.reservations:
                state = self._states.get(reservation.reservation_id)
                if state is None or state.settled_microusd is not None:
                    raise BudgetAccountingError("reservation bundle cannot be cancelled")
                states.append(state)
            for state in states:
                state.cancelled = True


class BudgetController:
    """Reserve before paid work; settle only against explicit actual cost."""

    def __init__(self, policy: BudgetPolicy, ledger: BudgetLedger) -> None:
        policy.validate()
        self.policy = policy
        self.ledger = ledger

    def authorize(
        self,
        *,
        subject_key: str,
        month_key: str,
        reserved_microusd: int,
        idempotency_key: str | None = None,
    ) -> BudgetReservation:
        if not subject_key.strip() or not month_key.strip():
            raise ValueError("subject_key and month_key are required")
        if reserved_microusd <= 0:
            raise ValueError("reserved_microusd must be positive")
        if idempotency_key is not None and not idempotency_key.strip():
            raise ValueError("idempotency_key must be non-empty when provided")
        if reserved_microusd > self.policy.max_single_reservation_microusd:
            raise BudgetExceeded("AI call reservation exceeds the single-call ceiling")
        return self.ledger.reserve_if_within(
            subject_key=subject_key,
            month_key=month_key,
            amount_microusd=reserved_microusd,
            monthly_limit_microusd=self.policy.monthly_limit_microusd,
            idempotency_key=idempotency_key,
        )

    def settle(self, reservation: BudgetReservation, actual_microusd: int) -> None:
        self.ledger.settle(reservation.reservation_id, actual_microusd)

    def cancel(self, reservation: BudgetReservation) -> None:
        self.ledger.cancel(reservation.reservation_id)
