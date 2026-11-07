"""Candidate W02-F09-B Web refresh record. NO enabled HTTP endpoint.

Every stored credential is a keyed digest of high-entropy secret bytes;
no raw refresh token, browser cookie, clinical fields or personally entered
content is stored in these tables. Django's User is still identity authority.
"""
from django.conf import settings
from django.db import models


class WebRefreshFamily(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="web_refresh_candidate_families",
    )
    current_digest = models.CharField(max_length=64, unique=True)
    auth_version = models.PositiveIntegerField()
    issued_at = models.DateTimeField()
    last_rotated_at = models.DateTimeField()
    idle_deadline = models.DateTimeField()
    expires_at = models.DateTimeField()
    revoke_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        app_label = "core"
        indexes = [
            models.Index(
                fields=["user", "revoke_at"],
                name="core_wrf_user_rev_idx",
            ),
        ]


class WebRefreshConsumedSecret(models.Model):
    family = models.ForeignKey(
        WebRefreshFamily,
        on_delete=models.CASCADE,
        related_name="consumed_secrets",
    )
    digest = models.CharField(max_length=64, unique=True)
    consumed_at = models.DateTimeField()

    class Meta:
        app_label = "core"
        indexes = [
            models.Index(
                fields=["family", "consumed_at"],
                name="core_wrused_fam_date_idx",
            ),
        ]

class WebRefreshTransportNonce(models.Model):
    """Consumed signed BFF request nonce. Store only keyed digest, never raw."""

    nonce_digest = models.CharField(max_length=64, unique=True)
    seen_at = models.DateTimeField()
    expires_at = models.DateTimeField(db_index=True)

    class Meta:
        app_label = "core"
