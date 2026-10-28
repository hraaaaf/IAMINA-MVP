from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0024_w02_vault_revision_anchor"),
    ]

    operations = [
        migrations.AddField(
            model_name="basepatientprofile",
            name="first_use_completed_at",
            field=models.DateTimeField(
                blank=True,
                help_text=(
                    "Set only by an authenticated, explicit first-use completion action. "
                    "Not a clinical completeness or consent marker."
                ),
                null=True,
            ),
        ),
    ]
