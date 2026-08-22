from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("diabetes", "0028_cgmconnection_cgmreadingrecord"),
    ]

    operations = [
        migrations.AddField(
            model_name="labreport",
            name="extraction_provenance",
            field=models.JSONField(
                blank=True,
                default=dict,
                help_text=(
                    "Structured field-level extraction evidence; excludes the full source text."
                ),
            ),
        ),
    ]
