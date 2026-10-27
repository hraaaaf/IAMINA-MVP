"""One-use W01-G5 sandbox reconciliation by existing Django account erasure path.

Never run on live patient or production database. The command is dry-run by
default.  It intentionally hardcodes the exact two orphan synthetic identities
and the independently observed Neon DB/branch/role, and refuses all divergence.
"""
from __future__ import annotations

import re
from datetime import datetime
from datetime import timezone as dt_timezone

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import connection

from core.api.v1.account import _erase_account_data
from core.models import BasePatientProfile
from core.models.erasure_attempt import ErasureAttempt
from core.models.erasure_record import ErasureRecord

_EXPECTED_IDENTITY = (
    "iamina925_empty",
    "iamina_preview_app",
    "noisy-truth-00115950",
    "br-sweet-frog-b9ok6ptp",
)
_EXPECTED_IDS = (5, 6)
_EXPECTED_NAMES = {5: "W01-A", 6: "W01-B"}
_CREATION_START = datetime(2026, 10, 27, 17, 4, tzinfo=dt_timezone.utc)
_CREATION_END = datetime(2026, 10, 27, 17, 5, tzinfo=dt_timezone.utc)
_EMAIL_RE = re.compile(r"\Aw01g5-bff-[0-9a-f]{20}@example\.invalid\Z")
_CONFIRMATION = "IAMINA_W01G5_CLEANUP_IDS_5_6_ONLY"
_IDENTITY_QUERY = (
    "SELECT current_database(), current_user, "
    "current_setting('neon.project_id', true), "
    "current_setting('neon.branch_id', true)"
)


def _verify_identity():
    with connection.cursor() as cursor:
        cursor.execute(_IDENTITY_QUERY)
        observed = tuple(cursor.fetchone() or ())
    if observed != _EXPECTED_IDENTITY:
        raise CommandError("W01_G5_STOP_WRONG_NEON_IDENTITY")


def _verify_targets():
    User = get_user_model()
    users = list(User.objects.order_by("pk"))
    if len(users) != 2 or tuple(user.pk for user in users) != _EXPECTED_IDS:
        raise CommandError("W01_G5_STOP_ACCOUNT_SET_NOT_EXACTLY_IDS_5_6")
    for user in users:
        if (
            not _EMAIL_RE.fullmatch(user.email)
            or user.username != user.email
            or user.first_name != "Synthetic"
            or user.last_name != _EXPECTED_NAMES[user.pk]
            or user.is_staff or user.is_superuser or not user.is_active
            or not _CREATION_START <= user.date_joined < _CREATION_END
        ):
            raise CommandError("W01_G5_STOP_TARGET_PROFILE_MISMATCH")
        try:
            profile = BasePatientProfile.objects.get(patient=user)
        except BasePatientProfile.DoesNotExist as exc:
            raise CommandError("W01_G5_STOP_PATIENT_PROFILE_MISSING") from exc
        if profile.firebase_uid:
            raise CommandError("W01_G5_STOP_EXTERNAL_FIREBASE_IDENTITY")
    if (
        BasePatientProfile.objects.count() != 2
        or ErasureAttempt.objects.filter(patient_id_snapshot__in=_EXPECTED_IDS).exists()
        or ErasureRecord.objects.filter(patient_id_snapshot__in=_EXPECTED_IDS).exists()
    ):
        raise CommandError("W01_G5_STOP_ALREADY_CLAIMED_OR_EXTRA_PROFILE")
    return users


class Command(BaseCommand):
    help = "Deny by default; reconcile only sandbox W01-G5 synthetic IDs 5 and 6."

    def add_arguments(self, parser):
        parser.add_argument("--apply", action="store_true")
        parser.add_argument("--confirm", default="")

    def handle(self, *args, **options):
        if options["apply"] and options["confirm"] != _CONFIRMATION:
            raise CommandError("W01_G5_STOP_EXPLICIT_CONFIRMATION_REQUIRED")
        _verify_identity()
        targets = _verify_targets()
        if not options["apply"]:
            self.stdout.write("DRY_RUN identity=verified targets=2 ids=5,6 mutation=none")
            return

        # The underlying service owns its own durable erasure claim, hook
        # execution, mandatory audit and DB transactions. Do not wrap in an
        # outer transaction or bypass any of those safeguards.
        for index, user in enumerate(targets, start=1):
            try:
                _erase_account_data(user, request=None)
            except Exception as exc:
                raise CommandError(
                    f"W01_G5_STOP_APP_ERASURE_FAILED stage={index}; "
                    "do not retry or bypass with SQL"
                ) from exc
            self.stdout.write(f"APP_ERASURE_VERIFIED stage={index}")

        User = get_user_model()
        if (
            User.objects.count() != 0
            or BasePatientProfile.objects.count() != 0
            or ErasureAttempt.objects.filter(
                patient_id_snapshot__in=_EXPECTED_IDS,
                state=ErasureAttempt.State.COMPLETED,
            ).count() != 2
            or ErasureRecord.objects.filter(
                patient_id_snapshot__in=_EXPECTED_IDS,
            ).count() != 2
        ):
            raise CommandError("W01_G5_POSTCONDITION_FAILED_EXTERNAL_REVIEW")
        self.stdout.write("APPLIED app_erased=2 auth_user=0 profiles=0")
