# Generated manually for FRUG-8E persistent per-user paid-AI throttle.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0014_ai_provider_failure_guard"),
    ]

    operations = [
        migrations.CreateModel(
            name="AIUserThrottleWindow",
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
                ("subject_key", models.CharField(max_length=72)),
                ("window_start", models.DateTimeField()),
                ("request_count", models.PositiveIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "core_ai_user_throttle",
            },
        ),
        migrations.AddConstraint(
            model_name="aiuserthrottlewindow",
            constraint=models.UniqueConstraint(
                fields=("subject_key", "window_start"),
                name="uniq_ai_user_throttle_window",
            ),
        ),
    ]
