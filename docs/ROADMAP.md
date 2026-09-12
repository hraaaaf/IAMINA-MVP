# IAmina — Canonical Roadmap

> **Authority:** this is the single canonical forward tracker for IAMINA. If an issue, PR body, handover, assessment, AGENTS note, architecture note or historical phase document conflicts with this file on current status, priority or next work, **this file wins**. Historical documents remain evidence only.
>
> **Global audit:** 2026-09-12, re-bound after PR #591 against frozen candidate `main@fd3e4a53543e515100b493acc63c99cc9e8464ce`, open GitHub trackers, `AGENTS.md` and `docs/TECHDEBT.md`.
>
> **Release posture:** `NOT_RELEASE_AUTHORIZED`. No Vercel deployment is authorized by this roadmap.

## North star

Ship one safe, measurable Morocco/MENA diabetes-companion PWA pilot, collect real evidence, then make an explicit go/no-go decision before broader rollout or a second disease capsule.

## Non-negotiable product boundaries

- Diabetes is the only live condition.
- IAMINA is a patient companion, not a physician replacement.
- Deterministic clinical/safety logic is authoritative; generative models may only narrate approved bounded output.
- No diagnosis, prescription, dose calculation, treatment optimization/change or autonomous medical instruction.
- Language/dialect enablement requires explicit safety parity; location never silently determines language or emergency jurisdiction.
- Pilot delivery is **PWA-first**. Native Android/iOS is deferred unless explicitly activated.
- Engineering proof, human approval, legal/CNDP approval and real-patient authorization are separate gates.

---

# 1. Executive status

| Area | Canonical status | Forward consequence |
|---|---|---|
| Gate A Secure Core | ✅ CLOSED / certified 10.0/10 | maintenance only |
| Historical P0 foundations / product truthfulness / agent governance | ✅ CLOSED | no reopening without new defect/evidence |
| Global UX / Dashboard / Journal | ✅ CLOSED | regressions only; new UX work must be a new scoped lot |
| Clinical Data Layer & Privacy foundation | ✅ MERGED | residual privacy debt remains under TD-001 |
| Companion intelligence / proactive lifecycle | ✅ CLOSED through current convergence | issue hygiene may remain, but no active forward feature lot |
| CGM gateway V1 / V1.1 / V2 / V2.1 | ✅ CLOSED | real physical-sensor evidence remains external if later claimed |
| P4-FRUGAL PRE-PILOT | ✅ CLOSED 10/10 | real pilot economics belong to P5-7 |
| MENA retained tracker | 🟡 32/38 = 84.2% retained | do not use as release authorization |
| P5 Pilot Readiness | 🟡 4/9 = 44.4% | active program |
| P5-6 consent evidence engineering | ✅ MERGED / REFROZEN | candidate `fd3e4a5…`; external evidence still blocks release |
| Real-patient release | 🟠 BLOCKED_EXTERNAL | current critical path |

---

# 2. One critical path

There is only one current release-critical sequence:

**P5-6 restricted safety/compliance evidence → three exact-SHA approved audits → explicit human release decision → controlled PWA pilot → P5-7 observed evidence → P5-8 go/no-go.**

Everything else is either closed, deferred, parallel non-blocking work, technical debt, or repository hygiene.

---

# 3. P5 Pilot Readiness

## P5-0 — Security reconciliation

**Status:** ✅ CLOSED.

Legacy security bookkeeping was reconciled with the reachable-history certification. Do not reopen absent new evidence.

## P5-1 — Morocco linguistic certification

**Status:** ✅ CLOSED / HUMAN_APPROVED / retained exact-main evidence.

Verified retained evidence:
- PR #579 merged;
- exact-main evidence SHA `2d18428a0c59a18c82a1c0dfb410469f17f81e04`;
- post-merge CI #34682380854 SUCCESS;
- migration #34682380897 SUCCESS;
- packet #34683056185 SUCCESS;
- artifact #10295285314;
- human approval recorded in closed issue #515.

## P5-2 — Arabic OCR real-world evidence

**Status:** ✅ CLOSED with negative qualification result.

Real-camera Tesseract `ara` evidence failed the required quality floor. No local Arabic full-document primary is qualified. This is a valid closed result, not an unfinished engineering task.

## P5-3 — Native TTS real-device evidence

**Status:** 🟡 DEFERRED / HUMAN_DEVICE_GATE.

Issue: #518.

Required only before a native Android/iOS pilot, public native distribution, or an explicit native-TTS adequacy claim. It **does not block the current PWA pilot**.

