"""
ObservabilityEvent model + track() — product telemetry layer.

track() is fire-and-forget: callsites are one-liners, never wrapped in try/except.
All exception handling is internal — identical resilience pattern to IAminaDeepMemory.save().

No PHI allowed in props. Use only anonymous counters, IDs, and non-identifying metadata.
"""

import logging

from django.db import models

# ── Event type constants ───────────────────────────────────────────────────────

EVT_LOG_CREATED      = "log_created"
EVT_SESSION_START    = "session_start"
EVT_CHAT_MESSAGE     = "chat_message"
EVT_STREAK_CONTINUED = "streak_continued"
EVT_STREAK_BROKEN    = "streak_broken"
EVT_SUMMARY_VIEWED   = "summary_viewed"
EVT_INACTIVE_7D      = "inactive_7d"

# ── Module logger ──────────────────────────────────────────────────────────────

_logger = logging.getLogger(__name__)


# ── Model ─────────────────────────────────────────────────────────────────────

class ObservabilityEvent(models.Model):
    """
    Immutable product telemetry record.

    No FK to Patient/User — keeps telemetry independent of auth model.
    No PHI in props — only anonymous counts, IDs, and non-identifying metadata.
    """

    event_type = models.CharField(max_length=64, db_index=True)
    patient_id = models.IntegerField(db_index=True)
    props      = models.JSONField(default=dict)
    timestamp  = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "core"
        ordering  = ["-timestamp"]
        indexes   = [
            models.Index(
                fields=["patient_id", "event_type", "timestamp"],
                name="obs_patient_type_ts_idx",
            )
        ]

    def __str__(self):
        return f"{self.event_type} patient={self.patient_id}"


# ── Public API ─────────────────────────────────────────────────────────────────

def track(event_type: str, patient_id: int, props: dict | None = None) -> None:
    """
    Fire-and-forget product telemetry write.

    Never raises. Failures are logged as WARNING and swallowed so that no
    callsite is ever interrupted by a telemetry error.

    Args:
        event_type: One of the EVT_* constants.
        patient_id: Django User PK (int). Never a Firebase UID or email.
        props:      Non-PHI metadata dict. Defaults to {}.
    """
    props = props or {}
    try:
        ObservabilityEvent.objects.create(
            event_type=event_type,
            patient_id=patient_id,
            props=props,
        )
    except Exception as exc:
        _logger.warning(
            "track() failed: event=%s patient=%s err=%r",
            event_type,
            patient_id,
            exc,
        )
