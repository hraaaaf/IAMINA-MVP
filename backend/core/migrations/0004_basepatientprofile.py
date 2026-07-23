from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_erasurerecord'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='BasePatientProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('firebase_uid', models.CharField(
                    blank=True, db_index=True, max_length=128, null=True, unique=True,
                    help_text='Firebase Auth UID — chassis-level auth bridge.',
                )),
                ('preferred_language', models.CharField(
                    choices=[('fr', 'Français'), ('ar-MA', 'Darija (dialecte marocain)'), ('ar', 'Arabe classique (Fusha)')],
                    default='ar-MA', max_length=8,
                    help_text='UI language preference.',
                )),
                ('ai_consent_given_at', models.DateTimeField(
                    blank=True, null=True,
                    help_text='Timestamp when the patient explicitly consented to AI analysis. NULL = no consent.',
                )),
                ('premium_valid_until', models.DateTimeField(
                    blank=True, null=True,
                    help_text='End of paid Premium access.',
                )),
                ('gender', models.CharField(
                    choices=[('male', 'Homme'), ('female', 'Femme')],
                    default='female', max_length=6,
                    help_text='Genre',
                )),
                ('date_of_birth', models.DateField(help_text='Date de naissance')),
                ('weight', models.DecimalField(
                    blank=True, decimal_places=1, max_digits=5, null=True,
                    help_text='Weight in kg',
                )),
                ('height', models.IntegerField(
                    blank=True, null=True,
                    help_text='Height in cm',
                )),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('patient', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='base_profile',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'verbose_name': 'Base Patient Profile',
                'verbose_name_plural': 'Base Patient Profiles',
                'app_label': 'core',
            },
        ),
    ]
