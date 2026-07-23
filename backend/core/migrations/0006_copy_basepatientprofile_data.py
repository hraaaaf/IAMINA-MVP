"""
Data migration: copy identity fields from diabetes.PatientProfile → core.BasePatientProfile.

This runs AFTER core_basepatientprofile table is created (0005) and AFTER the last
diabetes migration (0016_add_deep_memory) so both tables exist at migration time.

The copy is idempotent via get_or_create — safe to run multiple times.
"""
from django.db import migrations


def _identity_columns_present(schema_editor):
    """
    Return True if diabetes_patientprofile still has the identity columns
    that this migration copies from.  After diabetes.0017 (SeparateDatabaseAndState)
    runs and then is rolled back with noop reverse_sql, those columns are gone.
    In that state there is nothing left to copy — BasePatientProfile already has
    the data (or the DB is empty) so we skip the loop safely.
    """
    # Portable across SQLite and Postgres (raw PRAGMA is SQLite-only).
    connection = schema_editor.connection
    with connection.cursor() as cursor:
        cols = {
            col.name
            for col in connection.introspection.get_table_description(
                cursor, "diabetes_patientprofile"
            )
        }
    return "date_of_birth" in cols


def copy_identity_data(apps, schema_editor):
    # Guard: if the identity columns were already dropped (e.g. re-running after
    # a partial rollback where reverse_sql was noop), skip — nothing to copy.
    if not _identity_columns_present(schema_editor):
        return

    PatientProfile = apps.get_model("diabetes", "PatientProfile")
    BasePatientProfile = apps.get_model("core", "BasePatientProfile")
    for pp in PatientProfile.objects.select_related("patient").all():
        BasePatientProfile.objects.get_or_create(
            patient=pp.patient,
            defaults={
                "firebase_uid": pp.firebase_uid,
                "preferred_language": pp.preferred_language,
                "ai_consent_given_at": pp.ai_consent_given_at,
                "premium_valid_until": pp.premium_valid_until,
                "gender": pp.gender,
                "date_of_birth": pp.date_of_birth,
                "weight": pp.weight,
                "height": pp.height,
            },
        )


def reverse_copy(apps, schema_editor):
    """
    Reverse: copy identity fields back from BasePatientProfile → PatientProfile.
    Safe because PatientProfile still has all columns at reverse time
    (the SeparateDatabaseAndState migration in diabetes.0017 runs AFTER this one).
    """
    BasePatientProfile = apps.get_model("core", "BasePatientProfile")
    PatientProfile = apps.get_model("diabetes", "PatientProfile")
    for bp in BasePatientProfile.objects.select_related("patient").all():
        try:
            pp = PatientProfile.objects.get(patient=bp.patient)
            pp.firebase_uid = bp.firebase_uid
            pp.preferred_language = bp.preferred_language
            pp.ai_consent_given_at = bp.ai_consent_given_at
            pp.premium_valid_until = bp.premium_valid_until
            pp.gender = bp.gender
            pp.date_of_birth = bp.date_of_birth
            pp.weight = bp.weight
            pp.height = bp.height
            pp.save(update_fields=[
                "firebase_uid", "preferred_language", "ai_consent_given_at",
                "premium_valid_until", "gender", "date_of_birth", "weight", "height",
            ])
        except PatientProfile.DoesNotExist:
            pass


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0005_patientmodule"),
        ("diabetes", "0016_add_deep_memory"),
    ]

    operations = [
        migrations.RunPython(copy_identity_data, reverse_copy),
    ]
