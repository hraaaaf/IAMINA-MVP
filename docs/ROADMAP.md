# IAmina — Canonical Roadmap

> **Authority:** this is the single canonical forward tracker for IAMINA. If an issue, PR body, handover, assessment, AGENTS note, architecture note or historical phase document conflicts with this file on current status, priority or next work, **this file wins**. Historical documents remain evidence only.
>
> **Global audit:** 2026-09-17, reconciled against `main@df457cfdcc574439adb791fbfc44d484a1224417`, P5-4A merge #639, TD-014 merge #649, P5-6 release-gate evidence, #318/#320, `docs/TECHDEBT.md`, and the clarified local-first runtime boundary. The last explicitly frozen P5-6 candidate is `fb42e4d641b7b057607fe6a2de3d5104ccf15d0b`; later runtime/code changes mean it is retained as historical freeze evidence only, not as the current release candidate. The predecessor `5b27a22fc5c05a06e7eeeb0e841bb0e7dadce7f6` remains the last exact **remote development/certification** deployment proof. Vercel/Django/Neon is not the patient production runtime. No current release candidate exists until an explicit re-freeze is performed when the pre-real-patient gate is reactivated.
>
> **Canonical global progress:** **6/12 atomic roadmap lots CLOSED = 50.0%**. Atomic denominator: P5-0, P5-1, P5-2, P5-3, P5-4A, P5-4B, P5-5, P5-6 consent evidence engineering, P5-6A, P5-6B, P5-7, P5-8. Closed atoms currently retained: P5-0, P5-1, P5-2, P5-4A, P5-5 and P5-6 consent evidence engineering. The P5 whole-lot metric remains **4/9 = 44.4%** because P5-4B remains deferred and P5-6 remains open as a macro release gate. Retained MENA remains **32/38 = 84.2%** for its narrower scope.
>
> **Release posture:** `NOT_RELEASE_AUTHORIZED`. No current release candidate is frozen or authorized for deployment or real-patient processing. Engineering, UX, reliability, security and synthetic/non-patient work may continue. P5-6A/#318 and P5-6B/#320 are retained as mandatory **pre-real-patient gates**, not as the current engineering critical path.

## North star

Ship one safe, measurable Morocco/MENA diabetes-companion PWA pilot, collect real evidence, then make an explicit go/no-go decision before broader rollout or a second disease capsule.

## Non-negotiable product boundaries

- Diabetes is the only live condition.
- IAMINA is a patient companion, not a physician replacement.
- Deterministic clinical/safety logic is authoritative; generative models may only narrate approved bounded output.
- No diagnosis, prescription, dose calculation, treatment optimization/change or autonomous medical instruction.
- Language/dialect enablement requires explicit safety parity; location never silently determines language or emergency jurisdiction.
- Pilot delivery is PWA-first. Native Android/iOS is deferred unless explicitly activated.
- **Patient runtime is local-first:** first device enrollment, subsequent reopen, core clinical persistence and required local workflows must not require Vercel, Neon, Firebase, SMTP or another remote processor to be reachable.
- `iamina-certified` on Vercel, its Django runtime and its dedicated Neon database are **development/integration/certification infrastructure**, not the patient production runtime.
- Remote account creation is disabled by default in the patient path and may be enabled only explicitly for a remote DEV/certification account flow. Remote account, synchronization or auxiliary services may degrade independently; their outage or credential rejection must not destroy local enrollment or valid local clinical state.
- Local enrollment is continuity state; Web/PWA patient access is additionally protected by the merged strong device-local WebAuthn app-lock from #649. IAMINA does not own a weak PIN/password fallback for this lock and does not receive biometric material.
- Engineering proof, human approval, legal/CNDP approval and real-patient authorization are separate gates.
- No identifiable real-patient health data may enter IAMINA until the pre-real-patient gate is explicitly completed and release is authorized.

---

# 1. Executive status

