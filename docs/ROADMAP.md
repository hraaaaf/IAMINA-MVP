# IAmina — Canonical Roadmap

> **Authority:** this is the single canonical forward tracker for IAMINA. If an issue, PR body, handover, assessment, AGENTS note, architecture note or historical phase document conflicts with this file on current status, priority or next work, **this file wins**. Historical documents remain evidence only.
>
> **Global audit:** 2026-09-13, re-bound after PR #597 and exact production deployment proof against frozen P5-6 runtime candidate `5b27a22fc5c05a06e7eeeb0e841bb0e7dadce7f6`, open GitHub trackers, `AGENTS.md` and `docs/TECHDEBT.md`.
>
> **Canonical global progress:** **6/12 atomic roadmap lots CLOSED = 50.0%**. Atomic denominator: P5-0, P5-1, P5-2, P5-3, P5-4A, P5-4B, P5-5, P5-6 consent evidence engineering, P5-6A, P5-6B, P5-7, P5-8. Closed atoms: P5-0, P5-1, P5-2, P5-4A, P5-5 and P5-6 consent evidence engineering. The P5 whole-lot metric remains **4/9 = 44.4%** and retained MENA remains **32/38 = 84.2%** for their narrower scopes.
>
> **Release posture:** `NOT_RELEASE_AUTHORIZED`. Owner authorization exists for technical Vercel evidence deployment only; it does not authorize real-patient processing.

## North star

Ship one safe, measurable Morocco/MENA diabetes-companion PWA pilot, collect real evidence, then make an explicit go/no-go decision before broader rollout or a second disease capsule.

## Non-negotiable product boundaries

- Diabetes is the only live condition.
- IAMINA is a patient companion, not a physician replacement.
- Deterministic clinical/safety logic is authoritative; generative models may only narrate approved bounded output.
- No diagnosis, prescription, dose calculation, treatment optimization/change or autonomous medical instruction.
- Language/dialect enablement requires explicit safety parity; location never silently determines language or emergency jurisdiction.
- Pilot delivery is PWA-first. Native Android/iOS is deferred unless explicitly activated.
- Engineering proof, human approval, legal/CNDP approval and real-patient authorization are separate gates.

---

# 1. Executive status

| Area | Canonical status | Forward consequence |
|---|---|---|
| **Global canonical roadmap** | **🟡 6/12 = 50.0%** | authoritative portfolio completion metric |
| Gate A Secure Core | ✅ CLOSED / certified 10.0/10 | maintenance only |
| Historical P0 foundations / product truthfulness / agent governance | ✅ CLOSED | no reopening without new defect/evidence |
| Global UX / Dashboard / Journal | ✅ CLOSED | regressions only |
| Clinical Data Layer & Privacy foundation | ✅ MERGED | residual privacy debt remains under `docs/TECHDEBT.md` |
| Companion intelligence / proactive lifecycle | ✅ CLOSED through current convergence | no active forward feature lot |
| CGM gateway V1/V1.1/V2/V2.1 | ✅ CLOSED | physical-sensor evidence remains external if later claimed |
| P4-FRUGAL PRE-PILOT | ✅ CLOSED 10/10 | real pilot economics belong to P5-7 |
| MENA retained tracker | 🟡 32/38 = 84.2% | informational only |
| P5 whole-lot tracker | 🟡 4/9 = 44.4% | active program |
| P5-6 consent evidence engineering | ✅ CLOSED atomic sublot | inherited unchanged by current candidate |
| P5-6 backend deployment infrastructure | ✅ EXACT_PRODUCTION_HEALTHY | dedicated Neon PostgreSQL migrated; exact Vercel production health 200 |
| Real-patient release | 🟠 BLOCKED_EXTERNAL | current critical path |

### Progress arithmetic

1. **Canonical global progress: 6/12 = 50.0%.** Equal-weight atomic forward lots.
2. **P5 Pilot Readiness: 4/9 = 44.4%.** Historical whole-lot P5 accounting; P5-4 and P5-6 remain open as macro lots.
3. **Retained MENA: 32/38 = 84.2%.** Informational only; never a release gate.

No partial credit is assigned inside an atomic lot.

---

# 2. One critical path

**P5-6A restricted safety evidence + P5-6B deployment-specific topology/compliance evidence → three exact-SHA approved audits → explicit human release decision → controlled PWA pilot → P5-7 observed evidence → P5-8 go/no-go.**

Everything else is closed, deferred, parallel non-blocking work, technical debt or repository hygiene.

---

# 3. P5 Pilot Readiness

## P5-0 — Security reconciliation

**Status:** ✅ CLOSED.

## P5-1 — Morocco linguistic certification

**Status:** ✅ CLOSED / HUMAN_APPROVED / retained exact-main evidence.

