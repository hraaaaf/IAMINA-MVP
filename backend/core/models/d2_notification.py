"""D2 account-scoped, code-only in-app notices; never store medical content.

The table is not a message bus, a clinical triage engine or a browser push queue.
Only audited, allowlisted server source events may create event notices.
"""
from django.conf import settings
from django.db import models


class D2NotificationPreference(models.Model):
    patient = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="d2_notification_preference",
    )
    proactive_opt_in = models.BooleanField(default=False)
    notice_version = models.CharField(max_length=48, blank=True, default="")
    notice_digest = models.CharField(max_length=64, blank=True, default="")
    granted_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "core"


class D2Notification(models.Model):
    KIND_CHOICES = (("event", "Event"), ("proactive", "Proactive"))
    CODE_CHOICES = (
        ("ai_consent_given", "AI consent confirmed"),
        ("ai_consent_withdrawn", "AI consent withdrawn"),
        ("language_pref_available", "Language preference available"),
    )
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="d2_notifications",
    )
    # SHA256 keyed to a source row, patient and code. No clinical or free text.
    event_key = models.CharField(max_length=64)
    kind = models.CharField(max_length=12, choices=KIND_CHOICES)
    code = models.CharField(max_length=48, choices=CODE_CHOICES)
    created_at = models.DateTimeField()
    expires_at = models.DateTimeField()
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        app_label = "core"
        ordering = ("-created_at", "-id")
        constraints = [
            models.UniqueConstraint(
                fields=("patient", "event_key"),
                name="core_d2_notice_event_key_unique",
            ),
        ]
        indexes = [
            models.Index(
                fields=("patient", "expires_at", "created_at"),
                name="core_d2_notice_owner_active",
            ),
        ]
