from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0019_auth_abuse_bucket"),
    ]

    operations = [
        migrations.AlterField(
            model_name="basepatientprofile",
            name="preferred_language",
            field=models.CharField(
                choices=[
                    ("fr", "Français"),
                    ("ar-MA", "Darija (dialecte marocain)"),
                    ("ar", "Arabe classique (Fusha)"),
                    ("en", "English"),
                ],
                default="ar-MA",
                help_text="UI language preference.",
                max_length=8,
            ),
        ),
    ]
