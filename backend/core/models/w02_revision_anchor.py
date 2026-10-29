"""W02/D10 metadata-only monotonic server revision anchor.

No patient records, encryption keys, recovery secrets, or ciphertext are held.
Only Preview, guarded endpoints may mutate this model. CAS relies on PG row lock.
"""
from django.conf import settings
from django.db import models


class W02VaultRevisionAnchor(models.Model):
    patient = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="w02_revision_anchor",
    )
    slot = models.CharField(max_length=43, unique=True)
    committed_revision = models.PositiveBigIntegerField(default=0)
    committed_envelope_sha256 = models.CharField(max_length=64, blank=True, default="")
    pending_revision = models.PositiveBigIntegerField(null=True, blank=True)
    pending_ticket = models.CharField(max_length=43, blank=True, default="")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "core"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(committed_revision__gte=0),
                name="core_w02_committed_nonnegative",
            ),
        ]
