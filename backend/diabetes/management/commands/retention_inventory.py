"""Dry-run inventory of retained diabetes document text and declared policies."""

from __future__ import annotations

import json

from django.core.management.base import BaseCommand
from django.db.models import Sum
from django.db.models.functions import Length

from diabetes.models import LabReport
from diabetes.retention import DOCUMENT_RETENTION_POLICIES
from media.documents.retention import PENDING_EXTRACTION_POLICY


class Command(BaseCommand):
    help = "Inventory document retention without reading or deleting patient content."

    def add_arguments(self, parser):
        parser.add_argument("--json", action="store_true", dest="as_json")

    def handle(self, *args, **options):
        raw_text_reports = LabReport.objects.exclude(raw_text="")
        retained_chars = (
            raw_text_reports.annotate(raw_text_length=Length("raw_text"))
            .aggregate(total=Sum("raw_text_length"))["total"]
            or 0
        )

        policies = (PENDING_EXTRACTION_POLICY, *DOCUMENT_RETENTION_POLICIES)
        payload = {
            "dry_run": True,
            "persistent_raw_text": {
                "storage_key": "diabetes.LabReport.raw_text",
                "object_count": raw_text_reports.count(),
                "character_count": int(retained_chars),
            },
            "policies": [
                {
                    "storage_key": policy.storage_key,
                    "retention_class": policy.retention_class.value,
                    "policy_basis": policy.policy_basis,
                    "destructive_ttl_seconds": policy.destructive_ttl_seconds,
                    "human_gate_required": policy.human_gate_required,
                    "approval_reference": policy.approval_reference,
                }
                for policy in policies
            ],
        }

        if options["as_json"]:
            self.stdout.write(json.dumps(payload, sort_keys=True))
            return

        self.stdout.write("Retention inventory (dry-run only)")
        self.stdout.write(
            "LabReport.raw_text: "
            f"{payload['persistent_raw_text']['object_count']} objects / "
            f"{payload['persistent_raw_text']['character_count']} characters"
        )
        for policy in payload["policies"]:
            self.stdout.write(
                f"- {policy['storage_key']}: {policy['retention_class']} "
                f"ttl={policy['destructive_ttl_seconds']} "
                f"human_gate={policy['human_gate_required']}"
            )
