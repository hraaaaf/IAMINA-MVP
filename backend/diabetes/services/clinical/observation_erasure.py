"""Reconcile durable clinical-twin state after explicit source erasure.

ClinicalObservationState is a recomputable materialized derivation. When a source
LogEntry is explicitly erased, previously persisted aggregates may still encode
values from that deleted source. Erasure therefore rebuilds the derived state
from the surviving authoritative rows instead of preserving historical aggregates.
"""

from __future__ import annotations

from django.db import transaction

from diabetes.models.clinical_observation import ClinicalObservationState
from diabetes.services.clinical.observation_memory import (
    PersonalResponseResult,
    refresh_personal_response_memory,
)


@transaction.atomic
def reconcile_personal_response_memory_after_source_erasure(
    *,
    patient_id: int,
) -> PersonalResponseResult:
    """Remove stale derivations and rebuild only from surviving source rows.

    This intentionally differs from a normal sparse canonical refresh. A normal
    refresh preserves lifecycle state when evidence becomes temporarily sparse;
    explicit erasure must not preserve aggregates that may encode deleted data.
    If the remaining source dataset is insufficient, no observation state is
    recreated.
    """
    ClinicalObservationState.objects.filter(patient_id=patient_id).delete()
    return refresh_personal_response_memory(patient_id=patient_id)