Retained proof includes PR #579, exact-main evidence SHA `2d18428a0c59a18c82a1c0dfb410469f17f81e04`, green post-merge CI/migration, packet #34683056185, artifact #10295285314 and human approval in #515.

## P5-2 — Arabic OCR real-world evidence

**Status:** ✅ CLOSED with negative qualification result.

Real-camera Tesseract `ara` failed the required quality floor. No local Arabic full-document primary is qualified.

## P5-3 — Native TTS real-device evidence

**Status:** 🟡 DEFERRED / HUMAN_DEVICE_GATE.

Tracker: #518. Required only before a native pilot/distribution claim; it does not block the current PWA-first pilot.

## P5-4 — Pilot packaging

**Status:** 🟡 SPLIT.

### P5-4A — PWA packaging engineering

**Status:** ✅ CLOSED_WITH_BOUNDARIES.

Persistence, strict offline reopen, release discovery, last-known-good preservation and update behavior are retained. Controlled pilot URL, physical target-browser installation, production deployment and real-patient authorization remain external.

### P5-4B — Native Android/iOS alignment

**Status:** 🟡 DEFERRED.

Future native-only work includes permanent signing/provisioning and physical-device install/update/recovery evidence.

## P5-5 — End-to-end pilot rehearsal

**Status:** ✅ CLOSED / `PASS_WITH_BOUNDARIES`.

Retained synthetic/non-patient proof includes main `88b78e036ce3494dfe37921e70e064fbfdabd6bb`, rehearsal #34573137446, CI #34573137452 and artifact #10188573954.

## P5-6 — Real-patient release gate

**Status:** 🟠 ACTIVE / BLOCKED_EXTERNAL / HIGHEST PRIORITY.

Frozen candidate:

- release SHA: `5b27a22fc5c05a06e7eeeb0e841bb0e7dadce7f6`;
- safety corpus: 59 exact cases;
- parity coverage: 10 technical tuples;
- safety fingerprint: `823d109b0ddd10d1874eec53027eafd9d65884f14810304af3681c57c82cf7e5`;
- consent notice version: `2026-09-12.1`.

### Candidate re-freeze proof

PR #590 first changed backend release/deployment infrastructure and froze `52c0238fede74a1ba85fd3df32b1e89268bbe8f7`. An exact Vercel attempt then proved that candidate's old function-path packaging incompatible with the active Vercel Python contract. PR #597 corrects only that runtime packaging and therefore supersedes `52c0238...` as the forward candidate.

Verified current proof:

- old exact candidate `52c0238fede74a1ba85fd3df32b1e89268bbe8f7` → deployment `dpl_5AcyTUotrjRi5pt7A9zv92dxQsEX` → Vercel `unused_function`, no successful runtime;
- PR #597 exact head `edd4a3d86e4f773c527111b20349dfa6dd09dab5`;
- exact-head CI #4169 / workflow `34749918504` SUCCESS;
- exact-head migration drift #3729 / workflow `34749918503` SUCCESS;
- merge `main@5b27a22fc5c05a06e7eeeb0e841bb0e7dadce7f6`, tree `5b07093b3df9b0d337104e0e82133feb18341d80`;
- exact post-merge CI workflow `34750040306` SUCCESS after re-running backend jobs cancelled only by a later documentation-only push;
- post-merge migration drift #3730 / workflow `34750040338` SUCCESS;
- PR #597 changes exactly `backend/api/index.py`, `backend/core/tests/test_vercel_deployment_contract.py` and `backend/vercel.json`.

The #597 files modify deployment/runtime packaging only. The safety corpus and #591 consent-evidence contract are unchanged, so no safety or consent re-qualification is inferred.

Documentation-only commits may advance `main` without moving this frozen runtime candidate. Any later runtime/code change requires another explicit re-freeze.

### P5-6 consent evidence engineering

**Status:** ✅ CLOSED atomic sublot / MERGED / GREEN.

Retained from #591: exact notice version/hash/locale, legacy consent invalidation, server acceptance receipts, withdrawal revocation, current-consent AI-egress verification, consent-epoch isolation, Flutter/server fail-closed behavior and Secure Storage + Drift local gating.

### P5-6 backend deployment infrastructure

**Status:** ✅ EXACT_PRODUCTION_HEALTHY.

Verified production topology:

