"""W02-F09-B candidate opaque Web refresh family; isolated PG16 only.

Additive schema: no data backfill, no hosted migration authorization.
"""
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
            name="WebRefreshFamily",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("current_digest", models.CharField(max_length=64, unique=True)),
                ("auth_version", models.PositiveIntegerField()),
                ("issued_at", models.DateTimeField()),
                ("last_rotated_at", models.DateTimeField()),
                ("idle_deadline", models.DateTimeField()),
                ("expires_at", models.DateTimeField()),
                ("revoke_at", models.DateTimeField(blank=True, null=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="web_refresh_candidate_families", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "indexes": [
                    models.Index(fields=["user", "revoke_at"], name="core_wrf_user_rev_idx"),
                ],
            },
        ),
        migrations.CreateModel(
            name="WebRefreshConsumedSecret",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("digest", models.CharField(max_length=64, unique=True)),
                ("consumed_at", models.DateTimeField()),
                ("family", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="consumed_secrets", to="core.webrefreshfamily")),
            ],
            options={
                "indexes": [
                    models.Index(fields=["family", "consumed_at"], name="core_wrused_fam_date_idx"),
                ],
            },
        ),
    ]