| Area | Canonical status | Forward consequence |
|---|---|---|
| **Global canonical roadmap** | **🟡 6/12 = 50.0%** | continue verified non-patient engineering and remaining unresolved debt |
| Gate A Secure Core | ✅ CLOSED / certified 10.0/10 | maintenance only |
| Historical P0 foundations / product truthfulness / agent governance | ✅ CLOSED | no reopening without new defect/evidence |
| Global UX / Dashboard / Journal | ✅ CLOSED | regressions only |
| Clinical Data Layer & Privacy foundation | ✅ MERGED | residual privacy debt remains under `docs/TECHDEBT.md` |
| Companion intelligence / proactive lifecycle | ✅ CLOSED through current convergence | no active forward feature lot |
| CGM gateway V1/V1.1/V2/V2.1 | ✅ CLOSED | physical-sensor evidence remains external if later claimed |
| P4-FRUGAL PRE-PILOT | ✅ CLOSED 10.0/10 | real pilot economics belong to P5-7 |
| MENA retained tracker | 🟡 32/38 = 84.2% | informational only |
| P5 whole-lot tracker | 🟡 4/9 = 44.4% | active program |
| P5-4A offline packaging | ✅ CLOSED / AUTH_LOCAL_FIRST + STRONG_LOCAL_APP_LOCK | local-first availability and WebAuthn app-lock are merged; keep regression coverage |
| P5-6 consent evidence engineering | ✅ CLOSED atomic sublot | retained as merged engineering evidence |
| P5-6 remote dev/cert infrastructure | ✅ EXACT_REMOTE_PATH_HEALTHY / NOT_PATIENT_PROD | proves Vercel/Neon dev/cert path for `5b27a22…`; does not define patient production topology |
| P5-6 last frozen candidate evidence | 🟠 HISTORICAL_FREEZE / NOT_CURRENT | `fb42e4d…`; runtime/code advanced later, so explicit re-freeze is required before any release attempt |
| P5-6 current release candidate | ⚪ NONE | must be created by an explicit exact-SHA re-freeze when the pre-real-patient gate is reactivated |
| P5-6A / P5-6B | ⏸️ PRE_REAL_PATIENT_GATE / DEFERRED | mandatory before first identifiable real-patient health data; not current engineering critical path |
| Real-patient release | 🟠 NOT_AUTHORIZED | blocked until pre-real-patient gate is completed and explicitly authorized |

### Progress arithmetic

1. **Canonical global progress: 6/12 = 50.0%.** Equal-weight atomic forward lots; P5-4A is re-closed after merged local-first remediation and exact-head proof.
2. **P5 Pilot Readiness: 4/9 = 44.4%.** Historical whole-lot P5 accounting; P5-4 and P5-6 remain open as macro lots.
3. **Retained MENA: 32/38 = 84.2%.** Informational only; never a release gate.

No partial credit is assigned inside an atomic lot. Deferring a gate does not close it and does not increase progress.

---

# 2. One critical path

**Current non-patient engineering path:** continue verified product/security/reliability/UX work on synthetic or non-patient data, prioritizing reproduced defects and the unresolved items that remain in `docs/TECHDEBT.md`.

**Mandatory pre-real-patient path, activated before the first identifiable real-patient health data:** explicit exact-SHA re-freeze → P5-6A restricted safety evidence + P5-6B processor/CNDP evidence bound to the **actual local-first patient runtime and genuinely enabled external processors** → actual patient-runtime topology proof → three exact-SHA approved audits → explicit human release decision → controlled PWA pilot → P5-7 observed evidence → P5-8 go/no-go.

The Vercel/Django/Neon development/certification stack is not a mandatory patient-production dependency and must not be inserted into the patient processor/residency inventory solely because it exists for engineering. The pre-real-patient path is deferred, not waived. No release, deployment authorization or regulatory approval is implied by current engineering progress.

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

**Status:** 🟡 SPLIT / P5-4A CLOSED / P5-4B DEFERRED.

### P5-4A — PWA packaging engineering

**Status:** ✅ CLOSED / AUTH_LOCAL_FIRST_VERIFIED / STRONG_LOCAL_APP_LOCK_MERGED.

The reproduced offline-auth regression is resolved. PR #639 (`fix(auth): restore local-first offline reopen boundary`) merged as `bd13e8ad0c6f3ff2c4376b00c43fb8c54068d053`; its final candidate head was `05d02a0def7b909b83615c506ccf97f9623f1c6b`.

Retained local-first contract:

