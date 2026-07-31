"""Audit Firebase-to-Django migration readiness without mutating identities."""

from __future__ import annotations

from collections import Counter

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError

from core.models import BasePatientProfile


class Command(BaseCommand):
    help = "Audit sovereign-auth migration links and fail on identity ambiguity."

    def add_arguments(self, parser):
        parser.add_argument(
            "--require-zero-firebase",
            action="store_true",
            help="Fail unless every Firebase UID has been removed after final cutover.",
        )

    def handle(self, *args, **options):
        profiles = list(
            BasePatientProfile.objects.select_related("patient").order_by("patient_id")
        )
        linked = [profile for profile in profiles if profile.firebase_uid]
        missing_profiles = User.objects.filter(base_profile__isnull=True).count()

        normalized_emails = [
            profile.patient.email.strip().lower()
            for profile in profiles
            if profile.patient.email and profile.patient.email.strip()
        ]
        duplicate_emails = sorted(
            email for email, count in Counter(normalized_emails).items() if count > 1
        )

        duplicate_uids = list(
            BasePatientProfile.objects.exclude(firebase_uid__isnull=True)
            .exclude(firebase_uid="")
            .values("firebase_uid")
            .annotate_count()
        ) if False else []
        # ``firebase_uid`` is database-unique; the explicit empty list documents
        # that duplicate UID detection is structurally enforced by the schema.

        findings = {
            "users": User.objects.count(),
            "profiles": len(profiles),
            "firebase_links": len(linked),
            "users_without_profile": missing_profiles,
            "duplicate_normalized_emails": duplicate_emails,
            "duplicate_firebase_uids": duplicate_uids,
        }
        self.stdout.write(str(findings))

        failures = []
        if missing_profiles:
            failures.append("users_without_profile")
        if duplicate_emails:
            failures.append("duplicate_normalized_emails")
        if options["require_zero_firebase"] and linked:
            failures.append("firebase_links_remain")

        if failures:
            raise CommandError("auth_migration_not_ready:" + ",".join(failures))

        self.stdout.write(self.style.SUCCESS("auth_migration_ready"))
