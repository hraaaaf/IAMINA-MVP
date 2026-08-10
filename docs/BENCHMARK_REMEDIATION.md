# IAmina — Competitive benchmark remediation track

> **Baseline date:** 2026-08-10  
> **Authority:** supporting evidence for the forward LOTs registered in `docs/ROADMAP.md`. The roadmap remains the single forward tracker.

## Why this track exists

A proof-only comparison against current diabetes leaders found that IAmina's largest remaining product gaps are not its deterministic diabetes core or its internally certified UX. The material gaps are ecosystem depth and real-world evidence: device/data connectivity, clinician workflows, caregiver sharing, interoperability, and a mature real-patient pilot.

This track must not weaken or bypass the existing MENA safety/compliance critical path. In particular, no benchmark LOT authorizes a first real patient before the existing pilot safety/compliance gate is fully closed.

## Scoring baseline

The benchmark uses 50 binary/evidence-backed criteria grouped into eight weighted domains totaling 100 points. Credit is granted only for a capability demonstrated in the current repository or in official current competitor documentation; planned or plausible capability receives no implementation credit.

| Domain | Weight | IAmina baseline | Primary gap |
|---|---:|---:|---|
| Clinical safety | 15 | 13 | external/field validation rather than architecture |
| Diabetes core + analytics | 18 | 16 | minor evidence/coverage gaps |
| Devices + imports + interoperability | 15 | 4 | broad normalized device/data ecosystem |
| Clinician + caregiver sharing | 12 | 4 | durable care-team workflows |
| MENA localization/context | 12 | 9 | remaining human safety-parity approvals |
| Privacy + sovereignty | 10 | 8 | external assurance / operational proof |
| UX + offline + engagement | 10 | 8 | real-world use evidence |
| Real-world validation/maturity | 8 | 2 | first cohort + D7/D30/D90 evidence |
| **Total** | **100** | **64** | ecosystem + field evidence |

The numeric baseline is a prioritization instrument, not a clinical score and not a claim of medical superiority.

## Remediation order

| LOT | Responsibility | Priority | Why it exists | Closure boundary |
|---|---|---|---|---|
| **P0-BENCH-1** | Pilot evidence & retention contract | P0 | Freeze trustworthy evidence semantics before collecting the first cohort | versioned, auditable D1/D7/D30/D90 rolling-retention contract; mature denominators; reproducible `as_of`; regression proof on SQLite/PostgreSQL; no invented success threshold |
| **P1-BENCH-2** | Device/Data Integration Foundation | P1 | Largest functional benchmark deficit | canonical provenance-aware ingestion contract and prioritized MENA device/source matrix before individual vendor integrations |
| **P1-BENCH-3** | IAmina Clinician Connect | P1 | Close patient-to-clinician workflow gap | explicit invitation/consent, time-bounded read access, clinical summary/report, revocation, auditability; no prescribing authority |
| **P1-BENCH-4** | Care Circle | P1 | Close caregiver/family sharing gap | granular patient-controlled sharing, revocation and alert/data scopes without silently exposing the full record |
| **P2-BENCH-5** | Standards interoperability | P2 | Make clinical data portable rather than platform-locked | evidence-backed FHIR/export mapping for the data actually supported by IAmina; no speculative EHR integration claims |
| **P2-BENCH-6** | External assurance & real-world evidence | P2 | Convert strong internal controls into externally credible evidence | completed pilot analysis, limitations, external security/privacy/quality evidence as applicable, and D90 decision package |

## P0-BENCH-1 — exact contract

### Problem reproduced on 2026-08-10

The pre-LOT retention implementation had two evidence defects:

1. D1 and D7 were marked ready whenever the cohort contained any patient, so patients younger than the measured horizon could enter the denominator as false non-retained outcomes. D30 and D90 already excluded immature patients, creating inconsistent semantics across horizons.
2. Retention and funnel queries used database current time and did not expose a common evidence cutoff. A later event could therefore alter a historical evidence snapshot, making the pilot result harder to reproduce exactly.

The existing implementation already behaved as **rolling retention** for mature patients: a return on or after the horizon counted. P0-BENCH-1 preserves that behavior and names it explicitly instead of inventing a different exact-day/window definition.

### Acceptance criteria

- [ ] D1, D7, D30 and D90 use the same maturity rule: only patients whose acquisition age has reached the horizon enter that horizon denominator.
- [ ] Each horizon exposes its eligible denominator separately from total cohort size.
- [ ] `cohort_ready_dN` is true if and only if the corresponding eligible denominator is greater than zero.
- [ ] The contract explicitly identifies retention as rolling return on/after the horizon, bounded by the evidence cutoff.
- [ ] One timezone-aware `as_of` timestamp bounds acquisition, return, funnel and engagement evidence; events after `as_of` cannot alter the snapshot.
- [ ] The result exposes contract version, semantics, `as_of` and computation timestamp for auditability.
- [ ] Naive/unbounded evidence timestamps fail closed.
- [ ] Permanent tests cover immature D1/D7, mixed-age denominators, rolling D7 semantics, future-event exclusion, future-acquisition exclusion and immutable output.
- [ ] SQLite and authoritative PostgreSQL behavior pass repository CI; migration drift remains green.
- [ ] No schema migration, patient-facing clinical logic, treatment behavior, diagnosis/prescription behavior or generative authority is introduced.
- [ ] No D7/D30/D90 success threshold is invented in code or docs. The future go/no-go threshold requires an explicit founder/pilot protocol decision before outcome interpretation.

### Explicit non-scope

- enrolling a real patient;
- declaring the existing 13-item Pilot safety/compliance gate closed;
- choosing a target D90 percentage without an approved protocol;
- adding device integrations, clinician access, caregiver sharing or FHIR in this LOT;
- turning retention into a patient-facing or clinical metric.

## Sequencing rule

P0-BENCH-1 may be implemented before the external safety/compliance blockers are cleared because it changes only evidence computation. **Real-patient cohort execution remains blocked by the existing Pilot safety/compliance gate.** Once P0-BENCH-1 is certified, the benchmark track advances to P1-BENCH-2 unless the canonical MENA critical path requires a higher-priority safety action.

## Benchmark evidence sources

Competitor capabilities were checked against official product documentation available on the baseline date, including Glooko device/interoperability documentation, Dexcom Clarity/Follow documentation, Abbott FreeStyle Libre/LibreLinkUp/LibreView documentation, and Roche mySugr product documentation. Competitor claims are context for prioritization only; they are not imported into IAmina's safety or clinical contracts.