## P5-4 — Pilot packaging

**Status:** 🟡 SPLIT.

### P5-4A — PWA packaging engineering

**Status:** ✅ CLOSED_WITH_BOUNDARIES.

Verified engineering evidence includes persistence, strict offline reopen, release discovery, rejected-candidate last-known-good preservation, healthy update activation, correct new bundle bytes and no origin-storage clearing. Closeout is retained in the repository.

External boundaries still not claimed by P5-4A: controlled pilot URL, physical target-browser installation, production deployment and real-patient authorization.

### P5-4B — Native Android/iOS alignment

**Status:** 🟡 DEFERRED.

Future native-only work:
- Android permanent signing identity/artifacts;
- Apple signing/provisioning/distribution;
- physical native-device clean install/update/recovery evidence.

Not blocking PWA-first pilot.

## P5-5 — End-to-end pilot rehearsal

**Status:** ✅ CLOSED / `PASS_WITH_BOUNDARIES`.

Verified retained evidence:
- main `88b78e036ce3494dfe37921e70e064fbfdabd6bb`;
- rehearsal #34573137446 SUCCESS;
- CI #34573137452 SUCCESS;
- artifact #10188573954.

Synthetic/non-patient engineering proof only. Physical-device, live-sensor, production-signing and real-patient claims remain external.

## P5-6 — Real-patient release gate

**Status:** 🟠 ACTIVE / BLOCKED_EXTERNAL / HIGHEST PRIORITY.

Frozen candidate:
- release SHA: `fd3e4a53543e515100b493acc63c99cc9e8464ce`;
- safety corpus: 59 exact cases;
- parity coverage: 10 technical tuples;
- safety fingerprint: `823d109b0ddd10d1874eec53027eafd9d65884f14810304af3681c57c82cf7e5`;
- consent notice version: `2026-09-12.1`;
- PR #591 exact head `b018f724aeaa7b34217cd2810c35e95881332ee1`;
- exact-head CI #4145 / workflow `34708902735` SUCCESS;
- exact-head migration drift #3719 / workflow `34708902710` SUCCESS;
- merge `main@fd3e4a53543e515100b493acc63c99cc9e8464ce`, GitHub signature verified/valid;
- post-merge CI #4148 / workflow `34709544750` SUCCESS;
- post-merge migration drift #3722 / workflow `34709544765` SUCCESS.

PR #591 changed runtime consent/release behavior, so candidate `a25ec4dd1118784c8968588bab035dca4d0f71b6` is explicitly superseded. Its 32-file diff did not modify the safety corpus, so the 59-case/10-tuple fingerprint is retained unchanged.

### P5-6 consent evidence engineering

**Status:** ✅ MERGED / GREEN / CANDIDATE_REFROZEN.

Verified behavior now includes:
- exact notice version/hash/locale evidence;
- legacy timestamp-only consent invalidation and re-consent;
- server acceptance receipts;
- withdrawal clearing active proof and granular media grants;
- central outbound-AI egress verification of current notice evidence;
- media grant epoch isolation;
- Flutter fail-closed when server acceptance fails;
- local UI gate requiring Drift timestamp + verified Secure Storage evidence;
- local-only release scope still retaining global CNDP health-processing blockers.

This closes the consent-evidence **engineering sublot only**. It does not close P5-6 or authorize real-patient processing.

### P5-6A — Safety qualification manifest

**Tracker:** #318.

Already verified:
- qualified-human review is owner-attested;
- challenged Darija runtime rows were adjudicated;
- runtime cutover merged;
- safety owner/parity approval is attested;
- exact safety corpus remained unchanged by #591.

Still missing:
- real restricted qualification/evidence references;
- real locale-review qualification references for required locales;
- approved safety manifest bound to `fd3e4a53543e515100b493acc63c99cc9e8464ce` and the exact fingerprint/full 59-case/10-tuple coverage.

### P5-6B — CNDP / consent / processor / residency

**Tracker:** #320.

Still missing for the actual pilot deployment:
- exact runtime/database/cache/email/export/provider topology and countries/regions;
- approved deployment-specific patient notice and consent;
- applicable CNDP health-data processing evidence;
- foreign-transfer basis/evidence for every actual destination;
- account-specific processor/DPA/subprocessor/retention/deletion/no-training/privacy/security evidence;
- restricted residency manifest bound to `fd3e4a53543e515100b493acc63c99cc9e8464ce`.

### P5-6 success proof

