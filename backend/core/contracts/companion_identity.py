"""
CompanionIdentity — carries companion persona through the engine layer.

Previously named DomainContext in clinical/domain_context.py.
Renamed in ADR-0008 (2026-06-04) to eliminate collision with the chassis-level
DomainContext output struct (core/contracts/domain_context.py).

Created by each module's domain config and injected into IAmina brain,
prompts, and router calls. The engine never hardcodes companion_name
or domain_description.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class CompanionIdentity:
    companion_name: str       # "IAmina", "IAmina Cardio", …
    domain_description: str   # "diabetes management", "hypertension monitoring", …
    unit: str                 # "mg/dL", "mmHg", …
