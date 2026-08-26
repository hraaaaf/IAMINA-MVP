# IAmina — Roadmap

> **Last updated:** 2026-08-26 — Gate A Secure Core remains certified at 10.0/10. P4-FRUGAL PRE-PILOT is closed 10/10. PR #507 merged Companion multi-turn actionability at controlled synthetic 9.3/10 with deterministic organization routing and guarded SSE. The new forward execution lane is P5-PILOT / Pilot Readiness (#514). MENA critical-path arithmetic remains 32/38 because the P5 umbrella does not retroactively manufacture MENA evidence. P0-MENA-4 #319 remains blocked on retained external/human evidence. No Vercel deployment is authorized by this roadmap.
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

Canonical companion authority: `docs/COMPANION_INTELLIGENCE_CONTRACT.md`.

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
| Dashboard P7 — responsive convergence | 100% | ✅ Closed | PR #306; exact head `0775b9fd…`; CI #2751 + drift #2563 + UI #312 + P7 cert #7 + Chrome #289 green; merge `446c2763…`; closeout `docs/assessments/2026-08-17-dashboard-p7-responsive-convergence-closeout.md` |
| Journal metabolic-event redesign | 100% | ✅ Closed | P0-JOURNAL-1/2 + P1-JOURNAL-3/4/5/6/7 + P2-JOURNAL-8/9; PRs #67–#77 |
| P0-MENA-1 — outbound AI/data-egress contract | 100% | ✅ Merged | PRs #10–#15 |
| Canonical Clinical Data Layer & Privacy v1 | Runtime merged | ✅ Parallel maintenance foundation | PR #481 merge `bd84d147…`; exact-head CI #3424 + drift #3237 + Pulper #17 rerun green; residual universal free-form/raw-media de-identification remains TD-001; no MENA arithmetic change |
| P0-MENA-2 — locale + safety contract | 63% | 🟡 Native linguistic/parity evidence retained | English baseline 16/16 certified; #515 now formalizes the native/competent-speaker review gate; #318 remains `NOT_PLANNED` without claiming independent clinical-human approval |
| P0-MENA-3 — sovereign authentication migration | 100% | ✅ Merged | PR #17 |
| P0-MENA-4 — multimodal provider benchmark | 29% | 🟡 BLOCKED_EXTERNAL / HUMAN EVIDENCE | #319: Groq GPT-OSS primary conversational candidate frozen; Tesseract `ara` provisional bounded-field evidence; no local Arabic full-document primary qualifies; native TTS/device and linguistic evidence remain human gates |
| P4-FRUGAL PRE-PILOT | 100% | ✅ 10/10 closed | #422 closed; FRUG-0…9 pre-pilot evidence boundary retained; no real-pilot economics claim |
| P5-PILOT — Pilot Readiness | 1/9 = 11.1% | 🟡 Active | #514; P5-0 security reconciliation closed; P5-1 #515 active HUMAN_GATE |
| Pilot safety/compliance active scope | 100% | ✅ 10/10 retained active gates closed | Historical 10/13 completed; the three previously remaining external gates were de-scoped from the active engineering roadmap. This is scope reduction, not approval. Real-patient P5-6 must reopen whatever legal/governance evidence is actually required. |
| Companion intelligence / proactivity | P0 foundation + Clinical Twin + proactive lifecycle + P2-COMPANION-0..8 + P3/P4 convergence | ✅ Closed through current convergence closeout | PR #507 current Companion controlled synthetic audit 9.3/10; these lanes do not alter MENA arithmetic |
| CGM-GW-V1 — Dexcom + Libre ingestion gateway | 100% | ✅ Closed | Runtime PR #276 exact head `706225a4…`; exact-head CI #2568 + drift #2380 green; merge `f8a4ce7f…`; post-merge CI #2569 + drift #2381 green; closeout evidence `docs/assessments/2026-08-16-cgm-gateway-v1-closeout.md` |
| CGM-GW-V1.1 — LinX provenance via external bridge | 100% | ✅ Closed | Runtime PR #281 exact head `da7b2079…`; exact-head CI #2589 + drift #2401 green; merge `8eaadc36…`; post-merge CI #2590 + drift #2402 green; qualification `docs/assessments/2026-08-16-cgm-gateway-v1-1-linx-qualification.md` |
| CGM-GW-V2 — Product Wiring | 100% | ✅ Closed | Runtime PR #285 merge `8231be71…`; exact-head CI #2652 + drift #2464 + UI #265 + Chrome #230 green; post-merge CI #2653 + drift #2465 + UI #266 + Chrome #231 green; closeout `docs/assessments/2026-08-16-cgm-gateway-v2-closeout.md`; real-device proof remains a separate external gate |
| CGM-GW-V2.1 — Premium How to use | 100% | ✅ Closed | Runtime PR #294 merge `d6318790…`; exact-head CI #2684 + drift #2496 + UI #289 + Chrome #254 green; post-merge CI #2685 + Chrome #255 green; final dialog score 9.6/10; closeout `docs/assessments/2026-08-17-cgm-v2-1-how-to-use.md`; live physical-sensor proof remains a separate external gate |

