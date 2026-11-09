"""Bounded D2 retention purge and restore guard; never schedules itself.

DRY_RUN by default. --drain --apply is an operator-controlled batch drain,
NOT a cron job. Use --require-empty as a read-only post-restore gate.
No patient identifiers or notice content are printed.
"""
from datetime import timedelta

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from core.models.d2_notification import (
    D2Notification,
    D2ProactiveEmissionReceipt,
)


def _expired_counts(cutoff, receipt_cutoff):
    notices = D2Notification.objects.filter(expires_at__lte=cutoff).count()
    receipts = D2ProactiveEmissionReceipt.objects.filter(
        emitted_at__lte=receipt_cutoff,
    ).count()
    return notices, receipts


def _delete_one_batch(limit, cutoff, receipt_cutoff):
    with transaction.atomic():
        # Hard shared cap across both tables in each small transaction.
        ids = list(
            D2Notification.objects.filter(expires_at__lte=cutoff)
            .order_by("pk").values_list("pk", flat=True)[:limit]
        )
        deleted, _ = D2Notification.objects.filter(
            pk__in=ids, expires_at__lte=cutoff,
        ).delete()
        available = max(0, limit - len(ids))
        receipt_ids = list(
            D2ProactiveEmissionReceipt.objects.filter(
                emitted_at__lte=receipt_cutoff,
            ).order_by("pk").values_list("pk", flat=True)[:available]
        )
        receipt_deleted, _ = D2ProactiveEmissionReceipt.objects.filter(
            pk__in=receipt_ids, emitted_at__lte=receipt_cutoff,
        ).delete()
    return deleted, receipt_deleted


class Command(BaseCommand):
    help = (
        "Dry-run by default; --apply deletes one bounded batch, "
        "--apply --drain drains with a hard cap; --require-empty checks restore."
    )

    def add_arguments(self, parser):
        parser.add_argument("--apply", action="store_true")
        parser.add_argument("--limit", type=int, default=100)
        parser.add_argument(
            "--drain", action="store_true",
            help="Apply multiple bounded batches; only with --apply.",
        )
        parser.add_argument(
            "--max-batches", type=int, default=50,
            help="Safety cap for --drain, 1..100 (default 50).",
        )
        parser.add_argument(
            "--require-empty", action="store_true",
            help="Read-only restore guard; fail if any expired D2 row persists.",
        )

    def handle(self, *args, **options):
        limit = options["limit"]
        max_batches = options["max_batches"]
        apply = options["apply"]
        drain = options["drain"]
        require_empty = options["require_empty"]

        if type(limit) is not int or not 1 <= limit <= 200:
            raise CommandError("D2 purge limit must be within 1..200")
        if type(max_batches) is not int or not 1 <= max_batches <= 100:
            raise CommandError("D2 max-batches must be within 1..100")
        if drain and not apply:
            raise CommandError("D2 --drain requires explicit --apply")
        if require_empty and (apply or drain):
            raise CommandError("D2 --require-empty cannot delete records")

        # One fixed cutoff per invocation prevents moving retention boundaries.
        now = timezone.now()
        receipt_cutoff = now - timedelta(days=7)
        before_notices, before_receipts = _expired_counts(now, receipt_cutoff)

        if require_empty:
            if before_notices or before_receipts:
                raise CommandError(
                    "D2 RETENTION_CHECK FAIL "
                    f"expired={before_notices} receipts_expired={before_receipts}"
                )
            self.stdout.write("D2 RETENTION_CHECK PASS expired=0 receipts_expired=0")
            return

        if not apply:
            self.stdout.write(
                f"D2 DRY_RUN expired={before_notices} "
                f"receipts_expired={before_receipts} max_batch={limit}"
            )
            return

        if not drain:
            deleted, receipt_deleted = _delete_one_batch(
                limit, now, receipt_cutoff,
            )
            self.stdout.write(
                f"D2 APPLIED deleted={deleted} receipts_deleted={receipt_deleted} "
                f"max_batch={limit}"
            )
            return

        notices_deleted = receipts_deleted = batches = 0
        for _ in range(max_batches):
            notices_remaining, receipts_remaining = _expired_counts(
                now, receipt_cutoff,
            )
            if not (notices_remaining or receipts_remaining):
                break
            deleted, receipt_deleted = _delete_one_batch(
                limit, now, receipt_cutoff,
            )
            batches += 1
            notices_deleted += deleted
            receipts_deleted += receipt_deleted
            if deleted + receipt_deleted == 0:
                raise CommandError("D2 retention drain stalled; check concurrency")

        notices_remaining, receipts_remaining = _expired_counts(
            now, receipt_cutoff,
        )
        summary = (
            f"D2 DRAIN batches={batches} deleted={notices_deleted} "
            f"receipts_deleted={receipts_deleted} "
            f"expired_remaining={notices_remaining} "
            f"receipts_remaining={receipts_remaining} "
            f"max_batch={limit} max_batches={max_batches}"
        )
        if notices_remaining or receipts_remaining:
            raise CommandError(summary + " INCOMPLETE")
        self.stdout.write(summary + " COMPLETE")
