"""Persistent per-user abuse throttle for paid external AI only."""

from __future__ import annotations

import hashlib
import hmac
import logging
from dataclasses import dataclass
from datetime import UTC, datetime

from django.db import transaction

from core.models import AIUserThrottleWindow

logger = logging.getLogger("iamina.cost")


class UserAbuseThrottleExceeded(RuntimeError):
    """Raised before paid egress when an opaque user window exceeds its ceiling."""


@dataclass(frozen=True, slots=True)
class UserAbuseThrottlePolicy:
    window_seconds: int
    max_requests: int

    def validate(self) -> None:
        if (
            not isinstance(self.window_seconds, int)
            or isinstance(self.window_seconds, bool)
            or self.window_seconds <= 0
        ):
            raise ValueError("window_seconds must be a positive integer")
        if (
            not isinstance(self.max_requests, int)
            or isinstance(self.max_requests, bool)
            or self.max_requests <= 0
        ):
            raise ValueError("max_requests must be a positive integer")


class PersistentUserAbuseThrottle:
    """Cross-worker fixed-window throttle with no raw patient identifier at rest."""

    def __init__(self, *, policy: UserAbuseThrottlePolicy, key_material: bytes):
        policy.validate()
        if not isinstance(key_material, bytes) or len(key_material) < 32:
            raise ValueError("user throttle HMAC key material must be at least 32 bytes")
        self.policy = policy
        self._key_material = key_material

    def subject_key(self, patient_id: int) -> str:
        if not isinstance(patient_id, int) or isinstance(patient_id, bool) or patient_id <= 0:
            raise ValueError("patient_id must be a positive integer")
        digest = hmac.new(
            self._key_material,
            f"user-throttle|patient:{patient_id}".encode(),
            hashlib.sha256,
        ).hexdigest()
        return f"hmac256:{digest}"

    def _window_start(self, now: datetime) -> datetime:
        if now.tzinfo is None or now.utcoffset() is None:
            raise ValueError("now must be timezone-aware")
        epoch = int(now.timestamp())
        start_epoch = epoch - (epoch % self.policy.window_seconds)
        return datetime.fromtimestamp(start_epoch, tz=UTC)

    def authorize(self, *, patient_id: int, now: datetime) -> int:
        """Atomically consume one paid-AI request slot and return the new count."""
        subject_key = self.subject_key(patient_id)
        window_start = self._window_start(now)
        with transaction.atomic():
            row, _ = AIUserThrottleWindow.objects.get_or_create(
                subject_key=subject_key,
                window_start=window_start,
                defaults={"request_count": 0},
            )
            row = AIUserThrottleWindow.objects.select_for_update().get(pk=row.pk)
            if row.request_count >= self.policy.max_requests:
                logger.warning(
                    "runtime_finops user_throttle_exceeded limit=%d window_seconds=%d",
                    self.policy.max_requests,
                    self.policy.window_seconds,
                )
                raise UserAbuseThrottleExceeded("paid AI user throttle exceeded")
            row.request_count += 1
            row.save(update_fields=("request_count", "updated_at"))
            return row.request_count