- Vercel project `iamina-certified` / `prj_Pn9FnyconF3h2w9gOU74iV98kJoU`, linked to `hraaaaf/IAMINA-MVP`;
- exact frozen source `5b27a22fc5c05a06e7eeeb0e841bb0e7dadce7f6`;
- production deployment `dpl_8ex2k82KaozE6Fxc8wQBYJuRU43y`;
- state `READY`, target `production`, runtime region `cdg1`, one Python serverless function;
- stable alias `iamina-certified.vercel.app` resolves to that deployment;
- dedicated Neon project `IAMINA` / `square-sun-82359137`, PostgreSQL 16, region `aws-eu-central-1`, default branch `production` / `br-fragrant-frost-b1lbdfzs`;
- GitHub Actions run `34752706286`, successful rerun job `103717805309`: migrations applied, `migrate --check` clean, `db_connectivity=ok`, `django_migrations=applied_and_current`;
- `GET https://iamina-certified.vercel.app/api/v1/health` → HTTP 200, `status=ok`, `db=ok`, `cache=unavailable`;
- cache unavailability is non-fatal under the existing health contract; no Redis readiness claim is made;
- no AqarFinder/Supabase database and no unrelated Neon database was reused.

Technical deployment evidence is complete for the exact frozen runtime candidate. This does not authorize patient data or satisfy CNDP/processor evidence gates.

### P5-6A — Safety qualification manifest

**Tracker:** #318.

Already retained: owner-attested safety/clinical review, Darija adjudication/runtime cutover, safety-owner/parity attestation and English-locale validation. The owner-selected qualification wording is **« professionnels qualifiés »**, machine reference `issue-318:owner-attestation:professionnels-qualifies`.

This is an owner attestation and is not represented as independent credential verification. More specific diploma/licence/registration detail is neither invented nor claimed.

Still missing:

- restricted review evidence references required by the manifest, using the retained owner qualification reference where applicable;
- complete approved 59-case and 10-parity decisions;
- restricted safety manifest with `source_commit_sha = 5b27a22fc5c05a06e7eeeb0e841bb0e7dadce7f6` and the exact fingerprint;
- exact-SHA safety audit PASS.

### P5-6B — CNDP / consent / processor / residency

**Tracker:** #320.

Current state: `BLOCKED_EXTERNAL_RELEASE / EXACT_PRODUCTION_HEALTHY / COMPLIANCE_EVIDENCE_PENDING`.

Owner authorization for technical Vercel deployment/evidence collection is retained from 2026-09-13. It is not permission to process real patient data.

Technical runtime/database proof is now retained in #320 comment `5653049361` and this roadmap. Still required:

- freeze the complete actual runtime/database/cache/email/export/provider topology with exact countries/regions in restricted evidence;
- approved deployment-specific patient notice/consent;
- applicable CNDP health-data processing evidence;
- foreign-transfer basis/evidence for every actual external destination, where applicable;
- account-specific processor/DPA/subprocessor/retention/deletion/no-training/privacy/security evidence;
- restricted residency manifest with `source_commit_sha = 5b27a22fc5c05a06e7eeeb0e841bb0e7dadce7f6`;
- exact-SHA consent/residency audit PASS outputs.

Public provider or regulatory documentation may establish requirements but is not account/deployment-specific approval evidence.

### P5-6 success proof

All three fail-closed audits must PASS against the same exact candidate:

```bash
python manage.py audit_pilot_consent_governance --require-approved --expected-source-commit-sha 5b27a22fc5c05a06e7eeeb0e841bb0e7dadce7f6
python manage.py audit_pilot_data_residency --manifest /restricted/iamina/pilot-residency.json --require-approved --expected-source-commit-sha 5b27a22fc5c05a06e7eeeb0e841bb0e7dadce7f6
python manage.py audit_safety_corpus_review --manifest /restricted/iamina/safety-review-manifest.json --require-approved --expected-source-commit-sha 5b27a22fc5c05a06e7eeeb0e841bb0e7dadce7f6
```

Then and only then: explicit human real-patient release decision.

## P5-7 — Observed pilot evidence

**Status:** ⚪ PENDING P5-6.

Collect real pilot MAU/activation/retention, safety incidents, reliability/offline/update failures, LLM route/cost and zero-model rate, storage/egress cost, satisfaction/support burden and clinically safe usefulness signals. Synthetic evidence cannot become P5-7 proof.

## P5-8 — Go / No-Go

**Status:** ⚪ PENDING P5-7.

No second disease capsule before this evidence-based decision gate.

**P5 whole-lot tracker:** 4/9 = 44.4%.  
**Canonical global atomic tracker:** 6/12 = 50.0%.

---

# 4. MENA / multimodal residuals

## P0-MENA-2 — Locale + safety contract

**Status:** 🟡 PARTIALLY OPEN only through P5-6A restricted qualification evidence.

Remaining release-relevant work is absorbed into #318/P5-6A.

## P0-MENA-4 — Multimodal provider benchmark

**Status:** 🟡 DEFERRED / EXTERNAL-HUMAN EVIDENCE, issue #319.

Groq + `openai/gpt-oss-120b` remains the conversational candidate; no local Arabic full-document OCR primary qualifies under the current strict floor; native TTS evidence is deferred to P5-3; STT remains deferred by owner decision.