- first patient-device enrollment creates only a device-local enrollment marker plus opaque installation identifier and performs **zero required network requests**;
- subsequent local boot/reopen performs **zero required auth-network requests**;
- the default patient enrollment UI requests no email/password and makes no online-account claim;
- remote account registration is disabled by default and `registerWithEmail()` fails closed unless `IAMINA_REMOTE_ACCOUNT_ENROLLMENT=true` is explicitly enabled for the remote DEV/certification flow;
- local enrollment/session and the Django-signed remote API bearer are separate states;
- remote bearer rejection/expiry clears remote credential use only and cannot erase local enrollment or local clinical state;
- explicit sign-out clears the remote bearer, local marker and opaque local device identifier even if remote logout is unavailable;
- malformed secure-storage text never bootstraps local enrollment.

The separate strong local-auth debt was then resolved by PR #649 (`feat(auth): add strong local WebAuthn app-lock`), merged as `main@df457cfdcc574439adb791fbfc44d484a1224417`. The final exact candidate `fd5bc4392ceda6b411b72f3ceb9254119024ac5c` passed all 15 pull-request workflows, including CI #4454, TD-014 local app-lock certification #14 and TD-008 device integration baseline #14.

Fresh TD-014 artifact `10517999169`, digest `sha256:a0d17487f8cdca0bed18979e650eab6efc6679c76d834938dbae58de3e4f0255`, was inspected and retained:

- WebAuthn platform authenticator with required user verification;
- local/offline unlock with application network unavailable;
- user-verification failure fails closed;
- a genuinely mutated public key fails closed;
- no application network is required for unlock;
- BEFORE / setup / locked captures at `390×844`, `768×1024`, `1280×900`;
- zero horizontal overflow in the retained visual report;
- final P5-4A `AuthService` remained byte-identical through the app-lock lot.

Controlled pilot URL, physical target-browser installation, any patient distribution hosting, production release and real-patient authorization remain external.

### P5-4B — Native Android/iOS alignment

**Status:** 🟡 DEFERRED.

Future native-only work includes permanent signing/provisioning and physical-device install/update/recovery evidence.

## P5-5 — End-to-end pilot rehearsal

**Status:** ✅ CLOSED / `PASS_WITH_BOUNDARIES`.

Retained synthetic/non-patient proof includes main `88b78e036ce3494dfe37921e70e064fbfdabd6bb`, rehearsal #34573137446, CI #34573137452 and artifact #10188573954.

## P5-6 — Real-patient release gate

**Status:** ⏸️ PRE_REAL_PATIENT_GATE / DEFERRED / NOT_RELEASE_AUTHORIZED.

This gate is mandatory before the first identifiable real-patient health data enters IAMINA. It is not the current day-to-day engineering priority while work remains synthetic/non-patient. Deferral does not constitute approval, closure or waiver.

### Last retained frozen candidate evidence

The last explicitly frozen release SHA was `fb42e4d641b7b057607fe6a2de3d5104ccf15d0b`, with:

- safety corpus: 59 exact cases;
- parity coverage: 10 technical tuples;
- safety fingerprint: `823d109b0ddd10d1874eec53027eafd9d65884f14810304af3681c57c82cf7e5`;
- consent notice version: `2026-09-12.1`.

That SHA is retained as historical exact-freeze evidence. It is **not** the current release candidate because later runtime/code changes have advanced `main`. A new exact release candidate must be explicitly re-frozen before the pre-real-patient gate is executed.

### Historical candidate re-freeze proof

The predecessor candidate `5b27a22fc5c05a06e7eeeb0e841bb0e7dadce7f6` proved the **remote Vercel/Django/Neon development/certification path**. It did not prove or define the patient production runtime. Two release-gate/runtime defects were then fixed:

- PR #602 made the local-only consent audit consume the restricted residency manifest and bind genuine CNDP health-processing evidence to the exact release SHA;
- PR #603 made native password recovery require an explicit provider-neutral SMTP contract when that remote recovery path is enabled, removed silent delivery assumptions and preserved account-enumeration resistance.

Validation retained for the historical `fb42e4d…` freeze:

- #602 exact-head CI #4186 / workflow `34771054574` SUCCESS;
- #602 exact-head migration drift #3733 / workflow `34771054541` SUCCESS;
- #603 exact-head CI #4189 / workflow `34771391814` SUCCESS;
- #603 exact-head migration drift #3736 / workflow `34771391809` SUCCESS;
- #603 merge `main@fb42e4d641b7b057607fe6a2de3d5104ccf15d0b`;
- post-merge CI #4190 / workflow `34773613905` SUCCESS;
- post-merge migration drift #3737 / workflow `34773613814` SUCCESS.

