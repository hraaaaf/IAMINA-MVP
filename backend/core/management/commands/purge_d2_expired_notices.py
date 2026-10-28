"""Purge expired D2 saved previews; no notification producer or dispatch.

Run manually in dry-run mode first. An approved external scheduler must
invoke --apply for physical retention to be operationally enforced.
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from core.models import D2InAppNotice


class Command(BaseCommand):
    help = "Dry-run by default; physically delete expired D2 saved previews with --apply."

    def add_arguments(self, parser):
        parser.add_argument(
            "--apply", action="store_true",
            help="Actually delete expired notices (default only counts them).",
        )
        parser.add_argument(
            "--batch-size", type=int, default=500,
            help="Maximum expired notices per delete transaction (1 to 1000).",
        )

    def handle(self, *args, **options):
        batch_size = options["batch_size"]
        if not 1 <= batch_size <= 1000:
            raise CommandError("--batch-size must be between 1 and 1000")

        cutoff = timezone.now()
        expired = D2InAppNotice.objects.filter(expires_at__lte=cutoff)
        if not options["apply"]:
            self.stdout.write(
                f"DRY_RUN expired={expired.count()} cutoff={cutoff.isoformat()}"
            )
            return

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
        if remaining:
            raise CommandError(
                f"D2 retention purge incomplete: expired_remaining={remaining}"
            )
        self.stdout.write(
            f"APPLIED deleted={total_deleted} expired_remaining=0 "
            f"cutoff={cutoff.isoformat()}"
        )
