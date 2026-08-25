"""Persistent, patient-unlinked FinOps telemetry records."""

from django.db import models


class FinOpsTelemetryEvent(models.Model):
    """Append-only aggregate telemetry with no patient/user linkage or payload content."""

    event_type = models.CharField(max_length=32, db_index=True)
    payload = models.JSONField(default=dict)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        app_label = "core"
        ordering = ["timestamp", "id"]
        indexes = [
            models.Index(
                fields=["event_type", "timestamp"],
                name="finops_type_ts_idx",
            )
        ]

    def __str__(self) -> str:
        return f"{self.timestamp:%Y-%m-%d %H:%M} {self.event_type}"
