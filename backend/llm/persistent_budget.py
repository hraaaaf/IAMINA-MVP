"""Persistent atomic implementation of the provider-neutral AI budget ledger."""

from __future__ import annotations

from uuid import uuid4

from django.db import transaction

from core.models import AIBudgetAccount, AIBudgetReservationRecord

from .budget import (
    BudgetAccountingError,
    BudgetConfigurationError,
    BudgetExceeded,
    BudgetReservation,
    BudgetReservationBundle,
    BudgetScopeLimit,
)


class PersistentBudgetLedger:
    """DB-backed budget ledger with row-locked reservation accounting.

    Account rows are serialization points. Multi-scope bundles lock accounts in
    deterministic subject-key order so global/provider/workload hard ceilings are
    checked and committed in one database transaction.
    """

    @staticmethod
    def _reservation(record: AIBudgetReservationRecord) -> BudgetReservation:
        return BudgetReservation(
            reservation_id=record.reservation_id,
            subject_key=record.account.subject_key,
            month_key=record.account.month_key,
            reserved_microusd=record.reserved_microusd,
            idempotency_key=record.idempotency_key,
        )

    @staticmethod
    def _locked_account(*, subject_key: str, month_key: str) -> AIBudgetAccount:
        account, _ = AIBudgetAccount.objects.get_or_create(
            subject_key=subject_key,
            month_key=month_key,
            defaults={"committed_microusd": 0},
        )
        return AIBudgetAccount.objects.select_for_update().get(pk=account.pk)

    @staticmethod
    def _validated_scopes(
        scopes: tuple[BudgetScopeLimit, ...],
    ) -> tuple[BudgetScopeLimit, ...]:
        if not scopes:
            raise BudgetConfigurationError("at least one budget scope is required")
        for scope in scopes:
            scope.validate()
        keys = tuple(scope.subject_key for scope in scopes)
        if len(keys) != len(set(keys)):
            raise BudgetConfigurationError("budget scopes must have unique subject keys")
        return tuple(sorted(scopes, key=lambda item: item.subject_key))

    def committed_microusd(self, subject_key: str, month_key: str) -> int:
        committed = (
            AIBudgetAccount.objects.filter(
                subject_key=subject_key,
                month_key=month_key,
            )
            .values_list("committed_microusd", flat=True)
            .first()
        )
        return int(committed or 0)

    def reserve_if_within(
        self,
        *,
        subject_key: str,
        month_key: str,
        amount_microusd: int,
        monthly_limit_microusd: int,
        idempotency_key: str | None = None,
    ) -> BudgetReservation:
        normalized_key = idempotency_key.strip() if idempotency_key else None
        with transaction.atomic():
            account = self._locked_account(
                subject_key=subject_key,
                month_key=month_key,
            )
            if normalized_key is not None:
                existing = (
                    AIBudgetReservationRecord.objects.select_related("account")
                    .filter(account=account, idempotency_key=normalized_key)
                    .first()
                )
                if existing is not None:
                    if existing.cancelled:
                        raise BudgetAccountingError(
                            "idempotency key belongs to a cancelled reservation"
                        )
                    if existing.reserved_microusd != amount_microusd:
                        raise BudgetAccountingError(
                            "idempotency key cannot authorize a different amount"
                        )
                    return self._reservation(existing)

            if account.committed_microusd + amount_microusd > monthly_limit_microusd:
                raise BudgetExceeded("AI monthly budget would be exceeded")

            record = AIBudgetReservationRecord.objects.create(
                reservation_id=uuid4().hex,
                account=account,
                idempotency_key=normalized_key,
                reserved_microusd=amount_microusd,
            )
            account.committed_microusd += amount_microusd
            account.save(update_fields=("committed_microusd", "updated_at"))
            return self._reservation(record)

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
        normalized_key = idempotency_key.strip()
        if not normalized_key:
            raise ValueError("bundle idempotency_key is required")

        with transaction.atomic():
            accounts = {
                scope.subject_key: self._locked_account(
                    subject_key=scope.subject_key,
                    month_key=month_key,
                )
                for scope in ordered
            }

            existing_records: list[AIBudgetReservationRecord | None] = []
            for scope in ordered:
                account = accounts[scope.subject_key]
                existing_records.append(
                    AIBudgetReservationRecord.objects.filter(
                        account=account,
                        idempotency_key=normalized_key,
                    ).first()
                )

            existing_count = sum(record is not None for record in existing_records)
            if existing_count not in (0, len(ordered)):
                raise BudgetAccountingError("partial idempotent bundle state detected")
            if existing_count == len(ordered):
                reservations: list[BudgetReservation] = []
                for record in existing_records:
                    assert record is not None
                    if record.cancelled:
                        raise BudgetAccountingError(
                            "idempotency key belongs to a cancelled reservation"
                        )
                    if record.reserved_microusd != amount_microusd:
                        raise BudgetAccountingError(
                            "idempotency key cannot authorize a different amount"
                        )
                    record.account = accounts[record.account.subject_key]
                    reservations.append(self._reservation(record))
                soft = tuple(
                    scope.subject_key
                    for scope in ordered
                    if accounts[scope.subject_key].committed_microusd
                    >= scope.soft_alert_threshold_microusd
                )
                return BudgetReservationBundle(tuple(reservations), soft)

            for scope in ordered:
                account = accounts[scope.subject_key]
                if account.committed_microusd + amount_microusd > scope.monthly_limit_microusd:
                    raise BudgetExceeded(
                        f"AI monthly budget would be exceeded for scope {scope.subject_key}"
                    )

            reservations = []
            for scope in ordered:
                account = accounts[scope.subject_key]
                record = AIBudgetReservationRecord.objects.create(
                    reservation_id=uuid4().hex,
                    account=account,
                    idempotency_key=normalized_key,
                    reserved_microusd=amount_microusd,
                )
                account.committed_microusd += amount_microusd
                account.save(update_fields=("committed_microusd", "updated_at"))
                reservations.append(self._reservation(record))

            soft = tuple(
                scope.subject_key
                for scope in ordered
                if accounts[scope.subject_key].committed_microusd
                >= scope.soft_alert_threshold_microusd
            )
            return BudgetReservationBundle(tuple(reservations), soft)

    @staticmethod
    def _locked_reservation(
        reservation_id: str,
    ) -> tuple[AIBudgetAccount, AIBudgetReservationRecord]:
        try:
            account_id = AIBudgetReservationRecord.objects.values_list(
                "account_id", flat=True
            ).get(reservation_id=reservation_id)
        except AIBudgetReservationRecord.DoesNotExist as exc:
            raise BudgetAccountingError("unknown budget reservation") from exc

        account = AIBudgetAccount.objects.select_for_update().get(pk=account_id)
        try:
            record = AIBudgetReservationRecord.objects.select_for_update().get(
                reservation_id=reservation_id
            )
        except AIBudgetReservationRecord.DoesNotExist as exc:
            raise BudgetAccountingError("unknown budget reservation") from exc
        record.account = account
        return account, record

    @staticmethod
    def _locked_bundle_records(
        bundle: BudgetReservationBundle,
    ) -> tuple[tuple[AIBudgetAccount, AIBudgetReservationRecord], ...]:
        bundle.validate()
        reservation_ids = tuple(item.reservation_id for item in bundle.reservations)
        rows = list(
            AIBudgetReservationRecord.objects.filter(
                reservation_id__in=reservation_ids
            ).values_list("reservation_id", "account_id")
        )
        if len(rows) != len(reservation_ids):
            raise BudgetAccountingError("unknown budget reservation in bundle")

        account_ids = tuple(sorted({account_id for _, account_id in rows}))
        accounts = {
            account.pk: account
            for account in AIBudgetAccount.objects.select_for_update()
            .filter(pk__in=account_ids)
            .order_by("pk")
        }
        records = {
            record.reservation_id: record
            for record in AIBudgetReservationRecord.objects.select_for_update().filter(
                reservation_id__in=reservation_ids
            )
        }
        pairs: list[tuple[AIBudgetAccount, AIBudgetReservationRecord]] = []
        for reservation in sorted(bundle.reservations, key=lambda item: item.reservation_id):
            record = records[reservation.reservation_id]
            account = accounts[record.account_id]
            record.account = account
            pairs.append((account, record))
        return tuple(pairs)

    def settle(self, reservation_id: str, actual_microusd: int) -> None:
        if actual_microusd < 0:
            raise BudgetAccountingError("actual cost cannot be negative")
        with transaction.atomic():
            account, record = self._locked_reservation(reservation_id)
            if record.cancelled:
                raise BudgetAccountingError("unknown or cancelled budget reservation")
            if record.settled_microusd is not None:
                raise BudgetAccountingError("budget reservation already settled")
            if actual_microusd > record.reserved_microusd:
                raise BudgetAccountingError(
                    "actual cost exceeds the pre-authorized reservation"
                )

            account.committed_microusd -= record.reserved_microusd - actual_microusd
            account.save(update_fields=("committed_microusd", "updated_at"))
            record.settled_microusd = actual_microusd
            record.save(update_fields=("settled_microusd", "updated_at"))

    def settle_bundle(
        self, bundle: BudgetReservationBundle, actual_microusd: int
    ) -> None:
        if actual_microusd < 0:
            raise BudgetAccountingError("actual cost cannot be negative")
        with transaction.atomic():
            pairs = self._locked_bundle_records(bundle)
            for _, record in pairs:
                if record.cancelled:
                    raise BudgetAccountingError("unknown or cancelled budget reservation")
                if record.settled_microusd is not None:
                    raise BudgetAccountingError("budget reservation already settled")
                if actual_microusd > record.reserved_microusd:
                    raise BudgetAccountingError(
                        "actual cost exceeds the pre-authorized reservation"
                    )
            for account, record in pairs:
                account.committed_microusd -= record.reserved_microusd - actual_microusd
                account.save(update_fields=("committed_microusd", "updated_at"))
                record.settled_microusd = actual_microusd
                record.save(update_fields=("settled_microusd", "updated_at"))

    def cancel(self, reservation_id: str) -> None:
        with transaction.atomic():
            account, record = self._locked_reservation(reservation_id)
            if record.settled_microusd is not None:
                raise BudgetAccountingError("reservation cannot be cancelled")
            if record.cancelled:
                return

            account.committed_microusd -= record.reserved_microusd
            account.save(update_fields=("committed_microusd", "updated_at"))
            record.cancelled = True
            record.save(update_fields=("cancelled", "updated_at"))

    def cancel_bundle(self, bundle: BudgetReservationBundle) -> None:
        with transaction.atomic():
            pairs = self._locked_bundle_records(bundle)
            for _, record in pairs:
                if record.settled_microusd is not None:
                    raise BudgetAccountingError("reservation bundle cannot be cancelled")
            for account, record in pairs:
                if record.cancelled:
                    continue
                account.committed_microusd -= record.reserved_microusd
                account.save(update_fields=("committed_microusd", "updated_at"))
                record.cancelled = True
                record.save(update_fields=("cancelled", "updated_at"))
