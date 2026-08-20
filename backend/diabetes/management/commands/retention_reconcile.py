"""Dry-run reconciliation for document retention without reading patient content."""

from __future__ import annotations

import json
import re

from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.management.base import BaseCommand
from django_redis import get_redis_connection

from diabetes.models import LabReport
from diabetes.retention import DOCUMENT_RETENTION_POLICIES
from media.documents.retention import PENDING_EXTRACTION_POLICY

_PENDING_RE = re.compile(r"pulper:pending:(?P<patient_id>\d+):")


def _scan_cache_orphan_count() -> int:
    redis = get_redis_connection("default")
    physical_pattern = cache.make_key("pulper:pending:*")
    patient_ids: set[int] = set()
    for raw_key in redis.scan_iter(match=physical_pattern, count=100):
        key = raw_key.decode("utf-8", errors="ignore") if isinstance(raw_key, bytes) else str(raw_key)
        match = _PENDING_RE.search(key)
        if match:
            patient_ids.add(int(match.group("patient_id")))
    if not patient_ids:
        return 0
    existing_ids = set(User.objects.filter(id__in=patient_ids).values_list("id", flat=True))
    return len(patient_ids - existing_ids)


def build_reconciliation(*, include_cache: bool = False) -> dict[str, object]:
    governed_without_approval = sum(
        1
        for policy in DOCUMENT_RETENTION_POLICIES
        if policy.human_gate_required
        and policy.destructive_ttl_seconds is not None
        and not policy.approval_reference
    )
    payload: dict[str, object] = {
        "dry_run": True,
        "persistent_raw_text_objects": LabReport.objects.exclude(raw_text="").count(),
        "db_orphan_objects": 0,
        "transient_ttl_seconds": PENDING_EXTRACTION_POLICY.destructive_ttl_seconds,
        "unapproved_destructive_policies": governed_without_approval,
        "destructive_raw_text_purge_enabled": any(
            policy.storage_key == "diabetes.LabReport.raw_text"
            and policy.destructive_ttl_seconds is not None
            and bool(policy.approval_reference)
            for policy in DOCUMENT_RETENTION_POLICIES
        ),
        "cache_scan_performed": include_cache,
        "cache_orphan_patient_scopes": _scan_cache_orphan_count() if include_cache else None,
    }
    return payload


class Command(BaseCommand):
    help = "Reconcile document retention in dry-run mode without reading patient content."

    def add_arguments(self, parser):
        parser.add_argument("--include-cache", action="store_true")
        parser.add_argument("--json", action="store_true", dest="as_json")

    def handle(self, *args, **options):
        payload = build_reconciliation(include_cache=options["include_cache"])
        if options["as_json"]:
            self.stdout.write(json.dumps(payload, sort_keys=True))
            return
        self.stdout.write("Retention reconciliation (dry-run only)")
        for key, value in payload.items():
            self.stdout.write(f"{key}={value}")
