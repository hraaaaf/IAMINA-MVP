"""Persistent atomic implementation of the provider-neutral AI budget ledger."""

from __future__ import annotations

from uuid import uuid4

from django.db import transaction

from core.models import AIBudgetAccount, AIBudgetReservationRecord

from .budget import BudgetAccountingError, BudgetExceeded, BudgetReservation


class PersistentBudgetLedger:
    """DB-backed budget ledger with row-locked reservation accounting.

    The account row is the serialization point for one opaque subject/month.
    PostgreSQL `SELECT ... FOR UPDATE` prevents concurrent workers from
    authorizing reservations that collectively cross the hard ceiling.
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
