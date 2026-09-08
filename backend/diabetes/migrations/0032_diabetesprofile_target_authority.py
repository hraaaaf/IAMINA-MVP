from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('diabetes', '0031_cgmsensorsession_cgmreadingrecord_session'),
    ]

    operations = [
        migrations.AddField(
            model_name='diabetesprofile',
            name='target_confirmed_at',
            field=models.DateTimeField(
                blank=True,
                help_text=(
                    'Timestamp of explicit clinician confirmation. NULL means no current '
                    'clinician-confirmed target authority.'
                ),
                null=True,
            ),
        ),
        migrations.AddField(
            model_name='diabetesprofile',
            name='target_population_context',
            field=models.CharField(
                choices=[
                    ('unknown', 'Unknown'),
                    ('general_nonpregnant_adult', 'General nonpregnant adult'),
                    ('older_complex', 'Older adult — complex/intermediate health'),
                    ('pregnancy', 'Pregnancy'),
                    ('individualized', 'Individualized / other'),
                ],
                default='unknown',
                help_text=(
                    'Explicit population/applicability context for a clinician-confirmed '
                    'target. Never inferred from demographic fields.'
                ),
                max_length=32,
            ),
        ),
        migrations.AddField(
            model_name='diabetesprofile',
            name='target_range_provenance',
            field=models.CharField(
                choices=[
                    ('legacy_default', 'Legacy default'),
                    ('patient_declared', 'Patient declared'),
                    ('clinician_confirmed', 'Clinician confirmed'),
                    ('clinician_confirmation_stale', 'Clinician confirmation stale'),
                ],
                default='legacy_default',
                help_text=(
                    'Authority provenance for the configured range. Legacy/patient-declared '
                    'ranges are descriptive only.'
                ),
                max_length=32,
            ),
        ),
        migrations.AddField(
            model_name='diabetesprofile',
            name='target_time_in_range_goal_pct',
            field=models.FloatField(
                blank=True,
                help_text=(
                    'Clinician-confirmed minimum percentage of verified CGM readings expected '
                    'inside the configured range. NULL means no target-attainment judgment.'
                ),
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name='diabetesprofile',
            name='target_range_high',
            field=models.IntegerField(
                default=180,
                help_text=(
                    'Configured upper glucose range bound (mg/dL). This value alone is not '
                    'clinical target authority; see target_range_provenance.'
                ),
            ),
        ),
        migrations.AlterField(
            model_name='diabetesprofile',
            name='target_range_low',
            field=models.IntegerField(
                default=70,
                help_text=(
                    'Configured lower glucose range bound (mg/dL). This value alone is not '
                    'clinical target authority; see target_range_provenance.'
                ),
            ),
        ),
    ]
