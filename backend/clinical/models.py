"""
Platform abstract models — clinical layer.

These define the shared interface for any health domain capsule.
Concrete implementations live in the capsule app (diabetes/).
Abstract = no DB table created here.
"""
from django.db import models


class HealthEntry(models.Model):
    """Abstract base for a single health observation."""
    class Meta:
        abstract = True


class HealthPatient(models.Model):
    """Abstract base for a patient's extended health profile."""
    class Meta:
        abstract = True