Clinical rebind proof retained for that historical freeze:

- `backend/core/safety_corpora.py` blob is identical between `5b27a22…` and `fb42e4d…`: `bf046c298ee8e77591f5c5b1049b806a6255bfcf`;
- `backend/core/triage_classification.py` blob is identical between those candidates: `eba7a57967eeec1ba4b264c90ccab1a30e516b38`;
- the retained corpus therefore remains 59 exact cases / 10 tuples with fingerprint `823d109b0ddd10d1874eec53027eafd9d65884f14810304af3681c57c82cf7e5`.

This is historical technical exact-corpus evidence only. It does not fabricate reviewer identity, qualification or a new human approval. Any later runtime/code change invalidates use of that historical freeze as the current release candidate and requires another explicit re-freeze before a real-patient release attempt.

### P5-6 consent evidence engineering

**Status:** ✅ CLOSED atomic sublot / MERGED / GREEN.

Retained from #591: exact notice version/hash/locale, legacy consent invalidation, server acceptance receipts, withdrawal revocation, current-consent AI-egress verification, consent-epoch isolation, Flutter/server fail-closed behavior and Secure Storage + Drift local gating.

### P5-6 remote development/certification deployment state

**Status:** ✅ PREDECESSOR_REMOTE_PATH_HEALTHY / NOT_PATIENT_PROD / NO_CURRENT_CANDIDATE.

Proven predecessor **remote development/certification** topology:

- Vercel project `iamina-certified` / `prj_Pn9FnyconF3h2w9gOU74iV98kJoU`;
- exact source `5b27a22fc5c05a06e7eeeb0e841bb0e7dadce7f6`;
- deployment `dpl_8ex2k82KaozE6Fxc8wQBYJuRU43y`;
- state `READY`, target `production` in Vercel's deployment terminology, runtime region `cdg1`, one Python serverless function;
- stable alias `iamina-certified.vercel.app` resolved to that deployment;
- dedicated Neon project `IAMINA` / `square-sun-82359137`, PostgreSQL 16, region `aws-eu-central-1`, default branch `production` / `br-fragrant-frost-b1lbdfzs`;
- migrations current and health HTTP 200 with `status=ok`, `db=ok`, `cache=unavailable`;
- cache unavailability is non-fatal under the existing health contract; no Redis readiness claim is made;
- no AqarFinder/Supabase database and no unrelated Neon database was reused.

The words `production` above describe Vercel/Neon environment labels only. They do **not** mean patient production. `docs/LOCAL_FIRST_RUNTIME_BOUNDARY.md` defines the runtime boundary.

The historical `fb42e4d…` freeze was **not deployed**. PR #603 deliberately made the remote Django production-settings path fail closed until an explicit SMTP/reset contract is configured. That is a remote dev/cert deployment condition, not a requirement for local clinical availability. No future Vercel deployment may occur without separate explicit owner authorization.

### P5-6A — Safety qualification manifest

**Tracker:** #318.

Current state: `OPEN / PRE_REAL_PATIENT_GATE / DEFERRED / REVIEW_ATTESTED / OWNER_QUALIFICATION_ATTESTATION_RETAINED / HISTORICAL_EXACT_CORPUS_EVIDENCE_RETAINED / CURRENT_CANDIDATE_PENDING_REFREEZE / RESTRICTED_QUALIFICATION_REFERENCES_PENDING`.

Already retained: owner-attested safety/clinical review, Darija adjudication/runtime cutover, safety-owner/parity attestation and English-locale validation. Owner qualification wording: **« professionnels qualifiés »**, reference `issue-318:owner-attestation:professionnels-qualifies`.

Still missing before real-patient release:

- explicit exact-SHA re-freeze of the future release candidate;
- real opaque native-reviewer references for `fr`, `ar`, `en`, `ar-MA`;
- real qualification references required by the manifest contract;
- non-stale `reviewed_on` / `review_due_on`;
- approved coverage of all 59 exact case IDs;
- approved coverage of all 10 exact parity tuples;
- restricted safety manifest bound to the newly refrozen exact candidate and exact safety fingerprint;
- exact-SHA safety audit PASS.

