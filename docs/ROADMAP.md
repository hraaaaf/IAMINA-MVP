# IAmina — Canonical Roadmap

> **Authority:** this is the single canonical forward tracker for IAMINA. If an issue, PR body, handover, assessment, AGENTS note, architecture note or historical phase document conflicts with this file on current status, priority or next work, **this file wins**. Historical documents remain evidence only.
>
> **Global audit:** 2026-09-14, reconciled against current `main`, P5-6 release-gate evidence, #318/#320, and `docs/TECHDEBT.md`. The forward P5-6 candidate is `fb42e4d641b7b057607fe6a2de3d5104ccf15d0b`; the predecessor `5b27a22fc5c05a06e7eeeb0e841bb0e7dadce7f6` remains the last exact production-proven deployment.
>
> **Canonical global progress:** **6/12 atomic roadmap lots CLOSED = 50.0%**. Atomic denominator: P5-0, P5-1, P5-2, P5-3, P5-4A, P5-4B, P5-5, P5-6 consent evidence engineering, P5-6A, P5-6B, P5-7, P5-8. Closed atoms: P5-0, P5-1, P5-2, P5-4A, P5-5 and P5-6 consent evidence engineering. The P5 whole-lot metric remains **4/9 = 44.4%** and retained MENA remains **32/38 = 84.2%** for their narrower scopes.
>
> **Release posture:** `NOT_RELEASE_AUTHORIZED`. No current authorization exists to deploy the refrozen candidate or process real-patient data.

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
| P5-6 predecessor deployment infrastructure | ✅ EXACT_PRODUCTION_HEALTHY | proves Vercel/Neon path for `5b27a22…`, not exact deployment proof for current candidate |
| P5-6 current forward candidate | 🟠 REFROZEN / NOT_DEPLOYED | `fb42e4d…`; deployment requires separate explicit owner authorization |
| Real-patient release | 🟠 BLOCKED_EXTERNAL | current critical path |

### Progress arithmetic

1. **Canonical global progress: 6/12 = 50.0%.** Equal-weight atomic forward lots.
2. **P5 Pilot Readiness: 4/9 = 44.4%.** Historical whole-lot P5 accounting; P5-4 and P5-6 remain open as macro lots.
3. **Retained MENA: 32/38 = 84.2%.** Informational only; never a release gate.

No partial credit is assigned inside an atomic lot.

---

# 2. One critical path

**P5-6A restricted safety evidence + P5-6B processor/CNDP evidence + explicitly authorized exact-candidate deployment/topology proof → three exact-SHA approved audits → explicit human release decision → controlled PWA pilot → P5-7 observed evidence → P5-8 go/no-go.**

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

Forward candidate:

- release SHA: `fb42e4d641b7b057607fe6a2de3d5104ccf15d0b`;
- safety corpus: 59 exact cases;
- parity coverage: 10 technical tuples;
- safety fingerprint: `823d109b0ddd10d1874eec53027eafd9d65884f14810304af3681c57c82cf7e5`;
- consent notice version: `2026-09-12.1`.

### Candidate re-freeze proof

The predecessor candidate `5b27a22fc5c05a06e7eeeb0e841bb0e7dadce7f6` proved the Vercel/Django/Neon runtime. Two release-gate defects were then fixed:

- PR #602 made the local-only consent audit consume the restricted residency manifest and bind genuine CNDP health-processing evidence to the exact release SHA;
- PR #603 made native password recovery require an explicit provider-neutral SMTP production contract, removed silent delivery assumptions and preserved account-enumeration resistance.

Validation retained for the refrozen candidate:

- #602 exact-head CI #4186 / workflow `34771054574` SUCCESS;
- #602 exact-head migration drift #3733 / workflow `34771054541` SUCCESS;
- #603 exact-head CI #4189 / workflow `34771391814` SUCCESS;
- #603 exact-head migration drift #3736 / workflow `34771391809` SUCCESS;
- #603 merge `main@fb42e4d641b7b057607fe6a2de3d5104ccf15d0b`;
- post-merge CI #4190 / workflow `34773613905` SUCCESS;
- post-merge migration drift #3737 / workflow `34773613814` SUCCESS.

Clinical rebind proof:

- `backend/core/safety_corpora.py` blob is identical between `5b27a22…` and `fb42e4d…`: `bf046c298ee8e77591f5c5b1049b806a6255bfcf`;
- `backend/core/triage_classification.py` blob is identical between those candidates: `eba7a57967eeec1ba4b264c90ccab1a30e516b38`;
- the retained corpus therefore remains 59 exact cases / 10 tuples with fingerprint `823d109b0ddd10d1874eec53027eafd9d65884f14810304af3681c57c82cf7e5`.

