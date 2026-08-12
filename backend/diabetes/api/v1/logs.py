"""
LogEntry CRUD under /api/v1/logs — patient-scoped reads and writes.
"""

from typing import List

from django.db import transaction
from django.shortcuts import get_object_or_404
from ninja import Router, Status
from ninja.errors import HttpError

from core.observability import EVT_LOG_CREATED, track
from diabetes.models import LogEntry
from diabetes.services.clinical.observation_erasure import (
    reconcile_personal_response_memory_after_source_erasure,
)
from diabetes.services.session_cache import invalidate as _invalidate_ctx

from .kpis import invalidate_kpi_cache as _invalidate_kpis
from .schemas import (
    BatchSyncResponse,
    Error,
    LogEntryCreateSchema,
    LogEntrySchema,
    LogEntryUpdateSchema,
    MealPortionSchema,
    PaginatedLogsResponse,
    validate_meal_portion_links,
)

router = Router(tags=["logs"])

# Only fields consumed by the canonical personal-response derivation can make a
# persisted ClinicalObservationState stale when an existing source is replaced.
_CLINICAL_TWIN_SOURCE_FIELDS = frozenset(
    {
        "blood_sugar",
        "logged_at",
        "glycemic_context",
        "meal_type",
        "stressed",
        "exercised",
        "is_sick",
        "sleep_quality",
        "fatigue_level",
        "source",
    }
)


def _changes_clinical_twin_source(log: LogEntry, values: dict) -> bool:
    return any(
        field in _CLINICAL_TWIN_SOURCE_FIELDS and getattr(log, field) != value
        for field, value in values.items()
    )


@router.get("/logs", response=PaginatedLogsResponse)
def list_logs(request, page: int = 1, page_size: int = 50):
    """
    Paginated log list.  Query params: ?page=1&page_size=50.
    page_size is clamped to [1, 200] to prevent runaway queries.
    """
    page_size = max(1, min(page_size, 200))
    page = max(1, page)
    qs = LogEntry.objects.filter(patient=request.user).order_by("-created_at")
    total = qs.count()
    offset = (page - 1) * page_size
    items = list(qs[offset : offset + page_size])
    return {"total": total, "page": page, "page_size": page_size, "items": items}


@router.post("/logs", response=LogEntrySchema)
def create_log(request, data: LogEntryCreateSchema):
    log = LogEntry.objects.create(patient=request.user, **data.dict())
    _invalidate_ctx(request.user.id)
    _invalidate_kpis(request.user.id)
    track(
        EVT_LOG_CREATED,
        patient_id=request.user.id,
        props={"log_id": log.id, "meal_type": log.meal_type or ""},
    )
    return log


# /logs/batch MUST be declared before /logs/{log_id} — Ninja matches routes
# in registration order; the literal "batch" would otherwise be swallowed by
# the {log_id} int pattern as a 405.
@router.post("/logs/batch", response=BatchSyncResponse)
def batch_create_logs(request, data: List[LogEntryCreateSchema]):
    synced_uuids = []
    errors = []
    mutated_existing_source = False

    with transaction.atomic():
        for entry_data in data:
            if not entry_data.client_uuid:
                errors.append("Missing client_uuid for one entry")
                continue

            existing = LogEntry.objects.filter(client_uuid=entry_data.client_uuid).first()

            try:
                if existing is not None:
                    # Batch sync is a full local snapshot. Replaying the same UUID is
                    # idempotent, while an edited local snapshot must update the same
                    # patient's server row rather than being silently treated as a no-op.
                    if existing.patient_id != request.user.id:
                        errors.append("client_uuid is already owned by another patient")
                        continue
                    snapshot = entry_data.dict()
                    snapshot.pop("client_uuid", None)
                    clinical_source_changed = _changes_clinical_twin_source(
                        existing,
                        snapshot,
                    )
                    for field, value in snapshot.items():
                        setattr(existing, field, value)
                    existing.save()
                    mutated_existing_source = (
                        mutated_existing_source or clinical_source_changed
                    )
                else:
                    LogEntry.objects.create(patient=request.user, **entry_data.dict())
                    track(
                        EVT_LOG_CREATED,
                        patient_id=request.user.id,
                        props={"client_uuid": str(entry_data.client_uuid)},
                    )
                synced_uuids.append(entry_data.client_uuid)
            except Exception as e:
                errors.append(f"Error syncing {entry_data.client_uuid}: {str(e)}")

        if mutated_existing_source:
            # A full-snapshot edit may remove or replace evidence that was already
            # materialized in ClinicalObservationState. Rebuild once for the batch.
            reconcile_personal_response_memory_after_source_erasure(
                patient_id=request.user.id,
            )

    if synced_uuids:
        _invalidate_ctx(request.user.id)
        _invalidate_kpis(request.user.id)
    return {"synced_ids": synced_uuids, "errors": errors}


@router.get("/logs/{log_id}", response=LogEntrySchema)
def get_log(request, log_id: int):
    return get_object_or_404(LogEntry, id=log_id, patient=request.user)


def _validate_patch_portion_links(log: LogEntry, data: LogEntryUpdateSchema) -> None:
    if data.meal_items is None and data.meal_portions is None:
        return

    effective_items = data.meal_items if data.meal_items is not None else log.meal_items
    if data.meal_portions is not None:
        effective_portions = data.meal_portions
    else:
        effective_portions = [
            MealPortionSchema.model_validate(portion) for portion in log.meal_portions
        ]

    try:
        validate_meal_portion_links(effective_items or [], effective_portions)
    except ValueError as exc:
        raise HttpError(422, str(exc)) from exc


@router.patch("/logs/{log_id}", response=LogEntrySchema)
def update_log(request, log_id: int, data: LogEntryUpdateSchema):
    """Partial update — only supplied fields are written.  404 on cross-patient access."""
    with transaction.atomic():
        log = get_object_or_404(LogEntry, id=log_id, patient=request.user)
        _validate_patch_portion_links(log, data)
        updates = data.model_dump(exclude_none=True)
        clinical_source_changed = _changes_clinical_twin_source(log, updates)
        for field, value in updates.items():
            setattr(log, field, value)
        log.save()
        if clinical_source_changed:
            # A patch may explicitly erase/replace source fields that contributed
            # to a durable observation. Rebuild from surviving authoritative rows.
            reconcile_personal_response_memory_after_source_erasure(
                patient_id=request.user.id,
            )
    _invalidate_ctx(request.user.id)
    _invalidate_kpis(request.user.id)
    return log


@router.delete("/logs/{log_id}", response={204: None, 404: Error})
def delete_log(request, log_id: int):
    log = get_object_or_404(LogEntry, id=log_id, patient=request.user)
    with transaction.atomic():
        log.delete()
        reconcile_personal_response_memory_after_source_erasure(
            patient_id=request.user.id,
        )
    _invalidate_ctx(request.user.id)
    _invalidate_kpis(request.user.id)
    return Status(204, None)
