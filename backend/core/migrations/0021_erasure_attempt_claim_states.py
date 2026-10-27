from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("core", "0020_erasure_attempt")]

    operations = [
        migrations.AlterField(
            model_name="erasureattempt",
            name="state",
            field=models.CharField(
                choices=[
                    ("pending", "Pending"),
                    ("in_progress", "In progress"),
                    ("review_required", "Review required"),
                    ("completed", "Completed"),
                ],
                db_index=True,
                default="pending",
                max_length=16,
            ),
        ),
    ]
