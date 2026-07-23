"""
Demo scenarios for the 1-button launch flow (`/demo/` and — future — `/api/v1/demo/*`).

Scenario data (three weeks of glycaemic logs for a realistic patient profile)
is kept separate from the view so the same dataset can power both the HTML
demo and a future Ninja endpoint. Today only scenario A ships; scenarios
B–H mentioned in `AMINA_MVP_PLAN.md` §5 were simplified out during a prior
pass and need to be restored — tracked in `techdebt.md` TD-015.
"""

from __future__ import annotations

import logging
import random
from datetime import datetime, timedelta
from typing import TypedDict

from django.contrib.auth.models import User

logger = logging.getLogger(__name__)


class ScenarioEntry(TypedDict, total=False):
    days_ago: int
    hours: int
    meal: str
    desc: str
    insulin: int
    sugar: int
    exercised: str
    stressed: str


# ─────────────────────────────────────────────
# Scenario catalog
# ─────────────────────────────────────────────

SCENARIO_A: list[ScenarioEntry] = [
    {"days_ago": 16, "hours": 8,  "meal": "breakfast", "desc": "Whole wheat bread, olive oil, tea without sugar",  "insulin": 6,  "sugar": 125, "exercised": "no"},
    {"days_ago": 16, "hours": 20, "meal": "dinner",    "desc": "White pasta, bread, soda",                          "insulin": 8,  "sugar": 195, "exercised": "no"},
    {"days_ago": 15, "hours": 13, "meal": "lunch",     "desc": "Chicken, vegetables, small portion of rice",        "insulin": 7,  "sugar": 135, "exercised": "no"},
    {"days_ago": 14, "hours": 20, "meal": "dinner",    "desc": "Pizza, soda",                                       "insulin": 9,  "sugar": 210, "exercised": "no"},
    {"days_ago": 13, "hours": 20, "meal": "dinner",    "desc": "White bread, lentils, juice",                       "insulin": 7,  "sugar": 185, "exercised": "no"},
    {"days_ago": 12, "hours": 8,  "meal": "breakfast", "desc": "Eggs, avocado, no bread",                           "insulin": 5,  "sugar": 115, "exercised": "no"},
    {"days_ago": 11, "hours": 20, "meal": "dinner",    "desc": "Couscous (large portion), bread",                   "insulin": 8,  "sugar": 200, "exercised": "no"},
    {"days_ago": 10, "hours": 20, "meal": "dinner",    "desc": "Pasta, soda, dessert",                              "insulin": 9,  "sugar": 220, "exercised": "no"},
]

SCENARIOS: dict[str, list[ScenarioEntry]] = {
    "A": SCENARIO_A,
}

DEFAULT_SCENARIO_ID = "A"

DEMO_PATIENT_DEFAULTS = {
    "username": "demo_magic",
    "password": "demo1234",
    "first_name": "Youssef",
    "profile": {
        "date_of_birth": "1982-01-01",
        "diabetes_type": "type2",
        "treatment_type": "insulin_injections",
        "target_range_low": 80,
        "target_range_high": 140,
        "gender": "male",
    },
}


def get_scenario(scenario_id: str | None = None) -> list[ScenarioEntry]:
    """Return the scenario dataset; falls back to the default if unknown."""
    if scenario_id and scenario_id in SCENARIOS:
        return SCENARIOS[scenario_id]
    return SCENARIOS[DEFAULT_SCENARIO_ID]


def build_entries(dataset: list[ScenarioEntry], patient: User, now: datetime):
    """
    Build (not save) LogEntry objects from a scenario dataset. The caller
    persists via bulk_create so the service has no ORM side-effects on its
    own and is trivially testable.
    """
    # Local import avoids circular import with logs.models during app loading.
    from ..models import LogEntry

    entries = []
    for d in dataset:
        entry_time = (now - timedelta(days=d["days_ago"])).replace(
            hour=d["hours"], minute=15
        )
        sugar_val = d["sugar"] + random.randint(-3, 3)
        entries.append(LogEntry(
            patient=patient,
            blood_sugar=sugar_val,
            meal_type=d["meal"],
            meal_description=d["desc"],
            insulin_units=d["insulin"],
            exercised=d.get("exercised", "no"),
            sleep_quality="good",
            stressed=d.get("stressed", "no"),
            logged_at=entry_time,
        ))
    return entries


def format_clinical_report(report) -> str:
    """
    Turn a ClinicalReport from `services.clinical.engine` into the
    ⚠️-prefixed summary the AISummary model stores and the view parses.
    Kept here (not in engine) because the format is a presentation contract
    between the demo flow and the summary view.
    """
    lines = []
    for ins in report.insights:
        lines.append(f"\u26a0\ufe0f {ins['title']}")
        lines.append(f"Explication: {ins['content']}")
        lines.append(f"Action: {ins['action']}")
        lines.append("")
    return "\n".join(lines).strip()
