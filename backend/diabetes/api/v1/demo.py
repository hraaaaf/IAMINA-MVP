"""
Demo scenarios endpoint — Pre-configured patient data for testing.
GET  /api/v1/demo/scenarios — Returns 8 demo scenarios (A–H)
POST /api/v1/demo/seed      — Injects realistic test data for the current user (dev only)
"""

import random
from datetime import timedelta
from typing import List

from django.utils import timezone
from ninja import Router
from pydantic import BaseModel

from core.models import BasePatientProfile
from diabetes.api.v1.security import firebase_auth_backend
from diabetes.models import DiabetesProfile, LogEntry

router = Router(tags=["demo"])


class DemoScenarioResponse(BaseModel):
    id: str
    name: str
    description: str


class SeedResponse(BaseModel):
    created: int
    message: str


@router.get("/demo/scenarios", response=List[DemoScenarioResponse])
def list_demo_scenarios(request):
    scenarios = [
        {"id": "A", "name": "Type 1 — Hyperglycemia Risk",       "description": "Patient with postprandial spikes after high-carb meals"},
        {"id": "B", "name": "Type 2 — Stable Control",           "description": "Patient with well-controlled glucose levels"},
        {"id": "C", "name": "Type 1 — Dawn Phenomenon",          "description": "Patient with early morning spikes"},
        {"id": "D", "name": "Gestational — Fasting Hyperglycemia","description": "Pregnant patient with fasting glucose >105 mg/dL"},
        {"id": "E", "name": "Type 2 — Nocturnal Hypoglycemia",   "description": "Patient with nighttime lows after evening exercise"},
        {"id": "F", "name": "Type 1 — Stress-Induced Spikes",    "description": "Patient showing glucose correlation with stress events"},
        {"id": "G", "name": "Prediabetes — Prevention",          "description": "Pre-diabetic patient with lifestyle recommendations"},
        {"id": "H", "name": "Type 1 — Hypomania Behavior",       "description": "Patient with inconsistent logging & missed insulin"},
    ]
    return scenarios


@router.post("/demo/seed", auth=firebase_auth_backend, response=SeedResponse)
def seed_demo_data(request):
    """
    Injects 30 days of realistic glucose logs for the current authenticated user.
    Idempotent — skips if the user already has ≥ 20 entries.
    """
    user = request.user

    # Idempotency guard
    existing = LogEntry.objects.filter(patient=user).count()
    if existing >= 20:
        return {"created": 0, "message": f"Données déjà présentes ({existing} entrées)."}

    # Ensure BasePatientProfile + DiabetesProfile exist (two-step creation)
    base, _ = BasePatientProfile.objects.get_or_create(
        patient=user,
        defaults={"date_of_birth": "1985-06-15"},
    )
    DiabetesProfile.objects.get_or_create(
        base_profile=base,
        defaults={
            "diabetes_type": "type2",
            "treatment_type": "oral_meds",
            "unit_preference": "mg_dl",
        },
    )

    meal_types = ["Petit-déjeuner", "Déjeuner", "Dîner", "En-cas", "À jeun"]
    now = timezone.now()
    entries = []

    for day_offset in range(30):
        base_date = now - timedelta(days=day_offset)
        # 2–4 logs per day
        for hour in random.sample([7, 12, 19, 22], k=random.randint(2, 4)):
            meal = meal_types[hour // 6 % len(meal_types)]
            # Realistic glucose with some variability
            if meal == "À jeun":
                glucose = random.gauss(105, 12)
            elif meal in ("Déjeuner", "Dîner"):
                glucose = random.gauss(165, 30)
            else:
                glucose = random.gauss(140, 25)

            glucose = max(60.0, min(300.0, round(glucose, 1)))
            logged_at = base_date.replace(hour=hour, minute=random.randint(0, 59), second=0, microsecond=0)

            entries.append(LogEntry(
                patient=user,
                blood_sugar=glucose,
                meal_type=meal,
                logged_at=logged_at,
            ))

    LogEntry.objects.bulk_create(entries)
    return {"created": len(entries), "message": f"{len(entries)} entrées créées."}