All three fail-closed audits must PASS against the same approved candidate SHA:

```bash
python manage.py audit_pilot_consent_governance --require-approved --expected-source-commit-sha fd3e4a53543e515100b493acc63c99cc9e8464ce
python manage.py audit_pilot_data_residency --manifest /restricted/iamina/pilot-residency.json --require-approved --expected-source-commit-sha fd3e4a53543e515100b493acc63c99cc9e8464ce
python manage.py audit_safety_corpus_review --manifest /restricted/iamina/safety-review-manifest.json --require-approved --expected-source-commit-sha fd3e4a53543e515100b493acc63c99cc9e8464ce
```

Then and only then: explicit human release decision.

## P5-7 — Observed pilot evidence

**Status:** ⚪ PENDING P5-6.

Collect real, clearly labelled pilot evidence:
- MAU/activation/retention;
- safety incidents and escalation behavior;
- reliability/offline/update failures;
- LLM route/cost and zero-model rate;
- storage/egress cost;
- satisfaction and support burden;
- product engagement and clinically safe usefulness signals.

Synthetic evidence cannot be promoted to P5-7 proof.

## P5-8 — Go / No-Go

**Status:** ⚪ PENDING P5-7.

Decision gate on continued investment/expansion. No second disease capsule before this gate passes.

**Pilot Readiness:** **4/9 = 44.4%**. Closed whole lots: P5-0, P5-1, P5-2, P5-5.

---

# 4. MENA / multimodal residuals

## P0-MENA-2 — Locale + safety contract

**Status:** 🟡 PARTIALLY OPEN only through P5-6A restricted qualification evidence.

Do not run a separate parallel chantier for this. Its remaining release-relevant work is absorbed into #318/P5-6A.

## P0-MENA-4 — Multimodal provider benchmark

**Status:** 🟡 DEFERRED / EXTERNAL-HUMAN EVIDENCE, issue #319.

Current retained conclusions:
- Groq + `openai/gpt-oss-120b` remains the conversational candidate;
- no local Arabic full-document OCR primary qualifies under the current strict floor;
- native TTS real-device evidence is deferred to P5-3;
- STT remains deferred by owner decision.

This is **not** on the current PWA pilot critical path unless a specific modality is reintroduced into pilot scope.

**Retained MENA metric:** 32/38 = 84.2%. This historical/rebased metric is informational and must not be treated as a release gate.

---

# 5. Parallel engineering debt

These are real unresolved compromises from `docs/TECHDEBT.md`, but they are **not automatically allowed to pre-empt P5-6**.

| Debt | Priority | Canonical disposition |
|---|---|---|
| TD-001 free-form/raw-media de-identification not universal | Critical if external unstructured patient documents are enabled | keep patient-document cloud OCR fail-closed; qualify local OCR/de-ID before widening |
| TD-002 Firebase legacy auth | Critical target architecture | reconcile against actual current runtime before starting a migration lot; previous roadmap says P0-MENA-3 merged, so this debt text may be stale |
| TD-003 provider timeout/circuit-breaker/failure UX | High before relevant pilot exposure | audit current outbound boundary; open focused lot only for reproduced gaps |
| TD-004 stale CI/SAST exclusions | Medium-high | verify and remove only reproduced stale paths |
| TD-005 coarse locale/safety model | Critical historically | largely superseded by P5-1/P5-6; reconcile/remove stale remainder |
| TD-006 safety orthographic variants | Critical historically | reconcile against current 59-case reviewed corpus before any new work |
| TD-007 monitored emergency operational routing | Critical before pilot if operational routing is claimed/required | must be explicitly resolved or dispositioned inside P5-6 operating model |
| TD-008 frontend integration/accessibility | Medium/high before broader release | parallel quality lot after release blockers unless pilot-critical defect reproduced |
| TD-009 privileged-role MFA | High before staff/professional scale | deferred unless pilot includes privileged staff surface |
| TD-010 observability retention lifecycle | High before broader production | include in P5-6B if pilot observability stores patient-linked data; otherwise later |
| TD-011 stale demo seed data | Low-medium | post-critical-path maintenance |
| TD-012 large Flutter surfaces/silent catches | Medium | opportunistic focused refactors after pilot-critical work |

**Required cleanup:** `docs/TECHDEBT.md` must later be reconciled so resolved/superseded items do not masquerade as active debt.

---

# 6. CI / cost optimization

## CI-FRUGAL-2 — Chrome certification runner time

**Status:** 🟢 PARALLEL / NON-BLOCKING, issue #442.

