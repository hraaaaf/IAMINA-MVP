# ADR-0009 — V1 P3 module HTTP aliases remain dormant

**Date:** 2026-10-11  
**Status:** ACCEPTED — founder decision A; implementation certification pending  
**Decision:** [#929](https://github.com/hraaaaf/IAMINA-MVP/issues/929), [DRAFT #937](https://github.com/hraaaaf/IAMINA-MVP/pull/937)  
**Refines:** [ADR-0008](ADR-0008-platform-chassis.md) for the **V1 HTTP routing exposure only**. The platform chassis and ModuleRegistry contract remain in force.

## Context and evidence

The live canonical diabetes APIs include `/api/v1/logs/*` and `/api/v1/ai/chat` (including SSE). The historical `DIABETES_MANIFEST.url_prefix="/diabetes"` **reserved** a future namespace, while its declared `interactive_endpoints` advertised `/api/v1/diabetes/ai/chat` although the registered module router was `logs_router` without any chat endpoint.

In [#936](https://github.com/hraaaaf/IAMINA-MVP/pull/936), an isolated Django startup test showed `ModuleRegistry.all()` observed an empty registry before `DiabetesConfig.ready()` registered the diabetes module. Consequently, the historical dynamic `add_router` loop did not mount P3 aliases in that CI construction. The alias was 404 in Django resolver and absent from OpenAPI. **This accidental import-order behavior is not an acceptable security boundary.**

## Accepted V1 decision — option A

1. **No `/api/v1/diabetes/*` HTTP aliases are exposed for V1.** `url_prefix="/diabetes"` remains reserved module metadata only; it is not a live URL.
2. `diabetes.api.main` mounts **explicit canonical routers only**, never automatically mounts `ModuleRegistry.all()`.
3. `ModuleRegistry` continues to register the diabetes engine and module state. No patient/module data migration.
4. `DIABETES_MANIFEST.interactive_endpoints` lists the actually reachable `/api/v1/ai/chat`. `DiabetesConfig.ready()` derives `TRIAGE_REGISTRY` paths from that list. Dormant aliases must not be advertised as protected/reachable, but **real canonical chat and emergency SSE triage remain protected**.
5. Tests must verify alias 404 even on an urgent synthetic message, absent OpenAPI and Django resolver entries, no provider invocation on dormant paths, canonical chat triage, and no registration-driven router assembly after a clean Django boot.

## Rationale and alternatives

**Chosen: explicitly dormant** — smallest risk surface, preserves existing clients and clinical safety contracts, removes dependency on import order.

**Deferred: activate namespaced aliases** — would need a separate route design. Reusing `logs_router` cannot expose a chat route and mounting the same Ninja Router twice may require separate prefixes/instances. A future activation would require complete auth, cookie CSRF, patient scope, versioning, triage, consent, compatibility and SQLite/PostgreSQL tests, then independent privacy/security/clinical review. No implicit feature toggle or migration is authorized now.

## Consequences and release gates

- Canonical Flutter/web routes and deterministic triage should remain unchanged; all new aliases remain 404.
- Existing historical docs asserting that aliases are already active are not current proof and must be updated when relevant.
- A future activation requires a **new founder decision/ADR, isolated PR, exact-head CI, threat/privacy review, and clinical approval**. No automatic merge, Vercel deployment, cloud media egress or real-patient rollout from this ADR.
- `NOT_RELEASE_AUTHORIZED` remains the product release posture.
- Engineering verification is attached to **PR #937 exact HEAD and workflow results**, not inferred from the prior #936 16/16 green result. Until #937 CI succeeds, implementation is candidate, not certified.
