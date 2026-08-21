"""Persistent non-PHI FinOps models for atomic AI budget accounting."""

from django.db import models


class AIBudgetAccount(models.Model):
    """Aggregate committed AI spend for one opaque budget subject and month."""

    subject_key = models.CharField(max_length=160)
    month_key = models.CharField(max_length=7)
    committed_microusd = models.BigIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "core"
        db_table = "core_ai_budget_account"
        constraints = [
            models.UniqueConstraint(
                fields=("subject_key", "month_key"),
                name="uniq_ai_budget_subject_month",
            ),
        ]


class AIBudgetReservationRecord(models.Model):
    """Persistent reservation state with durable retry idempotency."""

    reservation_id = models.CharField(max_length=32, primary_key=True)
    account = models.ForeignKey(
        AIBudgetAccount,
        on_delete=models.PROTECT,
        related_name="reservations",
    )
    idempotency_key = models.CharField(max_length=160, null=True, blank=True)
    reserved_microusd = models.BigIntegerField()
    settled_microusd = models.BigIntegerField(null=True, blank=True)
    cancelled = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "core"
        db_table = "core_ai_budget_reservation"
        constraints = [
            models.UniqueConstraint(
                fields=("account", "idempotency_key"),
                name="uniq_ai_budget_account_idempotency",
            ),
        ]
