"""Dry-run first, explicit-approval *local synthetic only* erasure recovery.

Never executes on Vercel/Production. No Firebase UID or patient data in CLI output.
The hosted reconciler is a separate, independently reviewed W01 G3 gate.
"""
import json
import os

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError

from core.api.v1.account import _erase_account_data
from core.models.erasure_attempt import ErasureAttempt


class Command(BaseCommand):
    help = "Inspect or explicitly replay a synthetic erasure intent (local only)."

    def add_arguments(self, parser):
        parser.add_argument("--patient-id", type=int, required=True)
        parser.add_argument("--execute", action="store_true")
        parser.add_argument("--confirm", default="")

    def handle(self, *args, **options):
        patient_id = options["patient_id"]
        # Check the environment before *any* database lookup in execute mode.
        # Explicit opt-in is insufficient if a local CLI points at a cloud PG DB.
        if options["execute"] and (
            not settings.DEBUG
            or settings.DATABASES["default"]["ENGINE"] != "django.db.backends.sqlite3"
            or os.environ.get("VERCEL")
            or os.environ.get("VERCEL_ENV")
            or os.environ.get("IAMINA_G3_LOCAL_SYNTHETIC_RECOVERY") != "1"
        ):
            raise CommandError("Synthetic erasure recovery is disabled here")
        intent = ErasureAttempt.objects.filter(patient_id_snapshot=patient_id).first()
        if intent is None:
            raise CommandError("No erasure intent exists for this account")
        if not options["execute"]:
            self.stdout.write(json.dumps({
                "patient_id": patient_id,
                "state": intent.state,
                "action": "DRY_RUN",
            }))
            return

        if options["confirm"] != f"ERASE-SYNTHETIC-{patient_id}":
            raise CommandError("Explicit synthetic recovery confirmation required")
        if intent.state != ErasureAttempt.State.PENDING:
            raise CommandError("Erasure intent is not pending")
        user = User.objects.filter(pk=patient_id).first()
        if user is None:
            raise CommandError("Missing SQL user; do not mutate without forensic review")
        try:
            _erase_account_data(user)
        except Exception as exc:
            raise CommandError("Synthetic erasure recovery failed; intent retained") from exc
        self.stdout.write(json.dumps({
            "patient_id": patient_id,
            "state": "completed",
            "action": "EXECUTE",
        }))
