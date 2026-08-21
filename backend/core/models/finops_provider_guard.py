"""Persistent non-PHI provider failure/retry guard state for FRUG-8."""

from django.db import models


class AIProviderCircuitState(models.Model):
    """Cross-worker circuit-breaker state for one governed provider key."""

    provider = models.CharField(max_length=64, unique=True)
    consecutive_failures = models.PositiveIntegerField(default=0)
    opened_until = models.DateTimeField(null=True, blank=True)
    probe_in_flight_until = models.DateTimeField(null=True, blank=True)
    last_error_code = models.CharField(max_length=64, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "core"
        db_table = "core_ai_provider_circuit"


class AIProviderOperationAttempt(models.Model):
    """Durable retry/lease state keyed only by opaque HMAC operation identity."""

    provider = models.CharField(max_length=64)
    operation_key = models.CharField(max_length=72)
    attempt_count = models.PositiveIntegerField(default=0)
    active_attempt_number = models.PositiveIntegerField(null=True, blank=True)
    in_flight_until = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    last_error_code = models.CharField(max_length=64, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "core"
        db_table = "core_ai_provider_operation"
        constraints = [
            models.UniqueConstraint(
                fields=("provider", "operation_key"),
                name="uniq_ai_provider_operation_key",
            ),
        ]
