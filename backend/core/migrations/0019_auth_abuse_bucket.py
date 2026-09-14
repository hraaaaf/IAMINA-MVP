from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0018_versioned_ai_consent_evidence"),
    ]

    operations = [
        migrations.CreateModel(
            name="AuthAbuseBucket",
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
                ("scope", models.CharField(max_length=32)),
                ("key_hash", models.CharField(max_length=64)),
                ("window_started_at", models.DateTimeField()),
                ("count", models.PositiveIntegerField(default=0)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "indexes": [
                    models.Index(
                        fields=["updated_at"],
                        name="core_auth_abuse_updated_idx",
                    )
                ],
                "constraints": [
                    models.UniqueConstraint(
                        fields=("scope", "key_hash"),
                        name="core_auth_abuse_scope_key_uniq",
                    )
                ],
            },
        ),
    ]
