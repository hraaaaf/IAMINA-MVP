from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_basepatientprofile'),
    ]

    operations = [
        migrations.CreateModel(
            name='PatientModule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('module_name', models.CharField(
                    max_length=64,
                    help_text="Slug identifier for the module (e.g. 'diabetes').",
                )),
                ('activated_at', models.DateTimeField(auto_now_add=True)),
                ('is_active', models.BooleanField(default=True)),
                ('patient', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='modules',
                    to='core.basepatientprofile',
                )),
            ],
            options={
                'verbose_name': 'Patient Module',
                'verbose_name_plural': 'Patient Modules',
                'unique_together': {('patient', 'module_name')},
                'app_label': 'core',
            },
        ),
    ]
