# P0.4 — Legacy Memory Truth Migration

> **Scope:** IAmina companion-memory persistence/provenance only.  
> **Non-scope:** no patient-facing UX, diagnosis, prescription, treatment optimization, clinical threshold/formula, Django model or database schema change.  
> **Closure rule:** P0.4 includes the P0.4.1 heuristic-quarantine correction; final closure still requires exact-head reviews/gates, expected-head merge and post-merge CI + drift.

## Problem

The legacy `IAminaMemory` and `IAminaDeepMemory` snapshots predate the executable truth contract. They persist flat JSON dictionaries that mix deterministic derivatives, relationship/tone state and historical heuristic memory. Two generative paths could also mutate public memory fields before the next save boundary:

- chat `concern_detected` → `last_concern` / `emotional_signals`;
- reactor `tone_detected` → `current_tone`.

Because the old snapshot has no field provenance, a later load cannot prove whether an emotional/tone value came from deterministic keyword handling or model output.

A separate legacy food-response heuristic stored `food_sensitivities` from a single-reading/approximate-baseline rule. That value is not an approved deterministic clinical derivation and must not gain clinical authority merely because it remains readable for compatibility.

## P0.4 contract

### 1. Versioned companion snapshot

Both memory namespaces continue to use the existing `SnapshotStore` and existing Django `JSONField`. New writes use the explicit v3 envelope:

```text
schema: iamina.companion-memory
schema_version: 3
kind: memory | deep
values: {...}
provenance:
  field:
    kind: <TruthKind>
    source: <stable non-PHI source id>
```

No Django model or database migration is required.

### 2. Backward-compatible read

The codec accepts legacy flat snapshots and P0.4 v2 envelopes. Known compatible values remain readable. The caller-selected `patient_id` is always authoritative and cannot be overridden by the stored payload.

Unknown schema versions, wrong namespace/kind, malformed envelopes or provenance mismatches fail closed to field/default state.

### 3. Unprovable legacy emotion is quarantined

For a legacy flat `memory` payload, these fields reset to neutral defaults on load:

- `last_concern`;
- `current_tone`;
- `emotional_signals`.

Their legacy origin cannot distinguish deterministic keyword state from generative output. New deterministic keyword-derived conversation state remains persistable as `CONVERSATIONAL_STATE` with source `companion.keyword_emotion`.

### 4. Model output cannot survive the durable memory boundary

`IAminaMemory` keeps provenance-approved runtime copies of the sensitive conversation fields. `save()` serializes only those approved copies and then restores them into the live object.

Direct assignments that mimic legacy model-output paths therefore cannot become durable memory merely because another code path later calls `save()`.

### 5. Legacy food-response heuristic is quarantine-only

`HEURISTIC_INFERENCE` is a distinct truth class. It is neither a patient fact nor an allowed deterministic clinical input.

Historical `food_sensitivities` from flat snapshots or P0.4 v2 envelopes are migrated into `quarantined_heuristics.food_sensitivities`. The active `food_sensitivities` field is cleared on decode and encode boundaries.

The compatibility method `learn_food_sensitivity()` may remain temporarily callable, but it writes only into quarantine. A direct assignment to active `food_sensitivities` is also moved to quarantine on `save()` and removed from the live active field.

The active authority paths stay disabled:

- `IAmina.on_log()` does not feed the legacy heuristic;
- `compute_state()` does not derive a meal-related `next_intention` from it;
- quarantine data cannot enter deterministic clinical logic through the truth contract.

This preserves historical bytes for audit/backward compatibility without representing the heuristic as an approved clinical pattern.

## Executable evidence

`backend/diabetes/tests/test_memory_truth_migration.py` and companion regression tests prove:

- v3 schema/version/provenance;
- typed field provenance through `TruthKind`;
- v3 round-trip behavior for approved fields;
- P0.4 v2 → v3 food-heuristic migration;
- legacy flat → v3 food-heuristic migration;
- provenance tamper fail-closed behavior;
- unknown-version fail-closed behavior;
- patient identity cannot be overridden by a snapshot;
- legacy emotion/tone quarantine while compatible legacy data remains readable;
- direct model-like memory mutations do not persist;
- deterministic keyword emotion does persist with explicit provenance;
- `HEURISTIC_INFERENCE` cannot persist as patient fact or enter deterministic clinical logic;
- the legacy learning API and direct active mutations end in quarantine only;
- historical food heuristic data does not drive `next_intention`;
- active `on_log()` does not feed the legacy food heuristic.

## Acceptance gates

P0.4 is not CLOSED until all are true on one exact final head:

1. CI SUCCESS, including backend, PostgreSQL source-of-truth, Flutter, Ruff, import-linter, security and permanent contracts.
2. Django migration drift SUCCESS; expected result is no migration.
3. Clinical/Safety Reviewer PASS on the exact head.
4. Database & Migration Reviewer PASS on the exact head.
5. Release Certifier GO on the exact head.
6. Expected-head locked merge.
7. Post-merge CI SUCCESS and migration drift SUCCESS on the merge commit.
