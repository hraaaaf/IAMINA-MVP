"""D2 physical expiry purge: bounded, observable, and dry-run by default.

No scheduler, notification delivery, clinical write or user-account erasure is
performed by this command. Scheduling is a separate audited release gate.
"""
from __future__ import annotations

import json
from datetime import timedelta

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from core.models import D2InAppNotice


class Command(BaseCommand):
    help = "Physically purge expired D2 saved previews (dry-run by default)."

    def add_arguments(self, parser):
        parser.add_argument("--apply", action="store_true")
        parser.add_argument("--batch-size", type=int, default=500)
        parser.add_argument(
            "--max-deletes", type=int, default=10000,
            help="Hard ceiling of records allowed per invocation (1-100000).",
        )
        parser.add_argument(
            "--max-overdue-minutes", type=int, default=None,
            help="In dry-run only, fail if any expired item is older than this grace.",
        )

    def handle(self, *args, **options):
        batch_size = options["batch_size"]
        max_deletes = options["max_deletes"]
        max_overdue_minutes = options["max_overdue_minutes"]
        apply = options["apply"]
        if not 1 <= batch_size <= 1000:
            raise CommandError("--batch-size must be between 1 and 1000")
        if not 1 <= max_deletes <= 100000:
            raise CommandError("--max-deletes must be between 1 and 100000")
        if max_overdue_minutes is not None and not 1 <= max_overdue_minutes <= 10080:
            raise CommandError("--max-overdue-minutes must be between 1 and 10080")
        if apply and max_overdue_minutes is not None:
            raise CommandError("overdue assertion is read-only; omit --apply")

        cutoff = timezone.now()
        expired = D2InAppNotice.objects.filter(expires_at__lte=cutoff)
        before = expired.count()
        overdue = (
            expired.filter(
                expires_at__lte=cutoff-timedelta(minutes=max_overdue_minutes)
            ).count()
            if max_overdue_minutes is not None else None
        )

        def emit(mode, deleted, remaining):
            self.stdout.write(json.dumps({
                "schema_version": "1.0",
                "job": "d2_expired_saved_preview_purge",
                "mode": mode,
                "cutoff_utc": cutoff.isoformat(),
                "expired_before": before,
                "deleted": deleted,
                "expired_remaining": remaining,
                "overdue_count": overdue,
                "grace_minutes": max_overdue_minutes,
                "max_deletes": max_deletes,
            }, sort_keys=True))

        if not apply:
            self.stdout.write(f"DRY_RUN expired={before} cutoff={cutoff.isoformat()}")
            emit("DRY_RUN", 0, before)
            if overdue:
                raise CommandError(
                    f"D2_RETENTION_OVERDUE overdue_count={overdue}; investigate scheduler"
                )
            return

        # Fail before any write if the backlog exceeds the permitted scope.
        if before > max_deletes:
            raise CommandError(
                f"D2_RETENTION_LIMIT exceeded_count={before} max_deletes={max_deletes}"
            )

        total_deleted = 0
        while True:
            ids = list(
                expired.order_by("pk").values_list("pk", flat=True)[:batch_size]
            )
            if not ids:
                break
            with transaction.atomic():
                deleted, _ = D2InAppNotice.objects.filter(
                    pk__in=ids, expires_at__lte=cutoff,
                ).delete()
            total_deleted += deleted

        remaining = expired.count()
        self.stdout.write(
            f"APPLIED deleted={total_deleted} expired_remaining={remaining} "
            f"cutoff={cutoff.isoformat()}"
        )
        emit("APPLIED", total_deleted, remaining)
        if remaining:
            raise CommandError(
                f"D2 retention purge incomplete: expired_remaining={remaining}"
            )
