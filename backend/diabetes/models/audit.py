import hashlib

from django.contrib.auth.models import User
from django.db import models


class AuditLog(models.Model):
    """
    Immutable audit trail — RGPD Art. 30 record of processing.

    Design constraints:
    - No update: auto_now fields only, no editable fields.
    - No delete: the table itself is never pruned (legal retention obligation).
      Anonymisation is handled by nullifying patient FK on account deletion,
      not by row deletion.
    - ip_hash: one-way SHA-256 of the raw IP — never store the raw IP.
    """

    ACTION_CHOICES = [
        ("consent_given", "Consentement IA accordé"),
        ("consent_withdrawn", "Consentement IA retiré"),
        ("account_deleted", "Compte supprimé (RGPD)"),
        ("data_export", "Export données (RGPD)"),
        ("login", "Connexion"),
        ("password_change", "Changement de mot de passe"),
    ]

    # SET_NULL on delete: row is kept for audit trail, patient FK becomes NULL
    patient = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="audit_logs",
    )
    action = models.CharField(max_length=32, choices=ACTION_CHOICES, db_index=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    ip_hash = models.CharField(max_length=64, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        app_label = "diabetes"
        ordering = ["-timestamp"]
        verbose_name = "Audit Log"
        # Prevent accidental bulk-delete via admin or ORM
        default_permissions = ("add", "view")

    def __str__(self):
        pid = self.patient_id or "anonymised"
        return f"AuditLog({self.action}, patient={pid}, {self.timestamp})"

    @classmethod
    def record(cls, patient, action: str, request=None, **metadata):
        """Create an audit entry. Hashes IP if request provided."""
        ip_hash = ""
        if request:
            ip = _get_client_ip(request)
            if ip:
                ip_hash = hashlib.sha256(ip.encode()).hexdigest()
        cls.objects.create(
            patient=patient,
            action=action,
            ip_hash=ip_hash,
            metadata=metadata,
        )


def _get_client_ip(request) -> str:
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    return forwarded.split(",")[0].strip() if forwarded else request.META.get("REMOTE_ADDR", "")
