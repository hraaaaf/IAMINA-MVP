from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone
from decimal import ROUND_HALF_UP, Decimal

from django.utils import timezone as django_timezone

from diabetes.models import LogEntry

_GLUCOSE_QUANTUM = Decimal("0.01")


def normalize_import_timestamp(timestamp: datetime) -> datetime:
    """Return one canonical UTC instant for imported clinical readings."""
    if timestamp.tzinfo is None:
        timestamp = django_timezone.make_aware(
            timestamp,
            django_timezone.get_current_timezone(),
        )
    return timestamp.astimezone(timezone.utc)


def normalize_import_glucose(glucose: float | Decimal) -> Decimal:
    """Match LogEntry's 2-decimal storage precision without float drift."""
    return Decimal(str(glucose)).quantize(_GLUCOSE_QUANTUM, rounding=ROUND_HALF_UP)


def make_import_client_uuid(
    patient_id: int,
    timestamp: datetime,
    glucose: float | Decimal,
) -> str:
    """Stable identity shared by every diabetes import path."""
    instant = normalize_import_timestamp(timestamp)
    normalized_glucose = normalize_import_glucose(glucose)
    seed = (
        f"import:v2:{patient_id}:"
        f"{instant.isoformat(timespec='microseconds')}:"
        f"{normalized_glucose:.2f}"
    )
    digest = hashlib.sha256(seed.encode()).digest()
    return str(uuid.UUID(bytes=digest[:16]))


def imported_reading_exists(
    patient,
    timestamp: datetime,
    glucose: float | Decimal,
) -> bool:
    """Catch legacy import UUID schemes by clinical identity before creating v2."""
    instant = normalize_import_timestamp(timestamp)
    normalized_glucose = normalize_import_glucose(glucose)
    return LogEntry.objects.filter(
        patient=patient,
        source="import",
        logged_at=instant,
        blood_sugar=normalized_glucose,
    ).exists()
