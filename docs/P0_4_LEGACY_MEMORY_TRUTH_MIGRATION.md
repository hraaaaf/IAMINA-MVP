# P0.4 — Legacy Memory Truth Migration

> **Status:** ✅ CLOSED 100% — PR #114 merged as `ebfd77f036f10188888b7bc52d754a01cf11973b`; exact-head CI #1649 + drift #1461 and post-merge CI #1650 + drift #1462 are green.  
> **Scope:** IAmina companion-memory persistence/provenance only.  
> **Non-scope:** no patient-facing UX, diagnosis, prescription, treatment optimization, clinical threshold/formula, Django model or database schema change.

## Problem

The legacy `IAminaMemory` and `IAminaDeepMemory` snapshots predate the executable truth contract. They persist flat JSON dictionaries that mix deterministic derivatives, relationship/tone state and historical heuristic memory. Two generative paths could also mutate public memory fields before the next save boundary:

- chat `concern_detected` → `last_concern` / `emotional_signals`;
- reactor `tone_detected` → `current_tone`.

Because the old snapshot has no field provenance, a later load cannot prove whether an emotional/tone value came from deterministic keyword handling or model output.

A separate legacy food-response heuristic also stored `food_sensitivities` and could steer `next_intention` toward a meal observation despite lacking the evidence/provenance required for durable patient-facing reasoning.

## P0.4 contract

### 1. Versioned companion snapshot

Both memory namespaces continue to use the existing `SnapshotStore` and existing Django `JSONField`. The JSON payload becomes an explicit v2 envelope:

```text
schema: iamina.companion-memory
schema_version: 2
kind: memory | deep
values: {...}
provenance:
  field:
    kind: <TruthKind>
    source: <stable non-PHI source id>
```

No Django model or database migration is required.

### 2. Backward-compatible read

The codec accepts legacy flat snapshots. Known compatible values remain readable. The caller-selected `patient_id` is always authoritative and cannot be overridden by the stored payload.

Unknown schema versions, wrong namespace/kind, malformed envelopes or provenance mismatches fail closed to field/default state.

### 3. Unprovable legacy emotion is quarantined

For a legacy flat `memory` payload, these fields reset to neutral defaults on load:

- `last_concern`;
- `current_tone`;
- `emotional_signals`.

This is intentional. Their legacy origin cannot distinguish deterministic keyword state from generative output, so preserving them would promote unknown provenance into the new trusted snapshot.

New deterministic keyword-derived conversation state remains persistable as `CONVERSATIONAL_STATE` with source `companion.keyword_emotion`.

### 4. Model output cannot survive the durable memory boundary

`IAminaMemory` keeps provenance-approved runtime copies of the sensitive conversation fields. `save()` serializes only those approved copies and then restores them into the live object.

Direct assignments that mimic legacy model-output paths therefore cannot become durable memory merely because another code path later calls `save()`.

### 5. Legacy food-response heuristic is quarantined

Historical `food_sensitivities` remain decodable so an old snapshot is not structurally corrupted, but P0.4 removes both active authority paths:

- `IAmina.on_log()` no longer feeds `_learn_from_entry()`;
- `compute_state()` no longer derives a meal-related `next_intention` from `food_sensitivities`.

The compatibility helper/method remains temporarily present so this focused lot does not combine truth migration with a breaking API deletion. Historical values are not patient facts and do not drive the prompt.

## Executable evidence

`backend/diabetes/tests/test_memory_truth_migration.py` proves:

- v2 schema/version/provenance;
- typed field provenance through the existing `TruthKind` contract;
- v2 round-trip behavior;
- provenance tamper fail-closed behavior;
- unknown-version fail-closed behavior;
- patient identity cannot be overridden by a snapshot;
- legacy emotion/tone quarantine while compatible legacy data remains readable;
- direct model-like memory mutations do not persist;
- deterministic keyword emotion does persist with explicit provenance;
- historical food heuristic data does not drive `next_intention`;
- active `on_log()` no longer feeds the legacy food heuristic.

The pre-existing state and Sprint-2 persistence contracts were migrated so they permanently reject meal-intention steering from `food_sensitivities` and assert the v2 snapshot envelope instead of the retired flat format.

## Closure evidence

All P0.4 acceptance gates are satisfied:

1. Exact implementation head `f484ccb6018492873fa711cc72bb2e052eda69cb` — CI #1649 SUCCESS.
2. Exact implementation head — Django migration drift #1461 SUCCESS; no migration required.
3. Clinical/Safety Reviewer PASS anchored to the exact implementation head.
4. Release Certifier GO anchored to the same exact implementation head.
5. PR #114 merged with expected-head locking as `ebfd77f036f10188888b7bc52d754a01cf11973b`.
6. Post-merge `main@ebfd77f036f10188888b7bc52d754a01cf11973b` — CI #1650 SUCCESS and migration drift #1462 SUCCESS.

**P0.4 is CLOSED 100%.**
