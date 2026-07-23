"""
ModulePatientContext — frozen patient snapshot passed from chassis to modules.

Modules NEVER receive a Django ORM User or PatientProfile object (expert review
C3, ADR-0008). The chassis constructs this from verified JWT claims +
PatientProfile fields and passes it into module analyze() calls and narrate().

A module never constructs this object itself.

See docs/architecture/module-contract-spec.md section 2 for full spec.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class ModulePatientContext:
    patient_id: int
    # Django User PK (integer). NOT a UUID — PatientProfile.id is int (C7, ADR-0008).

    language: str
    # BCP-47 language code for the current session.
    # Example: "fr", "ar-MA", "en"

    region: str
    # ISO 3166-1 alpha-2 country code.
    # Example: "MA" (Morocco), "AE" (UAE)

    consent_flags: dict[str, bool]
    # Consent decisions relevant to this module.
    # Keys are consent slugs defined per module.
    # Example: {"ai_analysis": True, "data_export": False}
    # NEVER include ORM objects, raw PHI, or auth tokens.
