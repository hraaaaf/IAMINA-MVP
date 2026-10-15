"""D18: patient-owned, append-only weight declarations.

A measurement is a fact declared by its owner, never a clinical judgment.
Old profile.weight is a legacy snapshot, NOT a reliable dated observation.
Do not auto-backfill it with an invented timestamp or provenance.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from uuid import UUID, uuid4

from django.conf import settings
from django.db import IntegrityError, models, transaction
from django.utils import timezone


class PatientWeightIdempotencyConflict(ValueError):
    """The same UUID cannot replace an earlier patient measurement."""


class PatientWeightObservation(models.Model):
    """Immutable-by-service, owner-scoped patient-declared weight record."""

    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="weight_observations",
        on_delete=models.CASCADE,
    )
    client_uuid = models.UUIDField(default=uuid4, editable=False)
    value = models.DecimalField(max_digits=7, decimal_places=2)
    unit = models.CharField(
        max_length=2, choices=(("kg", "Kilograms"), ("lb", "Pounds"))
    )
    weight_kg = models.DecimalField(max_digits=7, decimal_places=2)
    measured_at = models.DateTimeField()
    provenance = models.CharField(
        max_length=32, choices=(("patient_declared", "Patient declared"),)
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "core"
        ordering = ("-measured_at", "-pk")
        indexes = [
            models.Index(
                fields=["patient", "-measured_at"],
                name="core_d18_weight_owner_time",
            ),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=("patient", "client_uuid"),
                name="core_d18_weight_owner_uuid",
            ),
        ]


def validated_birth_year(year: int | None, *, current_year: int | None = None) -> int | None:
    """Optional year-level granularity, never invent an exact birth date."""
    if year is None:
        return None
    if isinstance(year, bool) or not isinstance(year, int):
        raise ValueError("Birth year must be an integer or null")
    now_year = current_year if current_year is not None else timezone.now().year
    if year < 1900 or year > now_year:
        raise ValueError("Birth year is outside the supported calendar range")
    return year


def normalized_weight(
    value: Decimal | str, *, unit: str
) -> tuple[Decimal, Decimal]:
    """Deterministic unit conversion; no diagnostic or treatment inference."""
    if unit not in ("kg", "lb"):
        raise ValueError("Unsupported weight unit")
    try:
        original = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError("Invalid weight value") from exc
    if not original.is_finite() or original <= 0 or original > Decimal("9999.99"):
        raise ValueError("Weight must be finite, positive, and representable")
    # Do not silently round a patient's actual input.
    if original != original.quantize(Decimal("0.01")):
        raise ValueError("Weight has more than two decimal places")
    metric = (
        original if unit == "kg" else original * Decimal("0.45359237")
    ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    if metric <= 0:
        raise ValueError("Weight too small for stored precision")
    return original, metric


@transaction.atomic
def append_patient_weight(
    *,
    patient,
    value: Decimal | str,
    unit: str,
    measured_at: datetime,
    client_uuid: UUID,
    provenance: str = "patient_declared",
) -> tuple[PatientWeightObservation, bool]:
    """Append only; retrying a UUID cannot replace an earlier record.

    The caller MUST pass the authenticated patient. Ownership never comes
    from user-supplied JSON, a cached local profile, or a different bearer.
    """
    if patient is None or patient.pk is None:
        raise ValueError("A persisted authenticated patient is required")
    if not isinstance(client_uuid, UUID):
        raise ValueError("A valid client UUID is required")
    if provenance != "patient_declared":
        raise ValueError("Unsupported weight provenance")
    if not isinstance(measured_at, datetime) or timezone.is_naive(measured_at):
        raise ValueError("An aware measurement timestamp is required")
    if measured_at > timezone.now() + timedelta(minutes=5):
        raise ValueError("Measurement timestamp cannot be in the future")
    original, metric = normalized_weight(value, unit=unit)
    try:
        observation, created = PatientWeightObservation.objects.get_or_create(
            patient=patient,
            client_uuid=client_uuid,
            defaults={
                "value": original,
                "unit": unit,
                "weight_kg": metric,
                "measured_at": measured_at,
                "provenance": provenance,
            },
        )
    except IntegrityError:
        # The unique constraint provides the final protection if concurrent
        # retries occur; surface a write failure rather than overwrite.
        raise
    if not created and (
        observation.value != original
        or observation.unit != unit
        or observation.weight_kg != metric
        or observation.measured_at != measured_at
        or observation.provenance != provenance
    ):
        raise PatientWeightIdempotencyConflict("Client UUID already belongs to another declaration")
    return observation, created
