from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("diabetes", "0029_labreport_extraction_provenance"),
    ]

    operations = [
        migrations.AddField(
            model_name="labreport",
            name="source_sha256",
            field=models.CharField(
                blank=True,
                help_text="SHA-256 of source bytes for patient-scoped document idempotency.",
                max_length=64,
                null=True,
            ),
        ),
        migrations.AddConstraint(
            model_name="labreport",
            constraint=models.UniqueConstraint(
                condition=models.Q(source_sha256__isnull=False)
                & ~models.Q(source_sha256=""),
                fields=("patient", "source_sha256"),
                name="uniq_labreport_patient_sha256",
            ),
        ),
    ]
