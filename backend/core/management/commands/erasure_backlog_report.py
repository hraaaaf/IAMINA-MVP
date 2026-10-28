"""Privacy-safe, read-only backlog counters for account-erasure intents.

No patient ID, username, Firebase UID, raw exception, or audit metadata.
Designed for a management shell with legitimate database access.
"""
import json

from django.core.management.base import BaseCommand

from core.models.erasure_attempt import ErasureAttempt


class Command(BaseCommand):
    help = "Count account-erasure intent states without inspecting identities."

    def handle(self, *args, **options):
        counts = {
            state: ErasureAttempt.objects.filter(state=state).count()
            for state in (
                ErasureAttempt.State.PENDING,
                ErasureAttempt.State.IN_PROGRESS,
                ErasureAttempt.State.REVIEW_REQUIRED,
                ErasureAttempt.State.COMPLETED,
            )
        }
        self.stdout.write(json.dumps({
            "action": "READ_ONLY_ERASURE_BACKLOG",
            "pending": counts[ErasureAttempt.State.PENDING],
            "in_progress": counts[ErasureAttempt.State.IN_PROGRESS],
            "review_required": counts[ErasureAttempt.State.REVIEW_REQUIRED],
            "completed": counts[ErasureAttempt.State.COMPLETED],
            "unresolved_total": (
                counts[ErasureAttempt.State.PENDING]
                + counts[ErasureAttempt.State.IN_PROGRESS]
                + counts[ErasureAttempt.State.REVIEW_REQUIRED]
            ),
        }, sort_keys=True))