This is a technical exact-corpus rebind only. It does not fabricate reviewer identity, qualification or a new human approval.

Documentation-only closeout commits may advance `main` without moving the frozen candidate. Any later runtime/code change requires another explicit re-freeze.

### P5-6 consent evidence engineering

**Status:** ✅ CLOSED atomic sublot / MERGED / GREEN.

Retained from #591: exact notice version/hash/locale, legacy consent invalidation, server acceptance receipts, withdrawal revocation, current-consent AI-egress verification, consent-epoch isolation, Flutter/server fail-closed behavior and Secure Storage + Drift local gating.

### P5-6 deployment state

**Status:** 🟠 PREDECESSOR_EXACT_PRODUCTION_HEALTHY / CURRENT_CANDIDATE_NOT_DEPLOYED.

Proven predecessor topology:

- Vercel project `iamina-certified` / `prj_Pn9FnyconF3h2w9gOU74iV98kJoU`;
- exact source `5b27a22fc5c05a06e7eeeb0e841bb0e7dadce7f6`;
- production deployment `dpl_8ex2k82KaozE6Fxc8wQBYJuRU43y`;
- state `READY`, target `production`, runtime region `cdg1`, one Python serverless function;
- stable alias `iamina-certified.vercel.app` resolved to that deployment;
- dedicated Neon project `IAMINA` / `square-sun-82359137`, PostgreSQL 16, region `aws-eu-central-1`, default branch `production` / `br-fragrant-frost-b1lbdfzs`;
- migrations current and health HTTP 200 with `status=ok`, `db=ok`, `cache=unavailable`;
- cache unavailability is non-fatal under the existing health contract; no Redis readiness claim is made;
- no AqarFinder/Supabase database and no unrelated Neon database was reused.

The current candidate `fb42e4d…` is **not deployed**. PR #603 deliberately makes production startup fail closed until an explicit SMTP/reset contract is configured. No deployment of the refrozen candidate may be performed without separate explicit owner authorization.

### P5-6A — Safety qualification manifest

**Tracker:** #318.

Current state: `OPEN / REVIEW_ATTESTED / OWNER_QUALIFICATION_ATTESTATION_RETAINED / EXACT_CORPUS_REBOUND_TECHNICALLY / RESTRICTED_QUALIFICATION_REFERENCES_PENDING / BLOCKED_EXTERNAL_HUMAN`.

Already retained: owner-attested safety/clinical review, Darija adjudication/runtime cutover, safety-owner/parity attestation and English-locale validation. Owner qualification wording: **« professionnels qualifiés »**, reference `issue-318:owner-attestation:professionnels-qualifies`.

Still missing:

- real opaque native-reviewer references for `fr`, `ar`, `en`, `ar-MA`;
- real qualification references required by the manifest contract;
- non-stale `reviewed_on` / `review_due_on`;
- approved coverage of all 59 exact case IDs;
- approved coverage of all 10 exact parity tuples;
- restricted safety manifest with `source_commit_sha = fb42e4d641b7b057607fe6a2de3d5104ccf15d0b` and the exact fingerprint;
- exact-SHA safety audit PASS.

### P5-6B — CNDP / consent / processor / residency

**Tracker:** #320.

Current state: `OPEN / BLOCKED_EXTERNAL_RELEASE / PREDECESSOR_DEPLOYMENT_PROVEN / CURRENT_CANDIDATE_NOT_DEPLOYED / SMTP_PROCESSOR_PENDING / COMPLIANCE_EVIDENCE_PENDING`.

Still required:

- choose and configure the actual password-reset mail processor under the provider-neutral SMTP contract;
- account-specific processor/DPA/subprocessor/retention/deletion/privacy/security evidence for every enabled processor;
- actual exact-candidate topology with countries/regions after an explicitly authorized deployment;
- deployment-specific patient notice/consent approval evidence;
- applicable CNDP health-data processing evidence;
- foreign-transfer basis/evidence for every actual external destination where applicable;
- restricted residency manifest bound to `fb42e4d641b7b057607fe6a2de3d5104ccf15d0b`;
- exact-SHA consent and residency audit PASS outputs.

Public provider/CNDP documentation can define requirements but cannot substitute for account-specific approvals.

The current pilot scope enables no external AI processor. `--local-only` remains mandatory for the consent audit; it does not waive the global CNDP health-processing authorization gate.

### P5-6 success proof

All three fail-closed audits must PASS against the same exact candidate:

