"""
core.models.patient_module — PatientModule junction table

Tracks which modules a patient has activated.
Created in P2 of the IAmina Platform Transformation Plan.
"""
from django.db import models

from core.models.patient import BasePatientProfile


class PatientModule(models.Model):
    """
    Junction table: one row per (patient, module_name) activation.

    module_name examples: "diabetes", "hypertension", "mental_health"
    """

    patient = models.ForeignKey(
        BasePatientProfile,
        on_delete=models.CASCADE,
        related_name='modules',
    )

    module_name = models.CharField(
        max_length=64,
        help_text="Slug identifier for the module (e.g. 'diabetes').",
    )

    activated_at = models.DateTimeField(auto_now_add=True)

    is_active = models.BooleanField(default=True)

    class Meta:
        app_label = 'core'
        unique_together = [("patient", "module_name")]
        verbose_name = 'Patient Module'
        verbose_name_plural = 'Patient Modules'

    def __str__(self):
        return f"{self.patient.patient.username} — {self.module_name}"
