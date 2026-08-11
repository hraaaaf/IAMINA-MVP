# P0.4 — Legacy Memory Truth Migration

> **Status:** ✅ CLOSED 100% — P0.4 PR #114 + corrective P0.4.1 PR #117 are merged and fully post-merge certified.  
> **Scope:** IAmina companion-memory persistence/provenance only.  
> **Non-scope:** no patient-facing UX, diagnosis, prescription, treatment optimization, clinical threshold/formula, Django model or database schema change.  

## Problem

The legacy `IAminaMemory` and `IAminaDeepMemory` snapshots predate the executable truth contract. They persist flat JSON dictionaries that mix deterministic derivatives, relationship/tone state and historical heuristic memory. Two generative paths could also mutate public memory fields before the next save boundary:

- chat `concern_detected` → `last_concern` / `emotional_signals`;
- reactor `tone_detected` → `current_tone`.

Because the old snapshot has no field provenance, a later load cannot prove whether an emotional/tone value came from deterministic keyword handling or model output.

Legacy `food_sensitivities` came from a single-reading/approximate-baseline food-response heuristic, while legacy `peak_hours` is likewise compatibility-era heuristic state without an approved clinical derivation contract. Neither field may gain deterministic clinical authority merely because it remains readable for compatibility.

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

### 5. Legacy heuristics remain non-clinical

`HEURISTIC_INFERENCE` is a distinct truth class. It is neither a patient fact nor an allowed deterministic clinical input.

Historical `food_sensitivities` from flat snapshots or P0.4 v2 envelopes are migrated into `quarantined_heuristics.food_sensitivities`. The active `food_sensitivities` field is cleared on decode and encode boundaries.

The compatibility method `learn_food_sensitivity()` may remain temporarily callable, but it writes only into quarantine. A direct assignment to active `food_sensitivities` is also moved to quarantine on `save()` and removed from the live active field.

The active authority paths stay disabled:

- `IAmina.on_log()` does not feed the legacy food heuristic;
- `compute_state()` does not derive a meal-related `next_intention` from it;
- quarantine data cannot enter deterministic clinical logic through the truth contract.

Legacy `peak_hours` remains structurally readable for compatibility but is labelled `HEURISTIC_INFERENCE` in v3. The exact v2 marker that briefly labelled it `DETERMINISTIC_DERIVATION` is accepted only as a migration input; a subsequent v3 encode/save writes corrected heuristic provenance. Arbitrary mismatched provenance still fails closed.

This preserves historical bytes for audit/backward compatibility without representing either heuristic as an approved clinical pattern or clinical decision input.

## Executable evidence

`backend/diabetes/tests/test_memory_truth_migration.py`, `backend/core/tests/test_p0_4_peak_hours_provenance.py` and companion regression tests prove:

- v3 schema/version/provenance;
- typed field provenance through `TruthKind`;
- v3 round-trip behavior for approved fields;
- P0.4 v2 → v3 food-heuristic migration;
- legacy flat → v3 food-heuristic migration;
- v2 → v3 `peak_hours` compatibility with corrected `HEURISTIC_INFERENCE` provenance;
- provenance tamper fail-closed behavior;
- unknown-version fail-closed behavior;
- patient identity cannot be overridden by a snapshot;
- legacy emotion/tone quarantine while compatible legacy data remains readable;
- direct model-like memory mutations do not persist;
- deterministic keyword emotion does persist with explicit provenance;
- `HEURISTIC_INFERENCE` cannot persist as patient fact or enter deterministic clinical logic;
- the legacy food learning API and direct active mutations end in quarantine only;
- historical food heuristic data does not drive `next_intention`;
- active `on_log()` does not feed the legacy food heuristic;
- historical `peak_hours` never receives approved deterministic clinical authority.

## Closure evidence

All acceptance gates are satisfied across the implementation lot and its corrective lot:

### P0.4 — PR #114

1. Exact implementation head `f484ccb6018492873fa711cc72bb2e052eda69cb` — CI #1649 SUCCESS.
2. Exact implementation head — Django migration drift #1461 SUCCESS; no migration required.
3. Clinical/Safety Reviewer PASS and Release Certifier GO anchored to the exact implementation head.
4. PR #114 merged with expected-head locking as `ebfd77f036f10188888b7bc52d754a01cf11973b`.
5. Post-merge `main@ebfd77f036f10188888b7bc52d754a01cf11973b` — CI #1650 SUCCESS and migration drift #1462 SUCCESS.

### P0.4.1 — PR #117 corrective quarantine

1. Exact corrective head `d2269a92416f412e9f8629f508137a918ca8cf77` — CI #1676 SUCCESS.
2. Exact corrective head — Django migration drift #1488 SUCCESS; no migration required.
3. Clinical Safety Reviewer PASS, Database & Migration Reviewer PASS and Release Certifier GO anchored to the same exact corrective head; zero review threads.
4. PR #117 merged as `23eab9eafa9e25661ae71763a5266c48f9e2a437`.
5. Post-merge `main@23eab9eafa9e25661ae71763a5266c48f9e2a437` — CI #1677 SUCCESS and migration drift #1489 SUCCESS.

**P0.4 / P0.4.1 is CLOSED 100%.**
