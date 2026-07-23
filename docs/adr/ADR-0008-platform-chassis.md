# ADR-0008 — Platform Chassis Model

**Date:** 2026-06-04
**Status:** ACCEPTED
**Decision owners:** Founder + architecture review
**Supersedes:** DA-03 v3.1 (modular monolith decision — `docs/architecture/ARCHITECTURE-TIMELINE.md`)
**References:**
- Expert review results: `docs/architecture/ARCHITECTURE.md` (APPROVED_WITH_CONDITIONS, 14 conditions)
- Platform transformation plan: `docs/architecture/platform-transformation-plan.md`

---

## Context

DA-03 (v3.1) locked the architecture as a **modular monolith with extension seams** and explicitly deferred platform machinery until the Retention Gate (D90 ≥ threshold + one payer signal). The decision was made on cost grounds: building multi-module infrastructure before validating product-market fit with a single condition wastes engineering capacity.

On **2026-06-04**, the founder reversed this decision and directed the team to move to a **platform chassis + pluggable modules** model. This ADR documents that trigger, the accepted model, the constraints, and what DA-03 guidance remains in force.

---

## Trigger for Reversal

**Founder decision, 2026-06-04.** The trigger was architectural clarity: the seam-based monolith (DA-03) was accumulating implicit coupling that would require a large-scale rewrite when the second module eventually ships. Moving to explicit contracts now — while the codebase is still small — was judged cheaper than deferring and refactoring under time pressure post-gate.

The Retention Gate rule is **preserved** (see below). This ADR does not authorize building module 2. It authorizes building the chassis contract layer so that module 2 can be added cleanly when the gate passes.

---

## Decision

Adopt the **platform chassis + module contracts** model described in `docs/architecture/ARCHITECTURE.md`.

### Chassis services (four)
1. **Patient Identity + Auth** — Firebase JWT → Django User bridge. Modules receive an authenticated patient object; they never manage auth.
2. **LLM Narrative Engine** (`core/llm_gateway.py`) — the sole LLM entry point. PHI stripped before any model call. Module-agnostic: receives structured domain context, returns narrative text.
3. **Pattern Detection + Nudges** — chassis-owned, cross-module behavioral trend detection. Never diagnoses or prescribes.
4. **Observability + Retention** — `core/observability/` (already built, S4+S5). D1/D7/D30/D90 cohort tracking.

### Module contract
Every condition module (diabetes, future) implements:
- `ModuleManifest` — frozen dataclass declaring name, version, condition, url_prefix, tags, supported_languages, interactive_endpoints, acquisition_event
- `BaseEngine.analyze(patient_id: int, language: str) → DomainContext` — module fetches its own data internally; chassis receives structured output only
- `interactive_endpoints` — list of endpoint paths the module exposes that require triage protection; chassis `TriageVitalMiddleware` reads from this registry

Full contract spec: `docs/architecture/module-contract-spec.md`

---

## Retention Gate Rule

**The second module (hypertension or other) is NOT authorized until:**
1. D90 retention threshold passes (specific threshold TBD — recorded in CLAUDE.md Open Decisions; placeholder ≥25% in ROADMAP)
2. One payer signal confirmed (pharma B2B contract or equivalent)

This rule is binding regardless of platform readiness. The orange-box "Future Module" in the architecture diagram is a placeholder, not a build target.

Building the chassis contract layer (P0–P1) does not violate this gate — it enables clean module addition when the gate passes. Building module 2 code before the gate violates this decision.

---

## Expert Review Conditions (accepted)

The expert review (2026-06-04) returned APPROVE_WITH_CONDITIONS with 14 conditions. This ADR accepts all 14 as binding constraints on P1–P5 execution. Critical conditions resolved by this plan (P0+P1):

| Condition | Description | Resolution |
|---|---|---|
| C1 | PHI bypass via direct LLM access | `core/llm_gateway.py` narrate() is sole entry point (Phase E) |
| C2 | TriageVitalMiddleware blind to new routes | Moved to `core/middleware/`, reads `AppendOnlyTriageRegistry` (Phase B) |
| C4 | RGPD cascade incomplete on DELETE /account | Hook registry + Firebase deletion + ErasureRecord (Phase C) |
| C8 | API contract not specified | `docs/architecture/module-contract-spec.md` + `core/contracts/` package (Phase A) |

Remaining conditions (C3, C5, C6, C7, C9–C14) are resolved in subsequent plans (P2–P5).

---

## Naming Collision Resolution (P0)

This ADR also resolves a naming collision created by the v4.0 proposal:

| Old name | Old location | Old role | Action |
|---|---|---|---|
| `DomainContext` | `clinical/domain_context.py` | Companion identity (name, description, unit) | Renamed `CompanionIdentity`, moved to `core/contracts/companion_identity.py` |
| `DomainContext` | (new chassis concept) | Clinical output struct (kpis, patterns, insights, pivot_text) | New class, defined in `core/contracts/domain_context.py` |

The old `clinical/domain_context.py` is retained as a shim (`from core.contracts.companion_identity import CompanionIdentity as DomainContext`) for backward compatibility until P4 wires `DiabetesEngine.analyze()`.

---

## What DA-03 Guidance Remains in Force

All safety invariants from DA-03 are non-negotiable and carry forward:

- `TriageVitalMiddleware` must remain FIRST in the MIDDLEWARE chain
- `UnitGuardMiddleware` must remain SECOND
- PHI stripped before reaching any LLM (pseudonymizer as middleware)
- SQL-first KPIs (ADR-0007 — no Python-computed KPIs)
- `client_uuid` on `LogEntry` — offline sync idempotency
- No diagnosis, no prescription — companion role only

---

## Consequences

**Positive:**
- Formal contract eliminates implicit coupling before it compounds
- `ModulePatientContext` prevents ORM objects leaking into modules (security)
- `AppendOnlyTriageRegistry` eliminates hardcoded paths (patient safety)
- RGPD compliance enforced structurally via hook registry (legal)
- `narrate()` gateway makes PHI enforcement auditable (security)

**Negative / Trade-offs:**
- Engineering cost now vs. deferred: ~2 sprint weeks on P0–P1 before any feature work
- The chassis is overhead for a single-module system — only justified if module 2 ships
- D90 threshold still TBD — if the gate never passes, the chassis is sunk cost

**Mitigations:**
- P0–P1 are bounded to spec work + security fixes; no new module infrastructure
- Each phase is independently verifiable and independently reversible
- The Retention Gate rule prevents runaway platform investment

---

## Alternatives Considered

| Alternative | Rejected because |
|---|---|
| Continue DA-03 v3.1 (defer platform) | Founder reversal — coupling cost is now visible and compounding |
| Full microservices split | Premature — single-team, single-market, pre-gate |
| Build module 2 now (hypertension) | Violates Retention Gate — no D90 data, no payer signal |