### P5-6B — CNDP / consent / processor / residency

**Tracker:** #320.

Current state: `OPEN / PRE_REAL_PATIENT_GATE / DEFERRED / REMOTE_DEV_CERT_PATH_PROVEN / PATIENT_RUNTIME_TOPOLOGY_PENDING / COMPLIANCE_EVIDENCE_PENDING`.

Still required before real-patient release:

- explicit exact-SHA re-freeze of the future release candidate;
- freeze the **actual local-first patient runtime topology** and enumerate only the external processors genuinely enabled for that pilot;
- account-specific processor/DPA/subprocessor/retention/deletion/privacy/security evidence for every genuinely enabled external processor;
- if remote password recovery is enabled for the pilot, choose/configure its mail processor and include it in that evidence inventory; if it is not enabled, do not fabricate it as a runtime dependency;
- deployment/distribution-specific patient notice/consent approval evidence for the actual pilot architecture;
- applicable CNDP health-data processing evidence;
- foreign-transfer basis/evidence for every actual external destination where applicable;
- restricted residency manifest bound to the newly refrozen exact candidate and actual patient topology;
- exact-SHA consent and residency audit PASS outputs.

Public provider/CNDP documentation can define requirements but cannot substitute for account-specific approvals. Development-only Vercel/Neon infrastructure is excluded from the patient processor/residency inventory unless the actual pilot architecture later enables it for patient data.

The current pilot scope enables no external AI processor. `--local-only` remains mandatory for the consent audit when the gate is activated; it does not waive the global CNDP health-processing authorization gate.

### P5-6 success proof

When preparation for the first real-patient pilot starts, first explicitly re-freeze the exact release SHA and bind all restricted manifests to that same SHA and the actual patient runtime topology. Then all three fail-closed audits must PASS against it:

```bash
python manage.py audit_pilot_consent_governance \
  --local-only \
  --residency-manifest /restricted/iamina/pilot-residency.json \
  --require-approved \
  --expected-source-commit-sha <EXACT_REFROZEN_SHA>

python manage.py audit_pilot_data_residency \
  --manifest /restricted/iamina/pilot-residency.json \
  --require-approved \
  --expected-source-commit-sha <EXACT_REFROZEN_SHA>

python manage.py audit_safety_corpus_review \
  --manifest /restricted/iamina/safety-review-manifest.json \
  --require-approved \
  --expected-source-commit-sha <EXACT_REFROZEN_SHA>
```

Then and only then: explicit human real-patient release decision.

## P5-7 — Observed pilot evidence

**Status:** ⚪ PENDING P5-6.

Collect real pilot MAU/activation/retention, safety incidents, reliability/offline/update failures, LLM route/cost and zero-model rate, storage/egress cost, satisfaction/support burden and clinically safe usefulness signals. Synthetic evidence cannot become P5-7 proof.

## P5-8 — Go / No-Go

**Status:** ⚪ PENDING P5-7.

No second disease capsule before this evidence-based decision gate.

**P5 whole-lot tracker:** 4/9 = 44.4%.  
**Canonical global atomic tracker:** 6/12 = 50.0% with P5-4A closed.

---

# 4. MENA / multimodal residuals

## P0-MENA-2 — Locale + safety contract

**Status:** 🟡 IMPLEMENTATION CLOSED / PRE_REAL_PATIENT_EVIDENCE DEFERRED.

Runtime locale/high-severity variant coverage is implemented and bound into the exact safety corpus. Remaining release-relevant work is external/restricted review evidence under #318/P5-6A, activated before real-patient use rather than treated as current implementation debt.

## P0-MENA-4 — Multimodal provider benchmark

**Status:** 🟡 DEFERRED / EXTERNAL-HUMAN EVIDENCE, issue #319.

Groq + `openai/gpt-oss-120b` remains the conversational candidate; no local Arabic full-document OCR primary qualifies under the current strict floor; native TTS evidence is deferred to P5-3; STT remains deferred by owner decision.

Retained MENA metric: 32/38 = 84.2%, informational only.

---

# 5. Parallel engineering debt

`docs/TECHDEBT.md` owns unresolved compromises; it is not a competing roadmap. Critical/high debt is promoted into the current engineering path only when the corresponding feature is active or a current defect is reproduced. Pre-real-patient compliance evidence remains a separate future release gate.

