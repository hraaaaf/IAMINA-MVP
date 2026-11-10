"""CAL-12 synthetic-only export consent ledger.

These database rows are technical rehearsal evidence, never permission to
export medical records. No PHI, delivery address, file bytes or clinician name.
"""
from django.conf import settings
from django.db import models


class Cal12ExportConsentFixtureReceipt(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="cal12_fixture_export_receipts",
    )
    revision = models.PositiveIntegerField()
    notice_version = models.CharField(max_length=48)
    notice_sha256 = models.CharField(max_length=64)
    notice_locale = models.CharField(max_length=8)
    purpose = models.CharField(max_length=48)
    data_category = models.CharField(max_length=48)
    recipient_ref = models.CharField(max_length=64)
    channel = models.CharField(max_length=32)
    period_start_utc = models.DateTimeField()
    period_end_utc = models.DateTimeField()
    recipient_confirmed_at = models.DateTimeField()
    granted_at = models.DateTimeField()
    expires_at = models.DateTimeField()
    revoked_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "core"
        ordering = ("-revision",)
        constraints = [
            models.UniqueConstraint(
                fields=("owner", "revision"),
                name="core_cal12_fixture_owner_rev_unique",
            ),
        ]
        indexes = [
            models.Index(
                fields=("owner", "revoked_at", "expires_at"),
                name="core_cal12_fixture_active",
            ),
        ]


class Cal12ExportConsentFixtureEvent(models.Model):
    """One minimal event per transition, cascades on account erasure."""

    receipt = models.ForeignKey(
        Cal12ExportConsentFixtureReceipt,
        on_delete=models.CASCADE,
        related_name="events",
    )
    kind = models.CharField(
        max_length=16,
        choices=[
            ("granted", "Granted"),
            ("revoked", "Revoked"),
            ("superseded", "Superseded"),
        ],
    )
    occurred_at = models.DateTimeField()

    class Meta:
        app_label = "core"
        ordering = ("id",)
        constraints = [
            models.UniqueConstraint(
                fields=("receipt", "kind"),
                name="core_cal12_fixture_event_once",
            ),
        ]
