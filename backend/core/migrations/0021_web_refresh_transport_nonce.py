"""F09-C2 additive test-only signed BFF nonce digest ledger; no hosted migration."""

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0020_web_refresh_candidate"),
    ]

    operations = [
        migrations.CreateModel(
            name="WebRefreshTransportNonce",
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
                ("nonce_digest", models.CharField(max_length=64, unique=True)),
                ("seen_at", models.DateTimeField()),
                ("expires_at", models.DateTimeField(db_index=True)),
            ],
        ),
    ]