**MENA critical-path completion (rebased active scope): 32 of 38 retained explicit MENA tasks closed, approximately 84.2%.**

Rebaseline arithmetic: the prior canonical denominator was 41 with 32 closed. The active roadmap removed exactly three unresolved external tasks from the denominator: one independent qualified-clinical-human gate (#318) and two release-compliance outcomes grouped under #320. No task was added to the numerator for those decisions. Therefore `32 / (41 - 3) = 32/38 ≈ 84.2%`.

`CLOSED_GRAY` means **not pursued in the active engineering roadmap**. It does not mean clinically approved, CNDP-authorized, legally compliant, processor-approved, residency-approved, or cleared for real-patient production. P5-6 explicitly reopens whatever real-patient release requirements are actually necessary before a patient pilot.

Gate A is an engineering certification over already-counted foundations and therefore does **not** change the MENA critical-path numerator. Canonical Clinical Data Layer & Privacy v1, clinical-intelligence, Dashboard, Journal, UX quality, P4-FRUGAL and the closed CGM gateway integration lanes are tracked separately unless a retained pilot gate explicitly depends on them.

---

# P5-PILOT — Pilot Readiness — ACTIVE

Canonical tracker: #514.

## Goal

Move IAMINA from certified pre-pilot engineering to one safe, measurable founder-selected MENA pilot cohort, with hard separation between engineering proof, human evidence and real-patient authorization.

## Lots

1. **P5-0 — Security reconciliation — CLOSED.** Reconcile stale security bookkeeping with #30 reachable-history certification; legacy #8 closed on 2026-08-26 with the owner-attestation boundary preserved.
2. **P5-1 — MENA linguistic certification — ACTIVE / HUMAN_GATE.** Native/competent-speaker review for FR, MSA, Moroccan Darija Arabic + Latin, FR↔Darija code-switching and retained Gulf registers. Contract: #515 and `docs/assessments/2026-08-26-p5-1-mena-linguistic-review-protocol.md`.
3. **P5-2 — Arabic OCR real-world evidence.** Controlled non-patient real-camera Arabic evidence. Tesseract `ara` remains provisional only where bounded-field evidence qualifies; no local Arabic full-document primary currently passes the strict numeric floor.
4. **P5-3 — Native TTS real-device evidence.** Real iOS/Android listening evidence; human gate.
5. **P5-4 — Pilot packaging.** Signed installable build, local-first persistence, update/migration/rollback, secret/code protection and reproducible installation without exposing the repo.
6. **P5-5 — End-to-end pilot rehearsal.** Non-patient rehearsal across onboarding, data/import, Companion, OCR, CGM, reports, offline/update/backup/restore and degraded modes.
7. **P5-6 — Real-patient release gate.** Reopen and satisfy the CNDP/legal/processor/residency/clinical-human requirements that are actually required for a patient pilot. Previous scope reductions are not approval.
8. **P5-7 — Observed pilot evidence.** Real MAU, retention, safety incidents, reliability, LLM route/cost, storage/egress, satisfaction and support burden. Synthetic evidence must remain labelled synthetic.
9. **P5-8 — Go / No-Go.** Decide whether IAMINA merits continued investment/expansion. No second disease capsule before this gate passes.

Execution order:

`P5-0 → P5-1/P5-2/P5-3 in parallel → P5-4 → P5-5 → P5-6 → P5-7 → P5-8`

CI-FRUGAL #442 is parallel infrastructure work and must not delay this path.

**Pilot Readiness progress: 1/9 = 11.1%.** This metric is separate from the 32/38 MENA numerator.

---

# Gate A — Secure Core — CERTIFIED 10.0/10

Gate A uses ten equally weighted, independently checkable secure-core dimensions. All ten now pass: API/session safety; deterministic clinical authority; high-risk refusal parity; emergency truthfulness; governed AI/data egress; minimization/DLP/raw-media consent; sovereign authentication; PostgreSQL/migration integrity; current-tree SAST/anti-bypass/secret hygiene; and reachable Git-history hygiene. Issue #30 removed `.claude/settings.local.json` from all reachable branch history and was fresh-clone verified after the force-update.

**Engineering certification:** **10.0/10**.  
**Reachable-history security blocker:** **CLOSED** by issue #30 remediation. Gate A still does not waive requirements that remain in active scope.

Canonical evidence: `docs/assessments/2026-08-14-gate-a-secure-core-certification.md`.