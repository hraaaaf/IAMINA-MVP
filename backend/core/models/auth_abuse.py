"""Persistent authentication abuse-rate buckets.

The limiter intentionally lives in PostgreSQL rather than Redis/cache so the
control remains effective when optional cache infrastructure is unavailable.
Only keyed hashes are stored; raw IP addresses and account identifiers never
enter this table.
"""

from django.db import models


class AuthAbuseBucket(models.Model):
    scope = models.CharField(max_length=32)
    key_hash = models.CharField(max_length=64)
    window_started_at = models.DateTimeField()
    count = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "core"
        constraints = [
            models.UniqueConstraint(
                fields=("scope", "key_hash"),
                name="core_auth_abuse_scope_key_uniq",
            )
        ]
        indexes = [
            models.Index(fields=("updated_at",), name="core_auth_abuse_updated_idx")
        ]

    def __str__(self) -> str:
        return f"{self.scope}:{self.key_hash[:12]}:{self.count}"
