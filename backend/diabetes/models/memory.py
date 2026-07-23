from django.contrib.auth.models import User
from django.db import models


class IAminaMemorySnapshot(models.Model):
    """
    Persistent fallback for IAminaMemory.
    Written on every memory.save(); read when the cache is cold (server restart,
    Redis eviction, new device).  Avoids returning a blank memory to a returning
    patient.
    """
    patient = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="iamina_memory",
    )
    data_json = models.JSONField(default=dict)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "diabetes"
        verbose_name = "IAmina Memory Snapshot"

    def __str__(self):
        return f"IAminaMemorySnapshot(patient={self.patient_id})"


class IAminaDeepMemorySnapshot(models.Model):
    patient = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="iamina_deep_memory",
    )
    data_json = models.JSONField(default=dict)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "diabetes"
