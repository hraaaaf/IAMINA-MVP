# P0.4 — IAmina Legacy Memory Truth Migration

> **Scope:** make legacy `memory` / `deep` JSON snapshots backward-compatible with the P0.2 truth contract and retire the single-entry food-sensitivity heuristic from active reasoning.  
> **Non-scope:** no database schema migration, clinical threshold/formula change, new patient-facing feature, provider change, or second disease module.  
> **Closure rule:** exact-head specialist reviews + CI/drift, expected-head merge, then post-merge CI + drift on `main`.

## Acceptance contract

P0.4 is complete only when:

- unversioned legacy memory/deep snapshots still load without requiring a database migration;
- canonical truth classification is owned by code and cannot be overridden by snapshot-supplied metadata;
- legacy unknown fields are preserved outside active reasoning rather than silently discarded;
- `last_concern` remains an explicit `USER_CLAIM`; cached/dialogue/relationship state remains non-clinical `CONVERSATIONAL_STATE`;
- historical `food_sensitivities` is classified as `HEURISTIC_INFERENCE`, retained only in quarantine, and cannot enter deterministic clinical logic or patient-fact persistence;
- new log events no longer learn the old single-reading / approximate-baseline food heuristic;
- quarantined food heuristics cannot select `next_intention` or otherwise steer active companion reasoning;
- existing streak, relationship, emotion, milestone and cached-state behavior remains backward compatible;
- no Django model/migration change is introduced; migration drift stays green;
- Clinical Safety Reviewer + Database & Migration Reviewer + Release Certifier pass on the same exact head;
- post-merge CI and migration drift pass on `main` before the LOT is declared CLOSED 100%.
