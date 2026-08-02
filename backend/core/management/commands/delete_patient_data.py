"""Plan or execute a verified patient deletion after the pilot grace period."""

from __future__ import annotations

import json
import re
from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from core.data_portability import build_patient_export
from core.models import AuditLog

_GRACE_DAYS = 30
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


class Command(BaseCommand):
    help = "Plan or execute deletion of one patient account after verified approval."

    def add_arguments(self, parser) -> None:
        parser.add_argument("--user-id", type=int, required=True)
        parser.add_argument("--requested-at", type=date.fromisoformat, required=True)
        parser.add_argument("--approval-reference", required=True)
        parser.add_argument("--export-sha256", required=True)
        parser.add_argument(
            "--legal-hold-status",
            choices=("CLEARED", "ACTIVE", "UNKNOWN"),
            required=True,
        )
        parser.add_argument("--execute", action="store_true")
        parser.add_argument("--confirm", default="")

    def handle(self, *args, **options):
        user_id: int = options["user_id"]
        requested_at: date = options["requested_at"]
        approval_reference = options["approval_reference"].strip()
        export_sha256 = options["export_sha256"].strip().lower()
        legal_hold_status = options["legal_hold_status"]
        execute = options["execute"]

        if not approval_reference:
            raise CommandError("Approval reference is required")
        if not _SHA256.fullmatch(export_sha256):
            raise CommandError("export-sha256 must be a lowercase SHA-256 digest")
        if legal_hold_status != "CLEARED":
            raise CommandError("Deletion is blocked until legal-hold status is CLEARED")

        today = timezone.localdate()
        eligible_on = requested_at + timedelta(days=_GRACE_DAYS)
        if requested_at > today:
            raise CommandError("Deletion request date cannot be in the future")
        if today < eligible_on:
            raise CommandError(f"Deletion grace period is active until {eligible_on.isoformat()}")

        user_model = get_user_model()
        try:
            user = user_model.objects.get(pk=user_id)
        except user_model.DoesNotExist as exc:
            raise CommandError("Patient account not found") from exc

        export = build_patient_export(user)
        plan = {
            "schema_version": "1.0",
            "user_id": user_id,
            "requested_at": requested_at.isoformat(),
            "eligible_on": eligible_on.isoformat(),
            "approval_reference": approval_reference,
            "legal_hold_status": legal_hold_status,
            "verified_export_sha256": export_sha256,
            "current_record_manifest": export["manifest"],
            "action": "EXECUTE" if execute else "DRY_RUN",
        }

        if not execute:
            self.stdout.write(json.dumps(plan, ensure_ascii=False, indent=2))
            return

        expected_confirmation = f"DELETE-PATIENT-{user_id}"
        if options["confirm"] != expected_confirmation:
            raise CommandError(
                f"Execution requires --confirm {expected_confirmation}"
            )

        with transaction.atomic():
            AuditLog.objects.filter(actor=user).update(actor=None)
            AuditLog.objects.create(
                actor=None,
                action="delete",
                resource_type="PatientAccount",
                resource_id=str(user_id),
                metadata={
                    "approval_reference": approval_reference,
                    "requested_at": requested_at.isoformat(),
                    "eligible_on": eligible_on.isoformat(),
                    "export_sha256": export_sha256,
                    "record_manifest": export["manifest"],
                },
            )
            deleted_count, deleted_by_model = user.delete()

        result = {
            **plan,
            "deleted_count": deleted_count,
            "deleted_by_model": deleted_by_model,
        }
        self.stdout.write(json.dumps(result, ensure_ascii=False, indent=2))
