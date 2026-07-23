"""
emit_inactive_events — daily cron command for 90-day retention tracking.

Detects patients with no acquisition event in the last 7 days and emits one
INACTIVE_7D ObservabilityEvent per eligible patient per module per day.

Module-agnostic: iterates ModuleRegistry.all() and uses each module's
manifest.acquisition_event as the activity anchor — no LogEntry dependency.

Idempotence: a patient who already has an INACTIVE_7D event for today
is silently skipped — safe to run multiple times per day.

Usage:
    python manage.py emit_inactive_events
"""

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone


class Command(BaseCommand):
    help = "Emit INACTIVE_7D observability events for patients with no acquisition event in 7 days."

    def handle(self, *args, **options):
        from core.models import BasePatientProfile
        from core.observability import EVT_INACTIVE_7D, track
        from core.observability.events import ObservabilityEvent
        from core.registry import ModuleRegistry

        today = timezone.localdate()  # uses settings.TIME_ZONE, consistent with __date lookup
        cutoff = timezone.now() - timedelta(days=7)

        modules = list(ModuleRegistry.all())
        if not modules:
            self.stdout.write(self.style.WARNING("ModuleRegistry is empty — no modules registered yet."))
            return

        total_count = 0

        for module in modules:
            acq_event = module.manifest.acquisition_event

            # Patient IDs active in the last 7 days (have at least one acquisition event)
            active_patient_ids = (
                ObservabilityEvent.objects.filter(
                    event_type=acq_event,
                    timestamp__gte=cutoff,
                )
                .values_list("patient_id", flat=True)
                .distinct()
            )

            # Patients who have NOT had an acquisition event in the last 7 days
            inactive_patients = BasePatientProfile.objects.exclude(patient_id__in=active_patient_ids)

            # IDs that already received an INACTIVE_7D event today (idempotence)
            already_emitted = set(
                ObservabilityEvent.objects.filter(
                    event_type=EVT_INACTIVE_7D,
                    timestamp__date=today,
                ).values_list("patient_id", flat=True)
            )

            count = 0
            for base in inactive_patients:
                if base.patient_id not in already_emitted:
                    track(
                        EVT_INACTIVE_7D,
                        patient_id=base.patient_id,
                        props={"days_inactive": 7, "module": module.manifest.condition},
                    )
                    count += 1

            total_count += count
            self.stdout.write(
                self.style.SUCCESS(
                    f"[{module.manifest.condition}] Emitted INACTIVE_7D for {count} patients."
                )
            )

        self.stdout.write(self.style.SUCCESS(f"Total: {total_count} INACTIVE_7D events emitted."))
