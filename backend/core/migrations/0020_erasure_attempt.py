from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("core", "0019_auth_abuse_bucket")]

    operations = [
        migrations.CreateModel(
            name="ErasureAttempt",
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
                ("patient_id_snapshot", models.IntegerField(unique=True)),
                (
                    "firebase_uid_snapshot",
                    models.CharField(blank=True, default="", max_length=128),
                ),
                (
                    "state",
                    models.CharField(
                        choices=[("pending", "Pending"), ("completed", "Completed")],
                        db_index=True,
                        default="pending",
                        max_length=16,
                    ),
                ),
                ("requested_at", models.DateTimeField(auto_now_add=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
            ],
            options={"ordering": ["-requested_at"]},
        ),
    ]
