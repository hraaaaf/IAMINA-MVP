# IAmina — Roadmap

> **Last updated:** 2026-09-11 — Gate A Secure Core remains certified at 10.0/10. P4-FRUGAL PRE-PILOT is closed 10/10. P5-1 exact-SHA linguistic review engineering packet is merged via #523 but native/competent human certification remains open. P5-2 real-camera Arabic OCR evidence is closed via #517 with a negative qualification result: Tesseract `ara` 2/6 Arabic normalized exact and 2/6 numeric exact; no local Arabic full-document primary qualifies. P5-3 native TTS real-device evidence remains a human-device gate but is not a packaging blocker for the PWA-first pilot unless the PWA scope explicitly requires that acoustic lane. P5-4 is now split: P5-4A PWA pilot packaging is the current critical path; P5-4B native Android/iOS signing/device alignment is deferred and non-blocking for the PWA pilot. P5-5 retained synthetic/non-patient end-to-end rehearsal is CLOSED via #552/#553 with exact-main post-merge rehearsal #34573137446 and CI #34573137452 green on `88b78e036ce3494dfe37921e70e064fbfdabd6bb`; artifact #10188573954 retained `PASS_WITH_BOUNDARIES`. P5-6 real-patient release preparation is ACTIVE / BLOCKED_EXTERNAL: #318 and #320 are reopened, the consent/processor, residency/transfer and clinical-corpus `--require-approved` audit commands are present in the current tree, but no external approval or real-patient authorization is claimed. Dashboard global responsive recertification has clean exact-head visual proof in run #34535253185: 9/9 required captures are decoded-pixel distinct and manually reviewed, with model UX/UI score 9.1/10. Pilot Readiness remains 3/9 = 33.3%; MENA arithmetic remains 32/38. No Vercel deployment is authorized by this roadmap.
>
> **Authority:** this file is the single **forward** tracker. Detailed implementation history belongs in git, merged PRs, ADRs, assessments and architecture documents.

## North star

Ship a **safe, measurable MENA diabetes companion** to one founder-selected pilot cohort, then use retention, safety and payer evidence to decide whether IAmina deserves expansion.

IAmina's intended product moat is **evidence-qualified longitudinal companion intelligence and proactive follow-up**, not a generic chatbot, not a virtual doctor and not autonomous treatment optimization.

## Product constraints

- One live condition: diabetes.
- MENA rollout is country-by-country and locale-by-locale.
- French, Modern Standard Arabic and English are baseline languages.
- Dialects require explicit selection, native review and safety parity.
- Location may suggest settings; it never silently determines language, consent, emergency resources or clinical behavior.
- IAmina is a **patient companion**, not a physician, diagnostic system, prescribing system or medical-consultation replacement.
- IAmina may observe, compare, explain and propose only bounded non-prescriptive next steps; the qualified clinician remains the medical decision authority.
- Deterministic clinical and safety logic decides; generative models may narrate only approved structured output.
- No diagnosis, differential diagnosis, prescription, dose calculation, treatment optimization/change or autonomous medical instruction.
- No second disease module before the retention gate passes.
- **Pilot delivery is PWA-first.** Native Android/iOS signing, provisioning and native device-update certification are deferred alignment work and do not block the PWA pilot unless the native lane is explicitly activated.

Canonical companion authority: `docs/COMPANION_INTELLIGENCE_CONTRACT.md`.
Canonical PWA-first release strategy: `docs/P5_PWA_FIRST_RELEASE_STRATEGY.md`.

---

# Progress dashboard

