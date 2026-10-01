"""Synthetic demo patient provisioning for the public IAMINA demo.

The demo uses the same patient runtime as the authenticated application.
Only the data source differs: this service provisions deterministic synthetic
logs under an anonymous, non-login Django user derived from a hashed demo subject.
"""

from __future__ import annotations

import random
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.db import transaction
from django.utils import timezone

from core.companion.clinical import invalidate
from core.models import BasePatientProfile
from diabetes.models import DiabetesProfile, LogEntry

_DEMO_USERNAME_PREFIX = "demo_runtime_"
_DEMO_FRESHNESS_MAX_AGE = timedelta(days=7)

_MEALS = {
    "fasting": ((6, 8), (85, 155)),
    "breakfast": ((8, 10), (120, 180)),
    "lunch": ((12, 14), (130, 195)),
    "snack": ((15, 17), (100, 145)),
    "dinner": ((19, 21), (110, 185)),
}


def _username(subject_key: str) -> str:
    safe = "".join(ch for ch in subject_key.lower() if ch.isalnum())
    return f"{_DEMO_USERNAME_PREFIX}{safe[:32]}"


def _seed_logs(patient: User) -> None:
    rng = random.Random(42)
    now = timezone.now()
    entries: list[LogEntry] = []

    for days_ago in range(20, -1, -1):
        day = now - timedelta(days=days_ago)
        if rng.random() < 0.1:
            continue

        meal_types = ["fasting", "lunch"]
        if rng.random() < 0.7:
            meal_types.append("breakfast")
        if rng.random() < 0.35:
            meal_types.append("snack")
        if rng.random() < 0.75:
            meal_types.append("dinner")

        week = days_ago // 7
        trend_offset = {2: 15, 1: 5, 0: -10}.get(week, 0)

        for meal_type in meal_types:
            hour_range, glucose_range = _MEALS[meal_type]
            hour = rng.randint(*hour_range)
            minute = rng.randint(0, 59)
            glucose = rng.randint(
                glucose_range[0] + trend_offset,
                glucose_range[1] + trend_offset,
            )
            glucose = max(55, min(350, glucose))
            entries.append(
                LogEntry(
                    patient=patient,
                    blood_sugar=Decimal(str(glucose)),
                    meal_type=meal_type,
                    logged_at=day.replace(
                        hour=hour,
                        minute=minute,
                        second=0,
                        microsecond=0,
                    ),
                )
            )

    LogEntry.objects.bulk_create(entries)
    invalidate(patient.id)


@transaction.atomic
def get_or_create_synthetic_demo_patient(subject_key: str) -> User:
    """Return an anonymous synthetic patient with fresh deterministic logs."""

    patient, created = User.objects.get_or_create(
        username=_username(subject_key),
        defaults={
            "first_name": "Demo",
            "last_name": "Patient",
            "is_active": True,
        },
    )
    if created:
        patient.set_unusable_password()
        patient.save(update_fields=["password"])

    base, _ = BasePatientProfile.objects.get_or_create(
        patient=patient,
        defaults={
            "date_of_birth": "1985-03-15",
            "gender": "female",
            "weight": Decimal("68.0"),
            "height": 165,
        },
    )
    DiabetesProfile.objects.get_or_create(
        base_profile=base,
        defaults={
            "diabetes_type": "type2",
            "treatment_type": "oral_meds",
            "target_range_low": 70,
            "target_range_high": 180,
            "unit_preference": "mg_dl",
        },
    )

    entries = LogEntry.objects.filter(patient=patient)
    latest = entries.order_by("-logged_at").first()
    if latest is None or latest.logged_at < timezone.now() - _DEMO_FRESHNESS_MAX_AGE:
        entries.delete()
        _seed_logs(patient)

    return patient
