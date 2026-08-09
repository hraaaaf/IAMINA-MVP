from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("diabetes", "0021_logentry_meal_portions")]

    operations = [
        migrations.AlterField(model_name="logentry", name="exercised", field=models.CharField(blank=True, choices=[("yes", "Oui"), ("no", "Non")], default="", help_text="Exercice aujourd\'hui ?", max_length=3)),
        migrations.AlterField(model_name="logentry", name="sleep_quality", field=models.CharField(blank=True, choices=[("good", "Bonne"), ("bad", "Mauvaise")], default="", help_text="Qualite du sommeil", max_length=4)),
        migrations.AlterField(model_name="logentry", name="stressed", field=models.CharField(blank=True, choices=[("yes", "Oui"), ("no", "Non")], default="", help_text="Niveau de stress", max_length=3)),
        migrations.AlterField(model_name="logentry", name="fatigue_level", field=models.CharField(blank=True, choices=[("ok", "Bien"), ("tired", "Fatigué(e)")], default="", help_text="Niveau de fatigue aujourd\'hui", max_length=5)),
        migrations.AlterField(model_name="logentry", name="is_sick", field=models.CharField(blank=True, choices=[("no", "Non"), ("yes", "Oui")], default="", help_text="Malade ou pas bien aujourd\'hui", max_length=3)),
    ]
