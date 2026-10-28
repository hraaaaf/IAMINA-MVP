from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0019_auth_abuse_bucket"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="W02VaultRevisionAnchor",
            fields=[
                ("id", models.BigAutoField(
                    auto_created=True, primary_key=True, serialize=False,
                    verbose_name="ID",
                )),
                ("slot", models.CharField(max_length=43, unique=True)),
                ("committed_revision", models.PositiveBigIntegerField(default=0)),
                ("committed_envelope_sha256", models.CharField(
                    blank=True, default="", max_length=64,
                )),
                ("pending_revision", models.PositiveBigIntegerField(
                    blank=True, null=True,
                )),
                ("pending_ticket", models.CharField(
                    blank=True, default="", max_length=43,
                )),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("patient", models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="w02_revision_anchor",
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                "constraints": [
                    models.CheckConstraint(
                        condition=models.Q(committed_revision__gte=0),
                        name="core_w02_committed_nonnegative",
                    ),
                ],
            },
        ),
    ]
