from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('diabetes', '0019_reconcile_model_migration_state'),
    ]

    operations = [
        migrations.AddField(
            model_name='logentry',
            name='glycemic_context',
            field=models.CharField(
                blank=True,
                choices=[
                    ('fasting', 'À jeun'),
                    ('pre_meal', 'Avant repas'),
                    ('post_meal', 'Après repas'),
                    ('other', 'Autre contexte'),
                ],
                default='',
                help_text='Contexte de la mesure: à jeun, avant/après repas ou autre',
                max_length=12,
            ),
        ),
    ]
