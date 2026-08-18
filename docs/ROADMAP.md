# IAmina — Roadmap

> **Last updated:** 2026-08-18 — Gate A Secure Core remains certified at 10.0/10. The founder has explicitly de-scoped the independent qualified-clinical-human gate tracked by #318 and has kept the CNDP/processor/Morocco-residency release gate #320 in `CLOSED_GRAY` / `NOT_PLANNED` status for the active engineering roadmap. These are removals from active scope, not successful clinical review, CNDP authorization, processor approval, residency approval or real-patient legal clearance. PR #328 records the application-owner/safety-owner A/B/C/D review. Live multimodal provider evidence remains the principal external MENA critical-path blocker. Companion intelligence is closed through P3/P4 convergence. CGM gateway lanes remain parallel and do not alter the MENA numerator.
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
| Gate A — Secure Core engineering certification | 10.0/10 | ✅ Certified | Original rubric: `docs/assessments/2026-08-14-gate-a-secure-core-certification.md`; issue #30 remediation: `docs/assessments/2026-08-14-security-30-history-rewrite-certification.md` |
| P0 historical foundations | 100% | ✅ Merged | P0-A, P0-B, P0-C and migration drift |
| P0 product truthfulness | 100% | ✅ Closed | PRs #39–#43 |
| P0 agent governance | 100% | ✅ Closed | PR #63; Builder → Reviewer → Release Certifier protocol |
| P0 visual UX remediation | 100% | ✅ Closed | P0-UX-6 through P2-UX-14; PRs #53–#66 |
| UX visual rebase | 100% | ✅ Closed | UX-0–11; UX-11 reference parity 9.8/10; PR #110 |
| Dashboard P7 — responsive convergence | 100% | ✅ Closed | PR #306; exact head `0775b9fd…`; CI #2751 + drift #2563 + UI #312 + P7 cert #7 + Chrome #289 green; merge `446c2763…`; closeout `docs/assessments/2026-08-17-dashboard-p7-responsive-convergence-closeout.md` |
| Journal metabolic-event redesign | 100% | ✅ Closed | P0-JOURNAL-1/2 + P1-JOURNAL-3/4/5/6/7 + P2-JOURNAL-8/9; PRs #67–#77 |
| P0-MENA-1 — outbound AI/data-egress contract | 100% | ✅ Merged | PRs #10–#15 |
| P0-MENA-2 — locale + safety contract | 63% | 🟡 Independent clinical gate de-scoped; remaining linguistic/parity work retained | English baseline 16/16 certified; PR #328 records owner/safety-owner A/B/C/D review; #318 closed `NOT_PLANNED` without claiming clinical-human approval |
| P0-MENA-3 — sovereign authentication migration | 100% | ✅ Merged | PR #17 |
| P0-MENA-4 — multimodal provider benchmark | 29% | 🟡 Live runs externally blocked | PRs #18–#22 prepared execution paths; #319 remains the active live-evidence gate |
| Pilot safety/compliance active scope | 100% | ✅ 10/10 retained active gates closed | Historical 10/13 completed; the three previously remaining external gates are now de-scoped from the active roadmap: #318 qualified-clinical review and #320's two CNDP/processor/residency outcomes. This is scope reduction, not approval. |
| Companion intelligence / proactivity | P0 foundation + Clinical Twin + proactive lifecycle + P2-COMPANION-0..8 + P3/P4 convergence | ✅ Closed through current convergence closeout | Current main includes P3/P4 convergence closeout; these lanes do not alter MENA arithmetic |
| CGM-GW-V1 — Dexcom + Libre ingestion gateway | 100% | ✅ Closed | Runtime PR #276 exact head `706225a4…`; exact-head CI #2568 + drift #2380 green; merge `f8a4ce7f…`; post-merge CI #2569 + drift #2381 green; closeout evidence `docs/assessments/2026-08-16-cgm-gateway-v1-closeout.md` |
| CGM-GW-V1.1 — LinX provenance via external bridge | 100% | ✅ Closed | Runtime PR #281 exact head `da7b2079…`; exact-head CI #2589 + drift #2401 green; merge `8eaadc36…`; post-merge CI #2590 + drift #2402 green; qualification `docs/assessments/2026-08-16-cgm-gateway-v1-1-linx-qualification.md` |
| CGM-GW-V2 — Product Wiring | 100% | ✅ Closed | Runtime PR #285 merge `8231be71…`; exact-head CI #2652 + drift #2464 + UI #265 + Chrome #230 green; post-merge CI #2653 + drift #2465 + UI #266 + Chrome #231 green; closeout `docs/assessments/2026-08-16-cgm-gateway-v2-closeout.md`; real-device proof remains a separate external gate |
| CGM-GW-V2.1 — Premium How to use | 100% | ✅ Closed | Runtime PR #294 merge `d6318790…`; exact-head CI #2684 + drift #2496 + UI #289 + Chrome #254 green; post-merge CI #2685 + Chrome #255 green; final dialog score 9.6/10; closeout `docs/assessments/2026-08-17-cgm-v2-1-how-to-use.md`; live physical-sensor proof remains a separate external gate |

**MENA critical-path completion (rebased active scope): 32 of 38 retained explicit MENA tasks closed, approximately 84%.**

Rebaseline arithmetic: the prior canonical denominator was 41 with 32 closed. The active roadmap now removes exactly three unresolved external tasks from the denominator: one independent qualified-clinical-human gate (#318) and two release-compliance outcomes grouped under #320 (CNDP/processor approval and Morocco cross-border/data-residency approval). No task was added to the numerator for these decisions. Therefore `32 / (41 - 3) = 32/38 ≈ 84.2%`.

`CLOSED_GRAY` means **not pursued in the active engineering roadmap**. It does not mean clinically approved, CNDP-authorized, legally compliant, processor-approved, residency-approved, or cleared for real-patient production. If real-patient release later requires those guarantees, the relevant legal/compliance gates must be reopened with real evidence.

Gate A is an engineering certification over already-counted foundations and therefore does **not** change the MENA critical-path numerator. Clinical-intelligence, Dashboard, Journal, UX quality and the closed CGM gateway integration lanes are tracked separately and do not alter the MENA critical-path numerator unless a later retained pilot gate explicitly depends on them.

---

# Gate A — Secure Core — CERTIFIED 10.0/10

Gate A uses ten equally weighted, independently checkable secure-core dimensions. All ten now pass: API/session safety; deterministic clinical authority; high-risk refusal parity; emergency truthfulness; governed AI/data egress; minimization/DLP/raw-media consent; sovereign authentication; PostgreSQL/migration integrity; current-tree SAST/anti-bypass/secret hygiene; and reachable Git-history hygiene. Issue #30 removed `.claude/settings.local.json` from all reachable branch history and was fresh-clone verified after the force-update.

**Engineering certification:** **10.0/10**.  
**Reachable-history security blocker:** **CLOSED** by issue #30 remediation. Gate A still does not waive requirements that remain in active scope.

Canonical evidence: `docs/assessments/2026-08-14-gate-a-secure-core-certification.md`.