Retained MENA metric: 32/38 = 84.2%, informational only.

---

# 5. Parallel engineering debt

`docs/TECHDEBT.md` owns unresolved compromises; it is not a competing roadmap. Critical/high debt is promoted into the P5 critical path only when the corresponding feature is in pilot scope or a current defect is reproduced. Historical debt entries that have been superseded by P5-1/P5-6 must be reconciled rather than blindly reopened.

---

# 6. CI / cost optimization

CI-FRUGAL-2 / #442 remains parallel and non-blocking. Runner-cost work must not weaken retained visual certification or delay P5-6.

---

# 7. Repository hygiene

Open GitHub items are not automatically active roadmap work. Historical Companion/OCR evidence issues and stale PRs remain evidence/hygiene until current-main reproduction proves forward work. Stale issue/PR state never changes product status without code + tests + retained evidence.

---

# 8. Closed workstreams retained as history

Closed unless a new reproduced regression opens a scoped lot: Gate A Secure Core; P0 foundations; product truthfulness; agent governance; global UX/Dashboard/Journal convergence; outbound AI/data-egress foundation; current sovereign-auth migration work recorded as merged; Companion intelligence/proactivity convergence; CGM gateway V1/V1.1/V2/V2.1; P4-FRUGAL PRE-PILOT; P5-0; P5-1; P5-2; P5-5; P5-4A; and the P5-6 consent-evidence engineering atomic sublot.

Closed does not imply legal/CNDP authorization, physical-device proof, real-patient authorization or production approval unless that exact evidence is retained.

---

# 9. Execution order

1. **P5-6A #318:** build the exact-SHA restricted safety manifest for `5b27a22fc5c05a06e7eeeb0e841bb0e7dadce7f6`, using the retained owner qualification wording **« professionnels qualifiés »**, and complete the 59-case / 10-parity approvals.
2. **P5-6B #320:** freeze the actual Vercel `cdg1` + Neon `aws-eu-central-1` topology plus cache/email/export/provider paths and collect deployment/account-specific CNDP, consent, processor, residency and transfer evidence; build the exact-SHA residency manifest.
3. Run the three exact-SHA fail-closed audits.
4. Explicit human real-patient release decision.
5. Controlled PWA pilot.
6. P5-7 observed evidence.
7. P5-8 go/no-go.

Parallel work is allowed only if it cannot perturb the frozen candidate or its evidence chain.

---

# 10. Canonical governance

- `docs/ROADMAP.md` owns all forward status, priority, sequencing and completion percentages.
- Overall progress is the atomic 12-lot metric. Its denominator changes only through an explicit roadmap governance change.
- `docs/TECHDEBT.md` owns unresolved compromises only.
- `AGENTS.md` owns execution rules only and is subordinate to this roadmap for status.
- Issues/PRs are execution/evidence containers, not canonical portfolio status.
- Assessments/handovers/ADRs are evidence/history, not forward authority.
- Never declare a lot closed from a title, branch, PR state or old score alone.
- No Vercel deployment without explicit owner authorization; technical deployment authorization never implies real-patient release.

## Current canonical snapshot

- repo: `hraaaaf/IAMINA-MVP`
- frozen P5-6 runtime candidate: `5b27a22fc5c05a06e7eeeb0e841bb0e7dadce7f6`
- candidate proof: PR #597; exact-head CI #4169 / drift #3729; post-merge CI `34750040306` / drift #3730; merge `5b27a22...`
- exact production proof: `dpl_8ex2k82KaozE6Fxc8wQBYJuRU43y`, source `5b27a22...`, Python function, `cdg1`, stable alias `iamina-certified.vercel.app`, health HTTP 200 / `db=ok`
- dedicated database proof: Neon `IAMINA` / `square-sun-82359137`, PG16, `aws-eu-central-1`, branch `production`, migrations current
- safety fingerprint: `823d109b0ddd10d1874eec53027eafd9d65884f14810304af3681c57c82cf7e5`
- qualification wording: **professionnels qualifiés** — owner attestation reference `issue-318:owner-attestation:professionnels-qualifies`
- consent notice: `2026-09-12.1`
- canonical global progress: **6/12 = 50.0%**
- P5 whole-lot progress: **4/9 = 44.4%**
- retained MENA: **32/38 = 84.2%**
- current blockers: **#318 restricted exact-corpus manifest + #320 deployment-specific CNDP/processor/residency/transfer evidence**
- deployment state: **exact frozen candidate healthy in production; real-patient release still blocked externally**
- release posture: **NOT_RELEASE_AUTHORIZED**
- next exact action: build the restricted #318/#320 evidence packet against the proven exact deployment, bind both manifests to `5b27a22fc5c05a06e7eeeb0e841bb0e7dadce7f6`, then run the three exact-SHA approved audits.