```bash
python manage.py audit_pilot_consent_governance \
  --local-only \
  --residency-manifest /restricted/iamina/pilot-residency.json \
  --require-approved \
  --expected-source-commit-sha fb42e4d641b7b057607fe6a2de3d5104ccf15d0b

python manage.py audit_pilot_data_residency \
  --manifest /restricted/iamina/pilot-residency.json \
  --require-approved \
  --expected-source-commit-sha fb42e4d641b7b057607fe6a2de3d5104ccf15d0b

python manage.py audit_safety_corpus_review \
  --manifest /restricted/iamina/safety-review-manifest.json \
  --require-approved \
  --expected-source-commit-sha fb42e4d641b7b057607fe6a2de3d5104ccf15d0b
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

Runtime locale/high-severity variant coverage is implemented and bound into the exact safety corpus. Remaining release-relevant work is external/restricted review evidence under #318/P5-6A, not a separate implementation debt.

## P0-MENA-4 — Multimodal provider benchmark

**Status:** 🟡 DEFERRED / EXTERNAL-HUMAN EVIDENCE, issue #319.

Groq + `openai/gpt-oss-120b` remains the conversational candidate; no local Arabic full-document OCR primary qualifies under the current strict floor; native TTS evidence is deferred to P5-3; STT remains deferred by owner decision.

Retained MENA metric: 32/38 = 84.2%, informational only.

---

# 5. Parallel engineering debt

`docs/TECHDEBT.md` owns unresolved compromises; it is not a competing roadmap. Critical/high debt is promoted into the P5 critical path only when the corresponding feature is in pilot scope or a current defect is reproduced.

Reconciliation retained on 2026-09-14:

- TD-010 observability retention lifecycle is CLOSED by PR #610, merge `e9c04beee31638ff86d7fd0b50d5eddccc313c4e`, post-merge CI #4206 / workflow `34787203311` SUCCESS and migration drift #3742 SUCCESS;
- former TD-005 and TD-006 were removed from the unresolved-debt register because current runtime safety variant coverage is implemented and the only remaining release gate is the restricted human qualification/approval evidence already owned by #318/P5-6A;
- former TD-007 was removed after verifying the explicitly approved/documented `SELF_CARE_ONLY` pilot operating model: PR #24 formalized no human monitoring, mandatory disclosure and fail-closed evidence requirements for any future `MONITORED_HUMAN` mode; P0.6 PR #128 later centralized all patient-facing urgent responses through that policy.

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

1. **P5-6A #318:** complete the restricted safety evidence for `fb42e4d641b7b057607fe6a2de3d5104ccf15d0b`: real qualification/reviewer references, review-due policy/date, approved 59-case / 10-parity coverage and exact manifest.
2. **P5-6B #320:** choose the actual password-reset mail processor and collect the account-specific processor/CNDP/consent/residency/transfer evidence that can be assembled before deployment.
3. **Human gate:** obtain separate explicit owner authorization before any deployment of `fb42e4d…`.
4. Deploy the exact candidate only after that authorization, freeze actual topology, complete the exact residency manifest.
5. Run the three exact-SHA fail-closed audits.
6. Explicit human real-patient release decision.
7. Controlled PWA pilot.
8. P5-7 observed evidence.
9. P5-8 go/no-go.

Parallel engineering debt may proceed only if it cannot perturb the frozen candidate or its evidence chain.

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
- forward frozen P5-6 candidate: `fb42e4d641b7b057607fe6a2de3d5104ccf15d0b`
- candidate proof: PRs #602/#603; #603 post-merge CI #4190 / workflow `34773613905`; post-merge drift #3737 / workflow `34773613814`
- current candidate deployment: **NOT DEPLOYED**
- proven predecessor production deployment: `dpl_8ex2k82KaozE6Fxc8wQBYJuRU43y`, source `5b27a22fc5c05a06e7eeeb0e841bb0e7dadce7f6`, Python function, `cdg1`, health HTTP 200 / `db=ok`
- dedicated database proof: Neon `IAMINA` / `square-sun-82359137`, PG16, `aws-eu-central-1`, branch `production`, migrations current for the predecessor deployment
- safety fingerprint: `823d109b0ddd10d1874eec53027eafd9d65884f14810304af3681c57c82cf7e5`
- qualification wording: **professionnels qualifiés** — owner attestation reference `issue-318:owner-attestation:professionnels-qualifies`
- consent notice: `2026-09-12.1`
- canonical global progress: **6/12 = 50.0%**
- P5 whole-lot progress: **4/9 = 44.4%**
- retained MENA: **32/38 = 84.2%**
- current blockers: **#318 restricted qualification/approval evidence + #320 processor/CNDP/account evidence + exact-candidate deployment topology after explicit authorization**
- release posture: **NOT_RELEASE_AUTHORIZED**
- next exact action: finish all non-deployment #318/#320 evidence possible for `fb42e4d…`; deployment remains a human gate requiring explicit owner authorization.
