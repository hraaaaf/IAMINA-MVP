from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('diabetes', '0020_logentry_glycemic_context'),
    ]

    operations = [
        migrations.AddField(
            model_name='logentry',
            name='meal_portions',
            field=models.JSONField(
                blank=True,
                default=list,
                help_text=(
                    'Portions confirmées par le patient. Contient uniquement la saisie '
                    'utilisateur (food_id, portion_id et/ou grammes), jamais un calcul '
                    'nutritionnel présenté comme vérité persistée.'
                ),
            ),
        ),
    ]