| Workstream | Progress | Status | Evidence |
|---|---:|---|---|
| Gate A — Secure Core engineering certification | 10.0/10 | ✅ Certified | Original rubric: `docs/assessments/2026-08-14-gate-a-secure-core-certification.md`; issue #30 remediation: `docs/assessments/2026-08-14-security-30-history-rewrite-certification.md`; legacy #8 reconciled/closed 2026-08-26 |
| P0 historical foundations | 100% | ✅ Merged | P0-A, P0-B, P0-C and migration drift |
| P0 product truthfulness | 100% | ✅ Closed | PRs #39–#43 |
| P0 agent governance | 100% | ✅ Closed | PR #63; Builder → Reviewer → Release Certifier protocol |
| P0 visual UX remediation | 100% | ✅ Closed | P0-UX-6 through P2-UX-14; PRs #53–#66 |
| UX visual rebase | 100% | ✅ Closed | UX-0–11; UX-11 reference parity 9.8/10; PR #110 |
| Dashboard P7 — responsive convergence | 100% | ✅ Closed | PR #306; exact head `0775b9fd…`; CI #2751 + drift #2563 + UI #312 + P7 cert #7 + Chrome #289 green; merge `446c2763…`; P7 closeout `docs/assessments/2026-08-17-dashboard-p7-responsive-convergence-closeout.md`. Global responsive recertification 2026-09-10: run #34535253185 SUCCESS on exact visual head `38e23b3…`, 9/9 decoded-pixel-distinct captures manually reviewed at 390×844 / 768×1024 / 1280×900, model UX/UI score 9.1/10; evidence `docs/assessments/2026-09-10-dashboard-global-certification-closeout.md`. |
| Journal metabolic-event redesign | 100% | ✅ Closed | P0-JOURNAL-1/2 + P1-JOURNAL-3/4/5/6/7 + P2-JOURNAL-8/9; PRs #67–#77 |
| P0-MENA-1 — outbound AI/data-egress contract | 100% | ✅ Merged | PRs #10–#15 |
| Canonical Clinical Data Layer & Privacy v1 | Runtime merged | ✅ Parallel maintenance foundation | PR #481 merge `bd84d147…`; exact-head CI #3424 + drift #3237 + Pulper #17 rerun green; residual universal free-form/raw-media de-identification remains TD-001; no MENA arithmetic change |
| P0-MENA-2 — locale + safety contract | 63% | 🟡 Native linguistic/parity evidence retained | English baseline 16/16 certified; #515 formalizes the native/competent-speaker review gate; #318 is reopened under P5-6 and remains `BLOCKED_EXTERNAL_HUMAN`, with no independent clinical-human approval claimed |
| P0-MENA-3 — sovereign authentication migration | 100% | ✅ Merged | PR #17 |
| P0-MENA-4 — multimodal provider benchmark | 29% | 🟡 BLOCKED_EXTERNAL / HUMAN EVIDENCE | #319: Groq GPT-OSS primary conversational candidate frozen; P5-2/#517 real-camera bounded Tesseract `ara` evidence FAIL (2/6 Arabic, 2/6 numeric); no local Arabic full-document primary qualifies; native TTS/device and linguistic evidence remain human gates |
| P4-FRUGAL PRE-PILOT | 100% | ✅ 10/10 closed | #422 closed; FRUG-0…9 pre-pilot evidence boundary retained; no real-pilot economics claim |
| P5-PILOT — Pilot Readiness | 3/9 = 33.3% | 🟡 Active / PWA-first | #514; P5-0 security reconciliation closed; P5-2 #517 evidence gate closed with negative OCR qualification; P5-5 #552/#553 retained rehearsal closed with exact-main `PASS_WITH_BOUNDARIES`; P5-1/#515 remains a human gate; P5-3/#518 remains a human-device gate but not a native-packaging blocker for the PWA-first pilot; P5-4A/#519 is the current PWA packaging critical path; P5-4B native Android/iOS alignment is deferred; P5-6 has reopened #318/#320 and remains `BLOCKED_EXTERNAL` with no real-patient authorization |
| Pilot safety/compliance active scope | Engineering foundations retained; external release approval pending | 🟠 BLOCKED_EXTERNAL | Historical engineering foundations remain retained, while P5-6 has reopened #318 qualified clinical-human review and #320 CNDP/processor/residency release evidence. This does not change the MENA numerator and is not real-patient approval. |
| Companion intelligence / proactivity | P0 foundation + Clinical Twin + proactive lifecycle + P2-COMPANION-0..8 + P3/P4 convergence | ✅ Closed through current convergence closeout | PR #507 current Companion controlled synthetic audit 9.3/10; these lanes do not alter MENA arithmetic |
| CGM-GW-V1 — Dexcom + Libre ingestion gateway | 100% | ✅ Closed | Runtime PR #276 exact head `706225a4…`; exact-head CI #2568 + drift #2380 green; merge `f8a4ce7f…`; post-merge CI #2569 + drift #2381 green; closeout `docs/assessments/2026-08-16-cgm-gateway-v1-closeout.md` |
| CGM-GW-V1.1 — LinX provenance via external bridge | 100% | ✅ Closed | Runtime PR #281 exact head `da7b2079…`; exact-head CI #2589 + drift #2401 green; merge `8eaadc36…`; post-merge CI #2590 + drift #2402 green; qualification `docs/assessments/2026-08-16-cgm-gateway-v1-1-linx-qualification.md` |
| CGM-GW-V2 — Product Wiring | 100% | ✅ Closed | Runtime PR #285 merge `8231be71…`; exact-head CI #2652 + drift #2464 + UI #265 + Chrome #230 green; post-merge CI #2653 + drift #2465 + UI #266 + Chrome #231 green; closeout `docs/assessments/2026-08-16-cgm-gateway-v2-closeout.md`; real-device proof remains a separate external gate |
| CGM-GW-V2.1 — Premium How to use | 100% | ✅ Closed | Runtime PR #294 merge `d6318790…`; exact-head CI #2684 + drift #2496 + UI #289 + Chrome #254 green; post-merge CI #2685 + Chrome #255 green; final dialog score 9.6/10; closeout `docs/assessments/2026-08-17-cgm-v2-1-how-to-use.md`; live physical-sensor proof remains a separate external gate |