Reconciliation retained through 2026-09-17:

- TD-010 observability retention lifecycle is CLOSED by PR #610, merge `e9c04beee31638ff86d7fd0b50d5eddccc313c4e`, post-merge CI #4206 / workflow `34787203311` SUCCESS and migration drift #3742 SUCCESS;
- former TD-005 and TD-006 were removed from the unresolved-debt register because current runtime safety variant coverage is implemented and the only remaining release gate is the restricted human qualification/approval evidence already owned by #318/P5-6A;
- former TD-007 was removed after verifying the explicitly approved/documented `SELF_CARE_ONLY` pilot operating model: PR #24 formalized no human monitoring, mandatory disclosure and fail-closed evidence requirements for any future `MONITORED_HUMAN` mode; P0.6 PR #128 later centralized all patient-facing urgent responses through that policy;
- TD-008 device-level critical-flow coverage is CLOSED by PR #636 / merge `532376020d4696d4098994a97a764a1994c7f92f`; the dedicated integration baseline landed, the resolved debt was removed in `8d54168674c316ddcc64846384b0bcac72650fe4`, and handover `4e7b04a3387da68374e00ab858e63b914faa1884` retained the closeout;
- historical TD-013 authentication abuse protection is CLOSED by PR #623, merged as `main@f045491a3e07db388067fe54c60fd0c4b543e050`; exact-head CI #4238 and drift #3760 succeeded, then exact-main post-merge CI #4241 and drift #3761 succeeded. Tracker #622 is closed. The retained limiter is PostgreSQL-backed, covers login/registration/password-reset, is independent of Redis availability, stores HMAC-derived identifiers rather than raw IP/email, and has typed 429/recovery tests;
- TD-003 provider timeout/circuit-breaker/failure UX is CLOSED by backend breaker PR #628, frontend typed-error UX PR #629 and docs closeout PR #630. Exact-head #629 CI #4280, Companion E2E #98, UI browser #710, UI geometry #707 and missing-routes #66 succeeded; #630 exact-head CI #4291 and post-merge CI #4292 succeeded;
- TD-014 patient local app-lock/re-authentication is CLOSED by PR #649 / merge `df457cfdcc574439adb791fbfc44d484a1224417`; final candidate `fd5bc4392ceda6b411b72f3ceb9254119024ac5c` passed 15/15 workflows and its fresh WebAuthn/offline/visual artifact was inspected. TD-014 is removed from the unresolved debt register.
- TD-012 remains OPEN. AISummary phase 2 is merged by PR #689; DocumentImport remains CLOSED by PR #692; Companion remains CLOSED by PR #695. Reports is CLOSED by PR #698 / `6920c20b67af466ac69a1be292a9afcd3b17ca91`, reducing `reports_screen.dart` from ~29.0k to ~3.8k characters while retaining DB/stream/period orchestration in the state file. Exact-head CI #4599, browser #970, geometry #855, Offline UI #97 and P5-5 #354 succeeded. Visual comparison: 390×844 pixel-identical; 768×1024 and 1280×900 differed only in the time-dependent timestamp text (158 pixels each), with no geometry change; visual score 9.9/10. IAmina chat remains CLOSED by PR #671; Profile remains CLOSED by PR #675.

---

# 6. CI / cost optimization

CI-FRUGAL-2 / #442 remains parallel and non-blocking. Runner-cost work must not weaken retained visual certification or safety/security gates.

---

# 7. Repository hygiene

Open GitHub items are not automatically active roadmap work. Historical Companion/OCR evidence issues and stale PRs remain evidence/hygiene until current-main reproduction proves forward work. Stale issue/PR state never changes product status without code + tests + retained evidence.

---

# 8. Closed workstreams retained as history

Closed unless a new reproduced regression opens a scoped lot: Gate A Secure Core; P0 foundations; product truthfulness; agent governance; global UX/Dashboard/Journal convergence; outbound AI/data-egress foundation; current sovereign-auth migration work recorded as merged; Companion intelligence/proactivity convergence; CGM gateway V1/V1.1/V2/V2.1; P4-FRUGAL PRE-PILOT; P5-0; P5-1; P5-2; P5-4A; P5-5; the P5-6 consent-evidence engineering atomic sublot; and TD-014 strong local app-lock.

