from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0010_patient_locale_preference'),
    ]

    operations = [
        migrations.AddField(
            model_name='basepatientprofile',
            name='auth_token_version',
            field=models.PositiveIntegerField(
                default=0,
                help_text='Incrementing revocation version for sovereign IAMINA bearer tokens.',
            ),
        ),
    ]
