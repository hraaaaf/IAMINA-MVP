"""CAL-12 test-only: bind each synthetic consent receipt to bearer revocation epoch."""
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0021_cal12_export_consent_fixture_ledger"),
    ]

    operations = [
        migrations.AddField(
            model_name="cal12exportconsentfixturereceipt",
            name="native_auth_version",
            field=models.PositiveIntegerField(default=0),
        ),
    ]
