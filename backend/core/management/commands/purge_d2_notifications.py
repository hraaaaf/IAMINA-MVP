"""Manual D2 physical retention purge. No scheduler is activated by this file."""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from core.models.d2_notification import D2Notification


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
        if not options["apply"]:
            count = D2Notification.objects.filter(expires_at__lte=now).count()
            self.stdout.write(f"D2 DRY_RUN expired={count} max_batch={limit}")
            return
        with transaction.atomic():
            # Bounded by PK; no patient health fields are stored in this table.
            ids = list(
                D2Notification.objects.filter(expires_at__lte=now)
                .order_by("pk").values_list("pk", flat=True)[:limit]
            )
            deleted, _ = D2Notification.objects.filter(
                pk__in=ids, expires_at__lte=now,
            ).delete()
        self.stdout.write(f"D2 APPLIED deleted={deleted} max_batch={limit}")
