"""Deterministic, patient-scoped data portability export.

The export walks only reverse ownership relations from the authenticated Django
user through IAmina-owned apps. It never follows forward relations into shared
catalogues or other users' records.
"""

from __future__ import annotations

import base64
import hashlib
import json
from collections import defaultdict, deque
from datetime import date, datetime, time
from decimal import Decimal
from pathlib import Path
from typing import Any
from uuid import UUID

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Model
from django.db.models.fields.files import FieldFile
from django.utils import timezone

EXPORT_SCHEMA_VERSION = "1.0"
_ALLOWED_APP_LABELS = frozenset({"ai", "core", "diabetes"})
_EXCLUDED_FIELD_NAMES = frozenset(
    {
        "password",
        "raw_password",
        "secret",
        "api_key",
        "access_token",
        "refresh_token",
        "auth_token",
        "token",
        "token_hash",
        "token_version",
        "credential",
        "credentials",
    }
)
_ACCOUNT_FIELDS = (
    "id",
    "username",
    "email",
    "first_name",
    "last_name",
    "date_joined",
    "last_login",
    "is_active",
)


def _json_value(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    if isinstance(value, (Decimal, UUID, Path)):
        return str(value)
    if isinstance(value, bytes):
        return {"encoding": "base64", "value": base64.b64encode(value).decode("ascii")}
    if isinstance(value, FieldFile):
        return value.name or None
    if isinstance(value, dict):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_value(item) for item in value]
    return str(value)


def _serialize_account(user) -> dict[str, Any]:
    return {field: _json_value(getattr(user, field)) for field in _ACCOUNT_FIELDS}


def _serialize_model(instance: Model) -> dict[str, Any]:
    record: dict[str, Any] = {}
    for field in instance._meta.concrete_fields:
        if field.name.lower() in _EXCLUDED_FIELD_NAMES:
            continue
        value = field.value_from_object(instance)
        if field.is_relation:
            record[field.name] = {
                "model": field.related_model._meta.label_lower,
                "id": _json_value(value),
            }
        else:
            record[field.name] = _json_value(value)
    return record


def _owned_related(instance: Model):
    """Yield objects owned through reverse one-to-one or one-to-many relations."""
    for relation in instance._meta.related_objects:
        related_model = relation.related_model
        if related_model._meta.app_label not in _ALLOWED_APP_LABELS:
            continue
        if relation.many_to_many:
            continue
        accessor = relation.get_accessor_name()
        if not accessor:
            continue
        try:
            related = getattr(instance, accessor)
        except ObjectDoesNotExist:
            continue
        if relation.one_to_one:
            yield related
            continue
        order_field = related_model._meta.pk.name
        yield from related.all().order_by(order_field).iterator()


def _collect_owned_records(user) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    queue = deque([user])
    seen: set[tuple[str, str]] = {(user._meta.label_lower, str(user.pk))}

    while queue:
        current = queue.popleft()
        for related in _owned_related(current):
            identity = (related._meta.label_lower, str(related.pk))
            if identity in seen:
                continue
            seen.add(identity)
            grouped[related._meta.label_lower].append(_serialize_model(related))
            queue.append(related)

    return {
        model: sorted(records, key=lambda record: str(record.get("id", "")))
        for model, records in sorted(grouped.items())
    }


def build_patient_export(user, *, generated_at: datetime | None = None) -> dict[str, Any]:
    """Build a JSON-serializable export for one Django user."""
    timestamp = generated_at or timezone.now()
    if timezone.is_naive(timestamp):
        raise ValueError("generated_at must be timezone-aware")

    records = _collect_owned_records(user)
    counts = {model: len(items) for model, items in records.items()}
    subject = {"user_id": user.pk}
    data = {
        "account": _serialize_account(user),
        "records": records,
    }
    manifest = {
        "models": counts,
        "record_count": sum(counts.values()),
    }
    fingerprint_input = {
        "schema_version": EXPORT_SCHEMA_VERSION,
        "subject": subject,
        "manifest": manifest,
        "data": data,
    }
    canonical = json.dumps(
        fingerprint_input,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")

    return {
        "schema_version": EXPORT_SCHEMA_VERSION,
        "generated_at": timestamp.isoformat(),
        "subject": subject,
        "manifest": manifest,
        "data": data,
        "sha256": hashlib.sha256(canonical).hexdigest(),
    }
