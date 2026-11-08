"""Manual D2 physical retention purge. No scheduler is activated by this file."""
from datetime import timedelta

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from core.models.d2_notification import (
    D2Notification,
    D2ProactiveEmissionReceipt,
)


class Command(BaseCommand):
    help = "D2 bounded expired notices; dry-run unless --apply (no cron)."

    def add_arguments(self, parser):
        parser.add_argument("--apply", action="store_true")
        parser.add_argument("--limit", type=int, default=100)

    def handle(self, *args, **options):
        limit = options["limit"]
        if type(limit) is not int or not (1 <= limit <= 200):
            raise CommandError("D2 purge limit must be within 1..200")
        now = timezone.now()
        receipt_cutoff = now - timedelta(days=7)
        if not options["apply"]:
            count = D2Notification.objects.filter(expires_at__lte=now).count()
            receipt_count = D2ProactiveEmissionReceipt.objects.filter(
                emitted_at__lte=receipt_cutoff,
            ).count()
            self.stdout.write(
                f"D2 DRY_RUN expired={count} receipts_expired={receipt_count} "
                f"max_batch={limit}"
            )
            return
        with transaction.atomic():
            # Shared batch cap across both tables; no clinical fields stored.
            ids = list(
                D2Notification.objects.filter(expires_at__lte=now)
                .order_by("pk").values_list("pk", flat=True)[:limit]
            )
            deleted, _ = D2Notification.objects.filter(
                pk__in=ids, expires_at__lte=now,
            ).delete()
            remainder = max(0, limit - len(ids))
            receipt_ids = list(
                D2ProactiveEmissionReceipt.objects.filter(
                    emitted_at__lte=receipt_cutoff,
                ).order_by("pk").values_list("pk", flat=True)[:remainder]
            )
            receipt_deleted, _ = D2ProactiveEmissionReceipt.objects.filter(
                pk__in=receipt_ids, emitted_at__lte=receipt_cutoff,
            ).delete()
        self.stdout.write(
            f"D2 APPLIED deleted={deleted} receipts_deleted={receipt_deleted} "
            f"max_batch={limit}"
        )
