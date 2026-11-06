"""W01/G7: exactly two disposable fictitious patients, PG16-only, no Neon."""
import json
import os
import sys
from pathlib import Path

import django

django.setup()

from django.contrib.auth.models import User  # noqa: E402
from django.db import connection, transaction  # noqa: E402
from django.utils import timezone  # noqa: E402

from core.models import BasePatientProfile  # noqa: E402
from diabetes.models import DiabetesProfile, LogEntry  # noqa: E402

assert connection.vendor == "postgresql", "G7 FUE requires disposable PG16"
folder = Path("w01-g7-fue-proof")
folder.mkdir(exist_ok=True)
fixture_file = folder / "fixtures.json"

if "--verify" in sys.argv:
    saved = json.loads(fixture_file.read_text())
    assert saved["synthetic"] is True and len(saved["patients"]) == 2
    assert User.objects.count() == 2
    assert BasePatientProfile.objects.count() == 2
    assert LogEntry.objects.count() == 2
    assert DiabetesProfile.objects.count() == 0
    for row in saved["patients"]:
        log = LogEntry.objects.get(pk=row["log_id"])
        assert log.patient_id == row["user_id"]
        assert log.blood_sugar == (112 if row["label"] == "a" else 191)
    print("W01_G7_PG16_AFTER=PASS users=2 profiles=2 logs=2 diabetes_profiles=0")
else:
    password = os.environ.get("G7_FUE_PASSWORD", "")
    assert len(password) >= 30
    assert User.objects.count() == 0 and LogEntry.objects.count() == 0
    with transaction.atomic():
        records = []
        for label, value in (("a", 112), ("b", 191)):
            email = "w01-g7-" + label + "@example.invalid"
            user = User.objects.create_user(
                username=email, email=email, password=password
            )
            BasePatientProfile.objects.get_or_create(patient=user)
            log = LogEntry.objects.create(
                patient=user, blood_sugar=value, logged_at=timezone.now()
            )
            records.append({
                "label": label, "email": email, "user_id": user.pk,
                "log_id": log.pk, "blood_sugar": value,
            })
    fixture_file.write_text(
        json.dumps({"synthetic": True, "patients": records}, indent=2) + "\n"
    )
    print("W01_G7_PG16_SEED=PASS users=2 logs=2 no_real_patients=true")
