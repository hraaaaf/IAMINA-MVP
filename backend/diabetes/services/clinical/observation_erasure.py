"""Reconcile durable clinical-twin state after explicit source erasure.

ClinicalObservationState is a recomputable materialized derivation. When a source
LogEntry is explicitly erased, previously persisted aggregates may still encode
values from that deleted source. Erasure therefore rebuilds the derived state
from the surviving authoritative rows instead of preserving historical aggregates.

CompanionReviewAnchor snapshots are also derived from ClinicalObservationState.
They must be invalidated on source erasure/replacement rather than preserving a
historical comparison checkpoint that may encode data the patient removed.
"""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.db import transaction

from diabetes.models.clinical_observation import ClinicalObservationState
from diabetes.models.companion_review import CompanionReviewAnchor
from diabetes.services.clinical.observation_memory import refresh_personal_response_memory
from diabetes.services.clinical.personal_response import PersonalResponseResult


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
    recreated. Companion comparison anchors are discarded because their immutable
    snapshots may also encode the erased source evidence.
    """
    # Use the same patient-level lock as every canonical Clinical Twin refresh.
    # If a refresh started before erasure, it must finish first; this transaction
    # then purges/rebuilds. Refreshes starting afterward wait for this transaction
    # and therefore can only observe the surviving authoritative source rows.
    get_user_model().objects.select_for_update().only("pk").get(pk=patient_id)
    CompanionReviewAnchor.objects.filter(patient_id=patient_id).delete()
    ClinicalObservationState.objects.filter(patient_id=patient_id).delete()
    return refresh_personal_response_memory(patient_id=patient_id)
