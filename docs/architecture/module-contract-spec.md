# Module Contract Specification — IAmina Platform Chassis v4.0

**Date:** 2026-06-04
**Status:** ACCEPTED (P0 spec — no code P3+ before this document exists)
**ADR:** ADR-0008-platform-chassis.md
**Owner:** Platform team
**Implements conditions:** C3, C6, C7, C8 from expert review (`ARCHITECTURE.md`)

---

## Purpose

This document specifies the exact Python types and abstract interface every condition module must implement to plug into the IAmina chassis. No P3 (module router) code may be written before this spec is accepted.

---

## 1. ModuleManifest

A frozen dataclass that every module declares at startup. The chassis reads this to mount the module, configure triage protection, and route observability events.

```python
from dataclasses import dataclass, field

@dataclass(frozen=True)
class ModuleManifest:
    name: str
    # Human-readable module name. Example: "Diabetes Companion"

    version: str
    # Semver string. Example: "1.0.0"

    condition: str
    # Snake-case condition slug. Example: "diabetes", "hypertension"

    url_prefix: str
    # Static string — NO path params. Django Ninja add_router() does not accept
    # path parameters in prefixes (expert review C6).
    # Example: "/v1/diabetes" — NOT "/v1/{condition}/"

    tags: list[str]
    # OpenAPI tags for this module's endpoints. Example: ["diabetes", "glucose"]

    supported_languages: list[str]
    # BCP-47 language codes. Example: ["fr", "ar-MA", "en"]

    interactive_endpoints: list[str]
    # Endpoint paths that require TriageVitalMiddleware protection.
    # Registered into AppendOnlyTriageRegistry at startup via DiabetesConfig.ready().
    # Example: ["/api/v1/ai/chat"]

    acquisition_event: str
    # ObservabilityEvent type that marks a new user acquisition for this module.
    # Used by the retention dashboard cohort query.
    # Example: "LOG_CREATED"
```

**Diabetes module instance (reference):**

```python
DIABETES_MANIFEST = ModuleManifest(
    name="Diabetes Companion",
    version="1.0.0",
    condition="diabetes",
    url_prefix="/v1/diabetes",
    tags=["diabetes", "glucose", "ai"],
    supported_languages=["fr", "ar-MA", "en"],
    interactive_endpoints=["/api/v1/ai/chat"],
    acquisition_event="LOG_CREATED",
)
```

---

## 2. ModulePatientContext

A frozen dataclass passed from the chassis to modules. Modules NEVER receive a Django ORM `User` or `PatientProfile` object (expert review C3).

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class ModulePatientContext:
    patient_id: int
    # Django User PK (integer). NOT a UUID — PatientProfile.id is int (expert review C7).

    language: str
    # BCP-47 language code for the current session. Example: "fr", "ar-MA"

    region: str
    # ISO 3166-1 alpha-2 country code. Example: "MA", "AE"

    consent_flags: dict[str, bool]
    # Consent decisions relevant to this module.
    # Keys are consent slugs. Example: {"ai_analysis": True, "data_export": False}
    # NEVER include ORM objects, raw PHI, or auth tokens.
```

**Construction rule:** The chassis constructs `ModulePatientContext` from the verified JWT claims + `PatientProfile` fields. A module never constructs this object itself.

---

## 3. DomainContext (chassis-level output)

The structured clinical output a module returns to the chassis after running its `analyze()` method. The chassis uses this to drive the LLM narrative engine (`core/llm_gateway.narrate()`).

```python
from dataclasses import dataclass, field

@dataclass
class DomainContext:
    kpi_summary: dict
    # Module-computed KPIs as a plain dict. Example:
    # {"tir_pct": 68.2, "gmi": 7.1, "cv_pct": 33.4, "entries": 42}
    # Values must be JSON-serializable (no ORM objects, no numpy types).

    detected_patterns: list[str]
    # Human-readable pattern labels. Example:
    # ["dawn_phenomenon", "post_exercise_hypoglycemia"]

    insights: list[str]
    # English plain-text clinical insights for the LLM prompt.
    # PHI-free: no patient names, no DOB, no national IDs.
    # Example: ["Patient shows consistent dawn phenomenon over 7 days."]

    pivot_text: str
    # Compressed English pivot text for the LLM system prompt.
    # Output of SemanticCompressor. PHI-free.

    language: str
    # BCP-47 target language for the narrative response.
    # Example: "ar-MA" (Darija), "fr"
```

**Key distinction:** This `DomainContext` is the **chassis-level output struct** (clinical data flowing chassis ← module). It is NOT the companion identity struct (which is `CompanionIdentity` — see section 5 below).

---

## 4. BaseEngine.analyze() — Required Module Method

Every module must implement this method via the `BaseEngine` ABC (`core/engine/base.py`):

```python
from abc import ABC, abstractmethod
from core.contracts.domain_context import DomainContext