Closed does not imply legal/CNDP authorization, physical-device proof, real-patient authorization or production approval unless that exact evidence is retained.

---

# 9. Execution order

1. **Current engineering:** continue auditing remaining `docs/TECHDEBT.md` items for staleness and prioritize reproduced security/reliability/accessibility defects solvable with synthetic/non-patient data.
2. Continue product/UX/reliability/security engineering while preserving fail-closed real-patient boundaries, the local-first runtime contract and the merged strong local app-lock boundary.
3. **Before the first identifiable real-patient health data:** explicitly re-freeze the chosen exact release SHA, reactivate P5-6A #318 and P5-6B #320, freeze the actual patient runtime topology, enumerate only genuinely enabled processors, and collect genuine restricted evidence/approvals.
4. If the pilot requires any remote deployment/distribution change, obtain separate explicit owner authorization before that deployment. Development Vercel deployment remains separately authorization-gated and is not patient production proof.
5. Freeze the actual pilot topology/residency evidence after every authorized deployment/distribution step relevant to patient processing.
6. Run the three exact-SHA fail-closed audits.
7. Explicit human real-patient release decision.
8. Controlled PWA pilot.
9. P5-7 observed evidence.
10. P5-8 go/no-go.

No Vercel deployment is authorized by this execution order.

---

# 10. Canonical governance

- `docs/ROADMAP.md` owns all forward status, priority, sequencing and completion percentages.
- `docs/LOCAL_FIRST_RUNTIME_BOUNDARY.md` owns the patient-runtime vs remote-dev/cert architecture boundary and is subordinate only to an explicit later change in this roadmap.
- Overall progress is the atomic 12-lot metric. Its denominator changes only through an explicit roadmap governance change.
- `docs/TECHDEBT.md` owns unresolved compromises only.
- `AGENTS.md` owns execution rules only and is subordinate to this roadmap for status.
- Issues/PRs are execution/evidence containers, not canonical portfolio status.
- Assessments/handovers/ADRs are evidence/history, not forward authority.
- Never declare a lot closed from a title, branch, PR state or old score alone.
- No Vercel deployment without explicit owner authorization; technical deployment authorization never implies real-patient release.
- Deferring P5-6A/P5-6B does not waive them. The boundary is before the first identifiable real-patient health data enters IAMINA.

## Current canonical snapshot

- repo: `hraaaaf/IAMINA-MVP`
- main reconciled for this lot: `6920c20b67af466ac69a1be292a9afcd3b17ca91`
- P5-4A AUTH-LOCAL-FIRST: **CLOSED**, PR #639 merged as `bd13e8ad0c6f3ff2c4376b00c43fb8c54068d053`
- TD-014 strong local app-lock: **CLOSED**, PR #649 merged as `df457cfdcc574439adb791fbfc44d484a1224417`; final candidate `fd5bc4392ceda6b411b72f3ceb9254119024ac5c` had 15/15 SUCCESS
- last explicitly frozen P5-6 SHA: `fb42e4d641b7b057607fe6a2de3d5104ccf15d0b` — **historical freeze evidence, not current release candidate**
- current release candidate: **NONE / PENDING EXPLICIT REFREEZE**
- historical freeze proof: PRs #602/#603; #603 post-merge CI #4190 / workflow `34773613905`; post-merge drift #3737 / workflow `34773613814`
- patient production runtime boundary: **LOCAL-FIRST; Vercel/Django/Neon excluded unless a future explicit architecture change says otherwise**
- proven predecessor remote dev/cert deployment: `dpl_8ex2k82KaozE6Fxc8wQBYJuRU43y`, source `5b27a22fc5c05a06e7eeeb0e841bb0e7dadce7f6`, Python function, `cdg1`, health HTTP 200 / `db=ok`
- dedicated remote dev/cert database proof: Neon `IAMINA` / `square-sun-82359137`, PG16, `aws-eu-central-1`, branch `production`, migrations current for the predecessor remote deployment
- safety fingerprint retained from historical freeze: `823d109b0ddd10d1874eec53027eafd9d65884f14810304af3681c57c82cf7e5`
- qualification wording: **professionnels qualifiés** — owner attestation reference `issue-318:owner-attestation:professionnels-qualifies`
- consent notice: `2026-09-12.1`
- canonical global progress: **6/12 = 50.0% with P5-4A closed**
