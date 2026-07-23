# IAmina — Architecture Timeline

> **Historical document.** This file explains how the architecture evolved.  
> Current architecture: `ARCHITECTURE.md`  
> Forward work: `../ROADMAP.md`  
> Formal decisions: `../adr/`

Do not use this timeline as a backlog.

## v1 — Diabetes monolith

The original system combined the Django application, diabetes data, clinical logic, companion behavior, provider integrations, and safety middleware with limited modular boundaries.

Stable ideas already present:

- one live condition: diabetes;
- deterministic safety middleware;
- diabetes analytics and pattern detection;
- conversational companion layer;
- offline/mobile direction.

## v2 — Engine / domain separation

The codebase began separating shared engine concerns from diabetes-specific concerns.

Goals included:

- clearer domain ownership;
- reusable clinical/companion seams;
- fewer accidental dependencies;
- easier future refactoring without committing to a full plugin platform.

Some package names and layouts from this period were later replaced.

## v3 / DA-03 — Modular monolith, not a platform

The strategy deliberately favored:

- one condition;
- cheap extension seams;
- retention instrumentation;
- no broad plugin ecosystem or multi-tenancy before product proof.

This is where the enduring **Retention Gate** became explicit: disease/module expansion should follow evidence, not architecture enthusiasm.

## ADR-0008 — Platform chassis + module contracts

The founder later authorized building stronger chassis/module seams earlier than DA-03 proposed.

Implemented concepts included:

- module manifests/contracts;
- registry/router seams;
- patient identity/domain separation;
- safety registries;
- account deletion hooks;
- import-boundary enforcement;
- observability/retention foundations.

This was a technical optionality investment, not permission to launch multiple conditions.

**Still true after ADR-0008:** diabetes remains the only live condition until the Retention Gate passes.

Detailed implementation history remains available in git history and ADRs. The obsolete transformation-plan document was intentionally removed so agents do not mistake historical execution instructions for current work.

## 2026-07-23 — MENA sovereignty reset

The product strategy changed from a primarily Morocco/Darija beachhead with a simple Gulf expansion narrative to a broader but more disciplined **MENA-first architecture**.

Key changes:

1. **MENA became the target region**, with country-by-country and locale-by-locale enablement.
2. Language architecture changed from a small fixed language list to a contract separating country, UI language, response language, dialect, script/transliteration, units, time zone, and emergency jurisdiction.
3. Location was explicitly demoted to a suggestion signal; it must not silently determine language, consent, or safety behavior.
4. The AI architecture moved away from “pick the next preferred LLM provider” toward a **provider-agnostic outbound boundary** with independent text/STT/vision choices.
5. Data sovereignty/minimization became P0: legacy direct/provider-specific calls must be inventoried and governed before pilot.
6. Firebase became **legacy current-state**, with Django-native authentication as the sovereignty target.
7. The clinical authority model was clarified: deterministic IAmina logic decides structured results; models may verbalize approved minimized output or perform explicitly permitted media tasks.
8. Diabetes remains the only live condition; MENA expansion does not authorize multi-disease expansion.

## What survived every architectural reversal

- Diabetes is the only live condition until evidence justifies expansion.
- Retention, especially D90, is the core product proof metric.
- Deterministic safety must precede generative AI.
- No diagnosis/prescription/treatment optimization without a separate explicit product/regulatory decision.
- SQL-first KPI authority remains where ADR-0007 applies.
- Offline sync idempotency remains critical.
- Architecture should preserve future optionality without letting optionality become the roadmap.

## What must not be inferred from old documents

Historical statements such as these are **not current strategy**:

- “Kimi is the target LLM.”
- “Morocco determines the product language architecture.”
- “Firebase is the permanent auth architecture.”
- “The chassis means a second condition should be built next.”
- “PHI stripping in one middleware proves all model egress is safe.”

Use `ARCHITECTURE.md` and `ROADMAP.md` for current truth.