**MENA critical-path completion (rebased active scope): 32 of 38 retained explicit MENA tasks closed, approximately 84.2%.**

Rebaseline arithmetic: the prior canonical denominator was 41 with 32 closed. The active roadmap removed exactly three unresolved external tasks from the denominator: one independent qualified-clinical-human gate (#318) and two release-compliance outcomes grouped under #320. No task was added to the numerator for those decisions. Therefore `32 / (41 - 3) = 32/38 ≈ 84.2%`.

`CLOSED_GRAY` means **not pursued in the active engineering roadmap**. It does not mean clinically approved, CNDP-authorized, legally compliant, processor-approved, residency-approved, or cleared for real-patient production. P5-6 explicitly reopens whatever real-patient release requirements are actually necessary before a patient pilot. Reopening those gates under P5-6 does not retroactively add them to the retained 32/38 MENA denominator.

Gate A is an engineering certification over already-counted foundations and therefore does **not** change the MENA critical-path numerator. Canonical Clinical Data Layer & Privacy v1, clinical-intelligence, Dashboard, Journal, UX quality, P4-FRUGAL and the closed CGM gateway integration lanes are tracked separately unless a retained pilot gate explicitly depends on them.

---

# P5-PILOT — Pilot Readiness — ACTIVE / PWA-FIRST

Canonical tracker: #514.
Canonical delivery strategy: `docs/P5_PWA_FIRST_RELEASE_STRATEGY.md`.

## Goal

Move IAMINA from certified pre-pilot engineering to one safe, measurable founder-selected MENA pilot cohort using the PWA as the immediate delivery surface, with hard separation between engineering proof, human evidence and real-patient authorization. Native Android/iOS alignment follows later and does not block the PWA pilot unless explicitly activated.

## Lots

1. **P5-0 — Security reconciliation — CLOSED.** Reconcile stale security bookkeeping with #30 reachable-history certification; legacy #8 closed on 2026-08-26 with the owner-attestation boundary preserved.
2. **P5-1 — MENA linguistic certification — ACTIVE / HUMAN_GATE.** Exact-SHA 10-lane engineering packet merged via #523 and machine-green; native/competent-speaker review remains required under #515.
3. **P5-2 — Arabic OCR real-world evidence — CLOSED.** #517 closed 2026-08-27 after controlled non-patient real-camera evidence returned Tesseract `ara` FAIL: 2/6 Arabic normalized exact and 2/6 numeric exact. Numeric floor unchanged; local full-document Arabic remains `UNQUALIFIED`. Closeout: `docs/assessments/2026-08-27-p5-2-arabic-real-camera-ocr-closeout.md`.
4. **P5-3 — Native TTS real-device evidence — ACTIVE / HUMAN_DEVICE_GATE / NON-BLOCKING FOR PWA PACKAGING.** Engineering listening packet merged via #525; current iOS + Android acoustic listening evidence remains required under #518 for any claimed native TTS adequacy. This gate does not force native app packaging into the immediate PWA-first delivery path unless the PWA pilot explicitly depends on that acoustic lane.
5. **P5-4 — Pilot packaging — ACTIVE / PWA_FIRST.** Split under #519. **P5-4A PWA pilot packaging** is the current critical path and must prove exact-SHA reproducible build, mobile-browser installability, local/offline data preservation across supported updates, recovery/forward-fix behavior, no repository/developer access, no client-secret exposure and retained target-browser/device evidence. **P5-4B native Android/iOS alignment** retains permanent signing/provisioning, signed artifacts and native real-device update evidence, but is deferred and non-blocking for the PWA pilot. Canonical strategy: `docs/P5_PWA_FIRST_RELEASE_STRATEGY.md`.
6. **P5-5 — End-to-end pilot rehearsal — CLOSED.** Clean current-main replay merged via #552. Exact-main post-merge proof: `88b78e036ce3494dfe37921e70e064fbfdabd6bb`, rehearsal #34573137446 SUCCESS, CI #34573137452 SUCCESS, artifact #10188573954, digest `sha256:4e2b923ea948d99702bac4b37d65e9d9f1f471ca0bfdb1022bab2a9deb317139`, retained result `PASS_WITH_BOUNDARIES`. Machine PASS lanes: onboarding, data/import, Companion, CGM, deterministic local report PDF, offline/sync, backup/restore and degraded modes. Arabic local full-document OCR primary remains `QUALIFIED_NEGATIVE`; update/physical install, physical Android device, live physical CGM sensor and production signing/distribution remain explicit `EXTERNAL` boundaries. Canonical closeout: `docs/assessments/2026-09-11-p5-5-end-to-end-pilot-rehearsal-closeout.md` merged via #553.
7. **P5-6 — Real-patient release gate — ACTIVE / BLOCKED_EXTERNAL.** #318 qualified clinical-human review and #320 CNDP/processor/residency release evidence are reopened. Current-tree fail-closed commands `audit_pilot_consent_governance --require-approved`, `audit_pilot_data_residency --require-approved` and `audit_safety_corpus_review --require-approved` are verified present, but no approved restricted manifests or external release decision are claimed. Release posture remains `NOT_RELEASE_AUTHORIZED`. Canonical gate: `docs/P5_6_REAL_PATIENT_RELEASE_GATE.md`.
8. **P5-7 — Observed pilot evidence.** Real MAU, retention, safety incidents, reliability, LLM route/cost, storage/egress, satisfaction and support burden. Synthetic evidence must remain labelled synthetic.
9. **P5-8 — Go / No-Go.** Decide whether IAMINA merits continued investment/expansion. No second disease capsule before this gate passes.

Current critical path:

`P5-0 → P5-1/P5-2/P5-3 evidence as applicable → P5-4A PWA → P5-5 → P5-6 → P5-7 → P5-8`

Deferred native alignment lane:

`P5-4B Android/iOS signing + provisioning + native real-device install/update evidence` before any native pilot or public native release claim.

CI-FRUGAL #442 is parallel infrastructure work and must not delay this path.

**Pilot Readiness progress: 3/9 = 33.3%.** Closed lots: P5-0, P5-2 and P5-5. PWA-first re-prioritization changes sequencing, not arithmetic. P5-6 remains blocked on external/human release evidence and therefore does not increment the closed count. This metric is separate from the 32/38 MENA numerator.

---

# Gate A — Secure Core — CERTIFIED 10.0/10

Gate A uses ten equally weighted, independently checkable secure-core dimensions. All ten now pass: API/session safety; deterministic clinical authority; high-risk refusal parity; emergency truthfulness; governed AI/data egress; minimization/DLP/raw-media consent; sovereign authentication; PostgreSQL/migration integrity; current-tree SAST/anti-bypass/secret hygiene; and reachable Git-history hygiene. Issue #30 removed `.claude/settings.local.json` from all reachable branch history and was fresh-clone verified after the force-update.

**Engineering certification:** **10.0/10**.  
**Reachable-history security blocker:** **CLOSED** by issue #30 remediation. Gate A still does not waive requirements that remain in active scope.

Canonical evidence: `docs/assessments/2026-08-14-gate-a-secure-core-certification.md`.