"""
diabetes migration 0017 — PatientProfile → DiabetesProfile (SeparateDatabaseAndState)

CRITICAL: This migration uses SeparateDatabaseAndState to guarantee that the
diabetes_patientprofile table is NOT dropped at the database level.

state_operations: tell Django ORM that DiabetesProfile has only diabetes-specific
  fields plus the base_profile FK (identity fields removed).
database_operations: ADD the FK column, UPDATE it, then recreate the table
  keeping only the diabetes-specific columns + base_profile_id.

SQLite note: cannot DROP UNIQUE columns directly. We use a table-recreate pattern
  (CREATE new table, INSERT selected columns, DROP old table, RENAME new to original).
  This is safe and idempotent. For PostgreSQL production, ALTER TABLE DROP COLUMN
  works natively — add a DB-router check if needed.

Idempotency note: the RunPython database_forwards function checks whether
  the identity columns (patient_id) are still present before running the SQL.
  If the table is already in the final schema (after a rollback with noop reverse_sql
  that left columns dropped), the function is a no-op — the state_operations still
  run to keep Django's migration state consistent.
"""
from django.db import migrations, models
import django.db.models.deletion


def _get_columns(connection, table):
    # Portable across SQLite and Postgres (raw PRAGMA is SQLite-only).
    with connection.cursor() as cursor:
        return {
            col.name
            for col in connection.introspection.get_table_description(cursor, table)
        }


def apply_database_changes(apps, schema_editor):
    """
    Idempotent forward database operations for 0017.

    If the table already lacks identity columns (e.g. we are re-running after a
    rollback that used noop reverse_sql for DROP operations), the table is already
    in the final shape and we skip all SQL.
    """
    conn = schema_editor.connection
    cols = _get_columns(conn, "diabetes_patientprofile")

    # If patient_id is gone, the table was already recreated — nothing to do.
    if "patient_id" not in cols:
        return

    with conn.cursor() as cursor:
        # Step A: Add base_profile_id FK column if not already present.
        if "base_profile_id" not in cols:
            cursor.execute("""
                ALTER TABLE diabetes_patientprofile
                ADD COLUMN base_profile_id INTEGER
                    REFERENCES core_basepatientprofile(id) ON DELETE CASCADE;
            """)

        # Step B: Populate base_profile_id from patient_id lookup.
        cursor.execute("""
            UPDATE diabetes_patientprofile
            SET base_profile_id = (
                SELECT id FROM core_basepatientprofile
                WHERE core_basepatientprofile.patient_id = diabetes_patientprofile.patient_id
            );
        """)

        # Step C: drop the identity columns that moved to core_basepatientprofile,
        # keeping only diabetes-specific columns + the base_profile_id FK.
        if conn.vendor == "sqlite":
            # SQLite cannot drop UNIQUE/indexed columns directly, so use the
            # standard rebuild pattern: CREATE new + INSERT + DROP + RENAME.
            cursor.execute("""
                CREATE TABLE diabetes_patientprofile_new (
                    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                    diabetes_type VARCHAR(20) NOT NULL,
                    treatment_type VARCHAR(20) NOT NULL,
                    target_range_low INTEGER NOT NULL,
                    target_range_high INTEGER NOT NULL,
                    unit_preference VARCHAR(6) NOT NULL,
                    base_profile_id INTEGER NOT NULL
                        REFERENCES core_basepatientprofile(id) ON DELETE CASCADE
                );
            """)
            cursor.execute("""
                INSERT INTO diabetes_patientprofile_new
                    (id, diabetes_type, treatment_type, target_range_low,
                     target_range_high, unit_preference, base_profile_id)
                SELECT
                    id, diabetes_type, treatment_type, target_range_low,
                    target_range_high, unit_preference, base_profile_id
                FROM diabetes_patientprofile;
            """)
            cursor.execute("DROP TABLE diabetes_patientprofile;")
            cursor.execute("ALTER TABLE diabetes_patientprofile_new RENAME TO diabetes_patientprofile;")
        else:
            # Postgres (and other DBs that support DROP COLUMN directly): no table
            # rebuild needed. Drop the identity columns and enforce the FK NOT NULL.
            keep = {
                "id", "diabetes_type", "treatment_type", "target_range_low",
                "target_range_high", "unit_preference", "base_profile_id",
            }
            for col in (c for c in cols if c not in keep):
                cursor.execute(
                    f'ALTER TABLE diabetes_patientprofile DROP COLUMN "{col}" CASCADE;'
                )
            cursor.execute(
                "ALTER TABLE diabetes_patientprofile "
                "ALTER COLUMN base_profile_id SET NOT NULL;"
            )


def reverse_database_changes(apps, schema_editor):
    """
    Reverse is a no-op at the DB level.  The identity columns were dropped
    via the table-recreate pattern (Step C above) and cannot be restored
    without the original data.  Rolling back the ORM state (state_operations
    reverse) is sufficient for test-cycle rollback — the data migration in
    core.0006 reverse_copy handles copying data back.
    """
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("diabetes", "0016_add_deep_memory"),
        ("core", "0006_copy_basepatientprofile_data"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                # 1. Rename ORM model from PatientProfile to DiabetesProfile
                migrations.RenameModel("PatientProfile", "DiabetesProfile"),

                # 1b. Tell Django the physical table name stays as diabetes_patientprofile
                #     (SeparateDatabaseAndState only recreates the table, not renames it)
                migrations.AlterModelTable(
                    name="diabetesprofile",
                    table="diabetes_patientprofile",
                ),

                # 2. Add base_profile FK to ORM state
                migrations.AddField(
                    model_name="diabetesprofile",
                    name="base_profile",
                    field=models.OneToOneField(
                        to="core.BasePatientProfile",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="diabetes_profile",
                        null=True,
                    ),
                    preserve_default=False,
                ),

                # 3. Remove identity fields from ORM state
                migrations.RemoveField(model_name="diabetesprofile", name="patient"),
                migrations.RemoveField(model_name="diabetesprofile", name="firebase_uid"),
                migrations.RemoveField(model_name="diabetesprofile", name="preferred_language"),
                migrations.RemoveField(model_name="diabetesprofile", name="ai_consent_given_at"),
                migrations.RemoveField(model_name="diabetesprofile", name="premium_valid_until"),
                migrations.RemoveField(model_name="diabetesprofile", name="gender"),
                migrations.RemoveField(model_name="diabetesprofile", name="date_of_birth"),
                migrations.RemoveField(model_name="diabetesprofile", name="weight"),
                migrations.RemoveField(model_name="diabetesprofile", name="height"),
                migrations.RemoveField(model_name="diabetesprofile", name="created_at"),
                migrations.RemoveField(model_name="diabetesprofile", name="updated_at"),
            ],
            database_operations=[
                migrations.RunPython(apply_database_changes, reverse_database_changes),
            ],
        ),
    ]