Goal: reduce runner time without reducing the 42 real-Chrome visual proofs. This may proceed only if it does not delay P5-6 or weaken visual certification.

---

# 7. Repository hygiene audit

Open GitHub items are **not** automatically active roadmap work.

The 2026-09-12 audit found open items that are clearly historical, superseded, evidence-only or inconsistent with current roadmap state. They must be reconciled separately, not counted as active chantiers:

- old Companion certification result issues (#333, #334, #353, #356, #357): evidence records, not forward work;
- old OCR benchmark result issues (#372, #385, #386): evidence records, not forward work;
- #137 P2-PROACTIVE: roadmap says current Companion/proactivity convergence is closed; verify merge/evidence then close or rewrite as a new defect;
- #125 UX-12: roadmap says global UX remediation/rebase is closed; verify whether any acceptance criterion truly remains before retaining it open;
- #201 LOGIN-8C logo decode fix: verify current main behavior; close if already integrated/superseded;
- #203 Companion localhost/AuthService integration: reproduce on current architecture before treating as active; old Vercel-review context alone is insufficient;
- PR #551 P5-5 replay: superseded by merged #552/#553 closeout;
- PR #573 P5-6 exact-SHA binding: current main already contains later P5-6 candidate/refreeze work; reconcile and close if superseded;
- PR #302 and older open PRs (#182, #207, #221, #222, #223, #138, #171): verify against merged current truth; none may be treated as active merely because GitHub still says open.

**Rule:** stale issue/PR hygiene never changes product status without code + tests + retained evidence.

---

# 8. Closed workstreams retained as history, not backlog

The following are considered closed unless a new reproduced regression opens a new scoped lot:

- Gate A Secure Core;
- P0 foundations;
- product truthfulness;
- agent governance;
- global visual remediation / UX rebase;
- Dashboard responsive convergence and global responsive recertification;
- Journal metabolic-event redesign;
- outbound AI/data-egress foundation;
- sovereign-auth migration work already recorded as merged in prior roadmap;
- Companion intelligence / clinical twin / proactive lifecycle / current convergence;
- CGM gateway V1, V1.1, V2, V2.1;
- P4-FRUGAL PRE-PILOT;
- P5-0, P5-1, P5-2, P5-5;
- P5-4A PWA packaging engineering.

Closed does not imply legal/CNDP authorization, real-device proof, real-patient authorization or broader production approval unless that exact evidence is explicitly retained.

---

# 9. Execution order

1. **P5-6A #318:** obtain real restricted qualification references + exact-SHA safety manifest for `fd3e4a53543e515100b493acc63c99cc9e8464ce`.
2. **P5-6B #320:** freeze actual deployment topology and collect CNDP/consent/processor/residency evidence for the same candidate.
3. Run the three exact-SHA fail-closed audits.
4. Human release decision.
5. Controlled PWA pilot.
6. P5-7 real observed pilot evidence.
7. P5-8 go/no-go.
8. Only then promote deferred native/modality/scale work according to evidence.

Parallel work allowed only when it cannot perturb or delay the frozen release candidate and its evidence chain.

---

# 10. Canonical governance

- `docs/ROADMAP.md` owns **all forward status, priority, sequencing and completion percentages**.
- `docs/TECHDEBT.md` owns unresolved compromises only; it is not a competing roadmap.
- `AGENTS.md` owns execution rules only; any embedded status list is subordinate to this roadmap.
- Issues and PRs are execution/evidence containers, not canonical portfolio status.
- Assessments, handovers and ADRs are evidence/history, not forward authority.
- Never declare a lot closed from an issue title, branch name, PR state or old score alone. Require observable retained evidence.
- No Vercel deployment without explicit owner authorization.

## Current canonical snapshot

- repo: `hraaaaf/IAMINA-MVP`
- frozen P5-6 candidate: `fd3e4a53543e515100b493acc63c99cc9e8464ce`
- candidate proof: PR #591; exact-head #4145/#3719; post-merge #4148/#3722; signed merge
- active program: P5 Pilot Readiness
- progress: **4/9 = 44.4%**
- current blocker: **P5-6A #318 + P5-6B #320 external restricted/deployment evidence**
- release posture: **NOT_RELEASE_AUTHORIZED**
- next exact action: obtain/retain real restricted evidence for #318 and deployment-specific compliance evidence for #320, bind both manifests to `fd3e4a53543e515100b493acc63c99cc9e8464ce`, then run the three exact-SHA approved audits.
