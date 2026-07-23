"""Reconcile historical Django migration state with the database/model contract.

The 0017 SeparateDatabaseAndState migration enforced base_profile_id NOT NULL at
the database level but left the migration state as null=True. This migration
aligns Django's state with the already-enforced database constraint without
issuing a redundant/unsafe database ALTER.
"""

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("diabetes", "0018_p0_auth_profile_nullable_facts"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="diabetesprofile",
            options={
                "verbose_name": "Diabetes Profile",
                "verbose_name_plural": "Diabetes Profiles",
            },
        ),
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AlterField(
                    model_name="diabetesprofile",
                    name="base_profile",
                    field=models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="diabetes_profile",
                        to="core.basepatientprofile",
                    ),
                ),
            ],
            database_operations=[],
        ),
    ]