class BaseEngine(ABC):

    @abstractmethod
    def analyze(self, patient_id: int, language: str) -> DomainContext:
        """
        Run the module's clinical analysis pipeline and return a DomainContext.

        Rules:
        - patient_id is an integer (Django User PK), NOT a UUID (expert review C7)
        - Modules fetch their own data internally (LogEntry, PatientProfile, etc.)
        - The returned DomainContext must be PHI-free (no names, no DOB, no CIN)
        - The method must never call get_llm() directly — only the chassis calls narrate()
        - Raise ValueError if patient_id does not exist or has no usable data
        """
        ...
```

**Old (incompatible) signature — DO NOT USE:**
```python
# Pre-P0 signature — diabetes-specific types leaked into the ABC
def analyze(self, entries, kpis, language): ...
```

---

## 5. CompanionIdentity

The companion persona struct. Carries the companion's name, domain description, and measurement unit. Previously named `DomainContext` in `clinical/domain_context.py` — renamed to eliminate the collision with the chassis output struct (ADR-0008).

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class CompanionIdentity:
    companion_name: str
    # Display name of the companion. Example: "IAmina", "IAmina Cardio"

    domain_description: str
    # One-phrase domain description for the LLM system prompt.
    # Example: "diabetes management", "hypertension monitoring"

    unit: str
    # Primary measurement unit for this condition.
    # Example: "mg/dL" (diabetes), "mmHg" (hypertension)
```

**Backward compatibility:** `clinical/domain_context.py` exports `DomainContext` as an alias for `CompanionIdentity` until P4 wires `DiabetesEngine.analyze()`. All new code must import `CompanionIdentity` from `core.contracts.companion_identity`.

---

## 6. LLM Gateway Entry Point

`core/llm_gateway.narrate()` is the **only authorized LLM call surface** in the chassis (expert review C1). No module may import `get_llm()` or call `LLMPipeline` directly.

```python
def narrate(
    patient_context: ModulePatientContext,
    domain_context: DomainContext,
    companion_identity: CompanionIdentity,
    language: str,
) -> str:
    """
    Build a PHI-safe narrative response from module output.

    Pipeline:
    1. PHIPseudonymizer.calibrate(patient_context.patient_id)
    2. Build system prompt from companion_identity + language
    3. Build user prompt from domain_context
    4. PHIPseudonymizer.mask(system) + mask(user)
    5. LLMPipeline([PHIStrippingMiddleware, LoggingMiddleware]).complete(system, user)
    6. PHIPseudonymizer.unmask(response.content)
    7. Return plain string

    Raises:
    - PHILeakError if PHIStrippingMiddleware detects a pattern in the masked prompts
    """
    ...
```

---

## 7. Triage Registration Protocol

Every module with interactive endpoints (chat, voice, AI analysis) must register those paths at startup. Registration is append-only — no clear or delete.

```python
# In DiabetesConfig.ready() (diabetes/apps.py):
from core.safety_registry import TRIAGE_REGISTRY
TRIAGE_REGISTRY.register_path("/api/v1/ai/chat")
# Update to /api/v1/diabetes/ai/chat when P3 mounts modules under /diabetes/ prefix
```

`TriageVitalMiddleware` reads `TRIAGE_REGISTRY._paths` at request time. A path not in the registry is not triage-protected — any module adding a chat endpoint MUST register it.

---

## 8. RGPD Delete Hook Protocol

Every module must register a cleanup hook at startup. The chassis calls all hooks when a patient requests account deletion. Any hook failure blocks the response (RGPD Article 17).

```python
# In DiabetesConfig.ready() (diabetes/apps.py):
from core.account_hooks import register_account_delete_hook
register_account_delete_hook(lambda patient_id, firebase_uid: cleanup_diabetes_data(patient_id))
```

Hook signature: `Callable[[int, str], None]` — `(patient_id: int, firebase_uid: str) -> None`.

---

## 9. Naming Conventions Summary

| Concept | Class name | Location | Notes |
|---|---|---|---|
| Companion persona | `CompanionIdentity` | `core/contracts/companion_identity.py` | Was `DomainContext` in clinical/ — renamed ADR-0008 |
| Clinical output (chassis) | `DomainContext` | `core/contracts/domain_context.py` | New in P0 — chassis ← module data flow |
| Module declaration | `ModuleManifest` | `core/contracts/manifest.py` | Frozen dataclass |
| Patient snapshot (no ORM) | `ModulePatientContext` | `core/contracts/patient_context.py` | Frozen dataclass |
| Backward compat shim | `DomainContext` alias | `clinical/domain_context.py` | Alias for `CompanionIdentity`; remove in P4 |

---

## 10. Out of Scope for This Spec

The following are intentionally deferred to their respective phases:

- Module router mount mechanism (P3) — `core/api/main.py` dynamic routing
- Pattern detection service (P4) — `core/patterns/`
- `BasePatientProfile` split from `PatientProfile` (P2)
- Module isolation enforcement via system check (C9)
- Multi-module event aggregation (post Retention Gate)
