# P0.3 — IAmina Structured Insight Gateway

> **Status:** implementation lot under certification.  
> **Scope:** remove the last structured diabetes text-provider bypass identified as TD-014.  
> **Non-scope:** no clinical detector, threshold, fallback wording, JSON schema, patient-facing UX, persistence, migration or provider selection change.

## Acceptance contract

P0.3 is complete only when all of the following are true:

- `diabetes.services.clinical.engine._format_with_llm()` no longer imports or calls `llm.factory.get_llm` directly;
- structured deterministic-pattern formatting uses `GatewayLLM` with `Capability.SURFACE_DETERMINISTIC_PATTERN`;
- provider egress still passes the existing consent/authorization, PHI stripping and logging middleware owned by the shared gateway;
- the existing JSON parsing, fallback behavior and `sanitize_patient_visible()` output policy remain unchanged;
- a permanent source contract prevents reintroduction of direct provider access in the structured formatter;
- canonical CI and migration drift pass on the exact PR head;
- Clinical Safety Reviewer and Release Certifier pass on that exact head;
- TD-014 is removed only after the implementation is proven and canonical docs are aligned;
- post-merge CI and migration drift pass on `main` before the lot is declared 100% closed.
