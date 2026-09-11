"""Audit a live, authorized non-patient CGM bridge path."""

from __future__ import annotations

import json

from django.core.management.base import BaseCommand, CommandError

from diabetes.services.cgm_live_qualification import (
    LiveCGMQualificationError,
    qualify_live_cgm,
)


class Command(BaseCommand):
    help = (
        "Exercise a configured live CGM bridge and emit non-clinical qualification metadata. "
        "This is engineering evidence only, not real-patient release authorization."
    )

    def add_arguments(self, parser):
        parser.add_argument("--patient-id", type=int, required=True)
        parser.add_argument(
            "--source",
            choices=("dexcom", "libre", "linx"),
            default="linx",
        )
        parser.add_argument("--max-age-minutes", type=int, default=15)
        parser.add_argument("--minimum-readings", type=int, default=2)
        parser.add_argument(
            "--confirm-authorized-non-patient-test-subject",
            action="store_true",
            help="Confirm this run is limited to an authorized non-patient test subject.",
        )
        parser.add_argument(
            "--confirm-physical-sensor",
            action="store_true",
            help="Confirm the upstream bridge is currently fed by a physical CGM sensor.",
        )

    def handle(self, *args, **options):
        try:
            result = qualify_live_cgm(
                patient_id=options["patient_id"],
                expected_source=options["source"],
                max_age_minutes=options["max_age_minutes"],
                minimum_readings=options["minimum_readings"],
                authorized_non_patient_test_subject=bool(
                    options["confirm_authorized_non_patient_test_subject"]
                ),
                physical_sensor_attested=bool(options["confirm_physical_sensor"]),
            )
        except LiveCGMQualificationError as exc:
            raise CommandError(str(exc)) from exc

        self.stdout.write(json.dumps(result.as_payload(), ensure_ascii=False, indent=2))
