# IAmina — Module Contract Specification

> **Status:** CURRENT CONTRACT INTENT  
> **Decision origin:** ADR-0008  
> **Code is authoritative for exact signatures/fields.** This document describes the durable boundaries agents must preserve.

## Purpose

IAmina has real chassis/module seams, but only **one live condition: diabetes**.

The contract exists to:

- keep shared core concerns separate from diabetes-specific logic;
- prevent accidental cross-module coupling;
- preserve future optionality without making multi-condition expansion a current roadmap goal;
- ensure every interactive module path participates in shared safety, auth/account, and observability rules.

Do not use this spec as justification to build a second module before the Retention Gate passes.

## 1. Module manifest

Each condition module exposes a manifest/registration contract used by the chassis for concerns such as:

- module identity/name/version;
- static URL prefix/routing metadata;
- supported capabilities/languages where represented;
- interactive endpoints that require deterministic safety registration;
- observability/acquisition metadata where applicable.

Rules:

- route prefixes are static configuration, not dynamic path-parameter tricks;
- interactive endpoints must not bypass safety registration;
- a manifest is configuration, not a place to embed secrets or patient data;
- supported-language metadata does **not** by itself authorize a locale for real-patient use — MENA locale gates live in `docs/ROADMAP.md`.

## 2. Patient context boundary

A module should receive only the patient context it actually needs, through shared contracts rather than unrestricted cross-domain ORM access.

Durable principles:

- prefer stable IDs and explicit context fields over passing privileged ORM objects across boundaries;
- never include auth tokens or unnecessary identity fields;
- locale data must evolve beyond a single language string as P0-MENA-2 is implemented;
- consent must be explicit and purpose-aware;
- country/location must not silently determine language, dialect, consent, or emergency behavior.

The exact current dataclass/model fields are defined by code and may evolve during the MENA locale/auth reset.

## 3. Domain analysis output

A condition module returns structured domain output to shared companion/presentation layers.

That structured output should separate:

- deterministic KPI/metric data;
- deterministic detected patterns;
- data sufficiency/confidence;
- safe structured insights/context;
- locale/presentation metadata where required.

Rules:

- values must be serializable through the intended API/presentation boundary;
- numeric/clinical truth comes from deterministic domain logic, not model prose;
- sensitive/unnecessary identity data must not be inserted into narrative context;
- structured output must remain usable when all external AI providers are unavailable.

## 4. Engine contract

The shared engine abstraction exists so the chassis/companion layer can request domain analysis without importing diabetes implementation details.

Durable rules:

- the module fetches/owns its own domain data;
- shared core does not calculate diabetes-specific clinical metrics merely for convenience;
- domain analysis is deterministic;
- external LLM/provider calls are not part of the clinical authority contract;
- provider/media narration must go through the sanctioned outbound policy boundary as P0-MENA-1 is completed.

Do not copy old pre-refactor method signatures from historical docs. Verify the current abstract base class and implementation before changing callers.

## 5. Companion identity / presentation identity

Companion branding/persona metadata is distinct from clinical/domain analysis output.

Keep separate concepts for:

- who/what the companion presents itself as;
- what the domain engine determined;
- how a model may verbalize approved structured context.

Do not merge persona metadata into clinical truth structures.

## 6. AI / narrative boundary

Historical chassis work introduced a shared narrative gateway concept. The 2026-07 MENA reset strengthens the requirement:

> All external text/STT/vision/document calls must ultimately pass one enforceable outbound policy boundary.

Therefore:

- modules must not invent direct provider integrations;
- a shared narrative helper is not enough if alternate call paths bypass policy;
- consent, minimization, redaction, retention, processor metadata, timeout, and failure policy belong at the enforceable outbound boundary;
- models may verbalize approved structured outputs but do not decide diagnosis, prescription, treatment changes, or emergency authority.

Until P0-MENA-1 is complete, do not claim that every legacy call path already satisfies this architecture.

## 7. Safety registration

Every interactive endpoint capable of receiving patient health/safety-relevant free text or equivalent interpreted input must participate in deterministic safety handling before generative processing.

Rules:

- registration is explicit;
- adding a route requires tests proving the route is protected;
- new modalities must not create hidden bypasses;
- locale/dialect expansion requires native safety parity before pilot enablement.

## 8. Account deletion / lifecycle hooks

Modules that own patient data must participate in the shared account lifecycle and deletion process.

Rules:

- domain cleanup is explicit and auditable;
- failures must not silently create partial deletion while reporting success;
- migration from Firebase to Django-native auth must preserve deletion/export semantics;
- observability/retention data lifecycle must be included, not treated as unrelated telemetry.

## 9. Module isolation

Desired dependency direction:

```text
shared core/contracts
        ↓
diabetes module
        ↓
registered API/domain adapters
```

Avoid:

- shared core importing diabetes internals as an easy shortcut;
- cross-module foreign-key coupling without an explicit architecture decision;
- duplicated auth/safety/provider infrastructure inside modules;
- multi-condition abstractions with no current product use.

Use import-lint/static checks where available to enforce durable boundaries.

## 10. Locale implications for module contracts

The old model of `supported_languages = [fr, ar-MA, en]` is too coarse to represent the target MENA rollout contract by itself.

Future-safe module/core contracts must allow the product to distinguish:

- country/region;
- UI language;
- response language;
- dialect;
- script/transliteration preference;
- units;
- time zone;
- emergency jurisdiction;
- locale enablement/safety status.

This does not mean all fields must live in `ModuleManifest`; place them in the appropriate shared locale/account/config contracts.

## 11. Expansion gate

A second condition module is **GATED**.

Do not implement or activate a new disease module until the Retention Gate in `docs/ROADMAP.md` passes:

1. D90 retention meets the founder-set threshold.
2. A credible payer/distribution signal exists.

Architecture optionality is not product validation.

## 12. Change protocol

When changing a durable module/chassis contract:

1. Inspect the actual current code and import boundaries.
2. Check ADR-0008 and any superseding ADR.
3. Update focused tests first/alongside implementation.
4. Update this spec only for durable contract changes.
5. Update `ARCHITECTURE.md` if system boundaries changed.
6. Add a new/superseding ADR for decision-level changes; never rewrite old ADR history.

Do not add phase status, test counts, session notes, or provider-shopping decisions to this file.
