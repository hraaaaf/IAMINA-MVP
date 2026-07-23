"""
Migration 0014
==============
1. Remove the unused `daily_wellness` JSONField from LogEntry.
   - Field was introduced in 0007_amina_fields but never populated.
   - Scalar columns (fatigue_level, is_sick, stressed, sleep_quality) remain
     the single source of truth.

2. Add a DB-level CheckConstraint on blood_sugar (30 ≤ value ≤ 600 mg/dL).
   - Mirrors the Pydantic _BloodSugar API constraint.
   - On SQLite: enforced via table-recreation; on PostgreSQL: native CHECK.
"""
from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):

    dependencies = [
        ("diabetes", "0013_default_language_ar_ma"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="logentry",
            name="daily_wellness",
        ),
        migrations.AddConstraint(
            model_name="logentry",
            constraint=models.CheckConstraint(
                condition=Q(blood_sugar__gte=30) & Q(blood_sugar__lte=600),
                name="logentry_blood_sugar_range",
                violation_error_message="Blood sugar must be between 30 and 600 mg/dL.",
            ),
        ),
    ]
