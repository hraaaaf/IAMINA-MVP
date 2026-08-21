"""Persistent non-PHI per-user abuse throttle state for paid AI egress."""

from django.db import models


class AIUserThrottleWindow(models.Model):
    """Fixed-window request counter keyed only by opaque HMAC subject identity."""

    subject_key = models.CharField(max_length=72)
    window_start = models.DateTimeField()
    request_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "core"
        db_table = "core_ai_user_throttle"
        constraints = [
            models.UniqueConstraint(
                fields=("subject_key", "window_start"),
                name="uniq_ai_user_throttle_window",
            ),
        ]
