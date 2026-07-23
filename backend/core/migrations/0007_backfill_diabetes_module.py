"""
Data migration: backfill PatientModule rows for existing DiabetesProfile patients.

For every BasePatientProfile that has a linked DiabetesProfile (diabetes extension),
create a PatientModule(module_name="diabetes", is_active=True) row — unless one
already exists (get_or_create guards against duplicates).

Idempotent: running twice produces the same result.
Reversible: reverse migration is a no-op (rows remain — safe for data integrity).

Implementation note: uses raw SQL to read base_profile_id from the physical
diabetes_patientprofile table since the historical ORM state at this migration
point may not expose that column cleanly on all DB configs.
"""
from django.db import migrations, connection as _conn


def backfill_diabetes_module(apps, schema_editor):
    # Check whether base_profile_id column exists in the physical table
    # (it may not if migration 0017 ran in a fresh/empty DB context).
    # Portable across SQLite and Postgres (raw PRAGMA is SQLite-only).
    connection = schema_editor.connection
    with connection.cursor() as cursor:
        cols = {
            col.name
            for col in connection.introspection.get_table_description(
                cursor, "diabetes_patientprofile"
            )
        }

    if "base_profile_id" not in cols:
        # No base_profile_id column — either fresh empty DB or column was never added.
        # Nothing to backfill; PatientModule rows will be created on first login.
        return

    BasePatientProfile = apps.get_model("core", "BasePatientProfile")
    PatientModule = apps.get_model("core", "PatientModule")

    with schema_editor.connection.cursor() as cursor:
        cursor.execute(
            "SELECT DISTINCT base_profile_id FROM diabetes_patientprofile "
            "WHERE base_profile_id IS NOT NULL"
        )
        base_ids = [row[0] for row in cursor.fetchall()]

    for base in BasePatientProfile.objects.filter(id__in=base_ids):
        PatientModule.objects.get_or_create(
            patient=base,
            module_name="diabetes",
            defaults={"is_active": True},
        )


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0006_copy_basepatientprofile_data"),
        ("diabetes", "0017_patientprofile_to_extension"),
    ]

    operations = [
        migrations.RunPython(backfill_diabetes_module, noop),
    ]
