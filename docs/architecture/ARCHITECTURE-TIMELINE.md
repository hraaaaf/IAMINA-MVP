# Architecture Timeline — how the design got here

> This is the condensed decision history. It exists so the superseded version docs (v1.0, v2.x,
> v3.0, v3.1, the multi-capsule audit, the French implementation log) could be deleted without
> losing *why* each direction was chosen and then changed. Current design: `ARCHITECTURE.md`.
> Formal decisions: `docs/adr/`. Forward tracker: `docs/ROADMAP.md`.

The project changed architectural direction several times. The throughline: **a Darija/Arabic
diabetes companion whose real success metric is 90-day retention, not feature/condition breadth.**
Every reversal was a re-answer to one question — *build platform optionality now, or defer it until
retention proves there's a business?*

---

## v1.0 — Modular monolith (baseline)

The original Django app: LLM factory, IAmina companion, clinical engine, middleware pipeline, one
condition (diabetes). No module abstraction. This is the substrate everything below refactors.

## v2.0 — Engine / capsule split (implemented, branch `refactor/chassis-architecture`)

Introduced a hard boundary: a domain-agnostic **engine** vs a diabetes **capsule**, with
`SemanticCompressor` as the single seam between clinical data and the LLM. Renamed `tracking`→
`diabetes` and the chassis concept for clarity. Real refactor, shipped. (v2.0-chassis-target was a
pure naming-clarification artifact on top of this.)

## v2.2 — Engine decomposition (proposal, NOT implemented)

Proposed splitting `engine/` into `llm/`, `safety/`, `companion/`, `clinical/`, `media/` packages,
plus an `EngineRegistry` with plugin dispatch. The package decomposition idea partly survived; the
`EngineRegistry`/plugin-dispatch machinery was rejected downstream as premature. Superseded by v3.1.

## v3.0 — Multi-condition platform (proposal)

The full platform vision: `BaseEngine` ABC, **`EngineRegistry` runtime dispatch**, modular
middleware, `LLMPipeline`, split `PatientProfile`. The high-water mark of "build the platform now."
The `BaseEngine` ABC survived; the runtime registry/dispatch did not (yet).

## v3.1 / DA-03 — "Modular monolith, NOT a platform" (ACCEPTED 2026-06-03)

**The first reversal.** Decision: ship ONE condition with *cheap seams* (`BaseEngine` ABC,
`BasePatientProfile`) so a second condition is a future refactor, not a rewrite — but do **NOT**
build platform machinery (plugin API, `EngineRegistry` dispatch, webhooks, multi-tenancy). Rationale:
it's premature for a pre-revenue product. **Redirect that budget into observability/retention
instrumentation**, because 90-day retention is the metric that decides whether this is a business.

The **Retention Gate** was born here: don't build condition #2 or any platform machinery until BOTH
(1) D90 retention clears a go threshold AND (2) one named payer signal exist. This gate still stands.

> The cheap fixes from the v3.x multi-capsule readiness audit (move universal account/auth/health
> endpoints to `core/`, triage path registry) were folded into v3.1's seam work (S1–S5).

## ADR-0008 — Platform chassis (ACCEPTED 2026-06-04) — **CURRENT**

**The second reversal.** The founder reopened the DA-03 decision and authorized building the full
**platform chassis + module contracts** model now (`ARCHITECTURE.md`), as a *scoped, gated detour*.
What changed: the cheap seams became real seams (registry, contracts, profile split, import-linter).
What did NOT change: DA-03's strategic core — **one condition live, retention-first, no live second
module until the Retention Gate passes.**

An expert review (Software Architect · Backend · Security · Product) returned
APPROVE_WITH_CONDITIONS with 14 conditions (PHI gateway, triage registry, RGPD cascade,
SeparateDatabaseAndState migration risk, static router mount, `analyze()` signature, etc.). All 14
were resolved during the build — see the Expert Review section in `ARCHITECTURE.md`.

The chassis program (P0–P6 + P8.1) was built and merged 2026-06-05 → 06-07. It is now tracked as
**ROADMAP Phases 18–26**; the detailed implementation record is `platform-transformation-plan.md`
(archived). Phases 25–26 (live second module, third-party infra) remain **gated**.

---

## What survived every reversal (the stable core)

- One condition live (diabetes); breadth is deferred, not the strategy.
- **The Retention Gate** — still the go/stop for a second module (D90 threshold still unset).
- `BaseEngine` ABC as the clinical seam (refactored, never discarded).
- SQL-first KPIs (ADR-0007), PHI stripped before the LLM, `TriageVitalMiddleware` first in chain,
  `client_uuid` offline idempotency, no diagnosis / no prescription.
