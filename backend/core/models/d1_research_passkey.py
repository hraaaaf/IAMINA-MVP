"""D1 research-only owner-scoped WebAuthn ceremony records.

Not mounted on the public API and NOT an authorization to unlock clinical data.
No patient data or DEK is stored here. Each challenge is one-time and short-lived.
"""
from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models


class D1ResearchPasskeyCredential(models.Model):
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="d1_research_passkeys",
    )
    credential_id = models.CharField(max_length=1024, unique=True)
    public_key = models.BinaryField()
    user_handle = models.BinaryField()
    sign_count = models.PositiveBigIntegerField(default=0)
    rp_id = models.CharField(max_length=255)
    origin = models.URLField(max_length=512)
    created_at = models.DateTimeField(auto_now_add=True)
    revoked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        app_label = "core"
        indexes = [models.Index(fields=["patient", "revoked_at"], name="d1_prf_owner_rev_idx")]


class D1ResearchPasskeyChallenge(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="d1_research_passkey_challenges",
    )
    credential = models.ForeignKey(
        D1ResearchPasskeyCredential, on_delete=models.CASCADE,
        null=True, blank=True,
    )
    purpose = models.CharField(
        max_length=16,
        choices=[("enroll", "Enroll"), ("verify", "Verify")],
    )
    challenge = models.BinaryField()
    user_handle = models.BinaryField()
    origin = models.URLField(max_length=512)
    rp_id = models.CharField(max_length=255)
    auth_token_version = models.PositiveIntegerField()
    session_key = models.CharField(max_length=80)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    consumed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        app_label = "core"
        indexes = [
            models.Index(fields=["patient", "purpose", "expires_at"], name="d1_prf_chal_owner_idx"),
        ]
