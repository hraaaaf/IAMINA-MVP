from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("diabetes", "0030_labreport_source_sha256"),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="logentry",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    glycemic_context__in=("", "fasting", "pre_meal", "post_meal", "other")
                ),
                name="logentry_glycemic_context_canonical",
            ),
        ),
        migrations.AddConstraint(
            model_name="logentry",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    meal_type__in=(
                        "",
                        "fasting",
                        "breakfast",
                        "lunch",
                        "snack",
                        "dinner",
                        "iftar",
                        "suhoor",
                        "other",
                    )
                ),
                name="logentry_meal_type_canonical",
            ),
        ),
        migrations.AddConstraint(
            model_name="logentry",
            constraint=models.CheckConstraint(
                condition=models.Q(exercised__in=("", "yes", "no")),
                name="logentry_exercised_canonical",
            ),
        ),
        migrations.AddConstraint(
            model_name="logentry",
            constraint=models.CheckConstraint(
                condition=models.Q(sleep_quality__in=("", "good", "bad")),
                name="logentry_sleep_quality_canonical",
            ),
        ),
        migrations.AddConstraint(
            model_name="logentry",
            constraint=models.CheckConstraint(
                condition=models.Q(stressed__in=("", "yes", "no")),
                name="logentry_stressed_canonical",
            ),
        ),
        migrations.AddConstraint(
            model_name="logentry",
            constraint=models.CheckConstraint(
                condition=models.Q(fatigue_level__in=("", "ok", "tired")),
                name="logentry_fatigue_canonical",
            ),
        ),
        migrations.AddConstraint(
            model_name="logentry",
            constraint=models.CheckConstraint(
                condition=models.Q(is_sick__in=("", "no", "yes")),
                name="logentry_is_sick_canonical",
            ),
        ),
        migrations.AddConstraint(
            model_name="logentry",
            constraint=models.CheckConstraint(
                condition=models.Q(source__in=("manual", "voice", "cgm", "import", "demo")),
                name="logentry_source_canonical",
            ),
        ),
    ]
