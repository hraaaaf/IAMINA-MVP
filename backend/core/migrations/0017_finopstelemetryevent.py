from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0016_alter_patientlocalepreference_dialect"),
    ]

    operations = [
        migrations.CreateModel(
            name="FinOpsTelemetryEvent",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("event_type", models.CharField(db_index=True, max_length=32)),
                ("payload", models.JSONField(default=dict)),
                ("timestamp", models.DateTimeField(auto_now_add=True, db_index=True)),
            ],
            options={
                "ordering": ["timestamp", "id"],
            },
        ),
        migrations.AddIndex(
            model_name="finopstelemetryevent",
            index=models.Index(
                fields=["event_type", "timestamp"],
                name="finops_type_ts_idx",
            ),
        ),
    ]
