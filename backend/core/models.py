"""
AuditLog — append-only trail of sensitive actions.

Lives in the `core` app (rather than `tracking`) because it's cross-cutting:
the middleware that will populate it (Phase 5) watches auth, API, and admin
events — none of which are "tracking" concerns. Fields and retention follow
AMINA_MVP_PLAN.md §3 and TEAM.md (Security + Compliance).

Retention : 6 years (RGPD health data).
"""

from django.contrib.auth.models import User
from django.db import models

# Re-export so Django's migration framework discovers cross-cutting core models.
from core.finops_events import FinOpsTelemetryEvent  # noqa: F401
from core.observability.events import ObservabilityEvent  # noqa: F401


class AuditLog(models.Model):
    """Immutable record of one sensitive action performed against the system."""

    ACTION_CHOICES = [
        ('login', 'Connexion'),
        ('logout', 'Déconnexion'),
        ('view', 'Consultation'),
        ('create', 'Création'),
        ('update', 'Modification'),
        ('delete', 'Suppression'),
        ('export', 'Export'),
    ]

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    actor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='audit_entries',
        help_text="Utilisateur à l'origine de l'action (null si supprimé a posteriori).",
    )
    action = models.CharField(
        max_length=64,
        choices=ACTION_CHOICES,
        db_index=True,
        help_text="Type d'action journalisée.",
    )
    resource_type = models.CharField(
        max_length=64,
        help_text="Modèle Django concerné (ex. LogEntry, PatientProfile).",
    )
    resource_id = models.CharField(
        max_length=64, null=True, blank=True,
        help_text="Identifiant de la ressource visée (primary key ou UUID).",
    )
    metadata = models.JSONField(
        default=dict, blank=True,
        help_text="Contexte complémentaire ; jamais de PHI en clair.",
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=512, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
        app_label = 'core'

    def __str__(self):
        who = self.actor.username if self.actor_id else 'anonymous'
        return f"{self.created_at:%Y-%m-%d %H:%M} {who} {self.action} {self.resource_type}"
