from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):

    dependencies = [
        ("diabetes", "0032_diabetesprofile_target_authority"),
    ]

    operations = [
        migrations.AddField(
            model_name="logentry",
            name="meal_episode_id",
            field=models.UUIDField(
                blank=True,
                db_index=True,
                help_text=(
                    "Identifiant explicite d'un meme episode repas pour relier une mesure "
                    "pre_meal et post_meal sans appariement temporel infere."
                ),
                null=True,
            ),
        ),
        migrations.AddConstraint(
            model_name="logentry",
            constraint=models.UniqueConstraint(
                fields=("patient", "meal_episode_id", "glycemic_context"),
                condition=(
                    Q(meal_episode_id__isnull=False)
                    & Q(glycemic_context__in=("pre_meal", "post_meal"))
                ),
                name="uniq_patient_meal_episode_role",
            ),
        ),
    ]
