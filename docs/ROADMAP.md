# IAmina — Roadmap

> **Last updated:** 2026-08-17 — Gate A Secure Core is certified at 10.0/10 after issue #30 reachable Git-history remediation was completed and independently fresh-clone verified; the remaining real-patient pilot blockers are restricted linguistic/compliance/deployment approvals and live provider evidence. P3-EVALS is certified, human-reviewed PASS ALL, merged and post-merge green. Companion intelligence is closed through P3-EVALS. The P0-MENA-2 technical English baseline is certified complete across 16/16 active patient-facing surfaces; restricted human linguistic/parity gates remain open. CGM-GW-V1 is closed for Dexcom/Libre, CGM-GW-V1.1 is closed for explicit LinX provenance through an external Juggluco-to-Nightscout bridge, CGM-GW-V2 product wiring is closed for authenticated connection/sync/persistence/API/Flutter integration, and CGM-GW-V2.1 premium per-source How-to guidance is closed; these remain parallel integration lanes and do not alter the 32/41 MENA critical-path numerator. Medtronic remains HOLD pending a sufficiently canonical modern CareLink path. The active pilot critical path remains MENA pilot hardening. UX visual rebase remains closed through UX-11 at 9.8/10.
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
| Journal metabolic-event redesign | 100% | ✅ Closed | P0-JOURNAL-1/2 + P1-JOURNAL-3/4/5/6/7 + P2-JOURNAL-8/9; PRs #67–#77 |
| P0-MENA-1 — outbound AI/data-egress contract | 100% | ✅ Merged | PRs #10–#15 |
| P0-MENA-2 — locale + safety contract | 63% | 🟡 English technical gate closed; human review open | English baseline 16/16 certified in `docs/assessments/2026-08-14-english-baseline-completeness-certification.md`; PR #226 closes selection/persistence/ARB parity; three human linguistic/parity gates remain |
| P0-MENA-3 — sovereign authentication migration | 100% | ✅ Merged | PR #17 |
| P0-MENA-4 — multimodal provider benchmark | 29% | 🟡 Live runs externally blocked | PRs #18–#22 prepared execution paths |
| Pilot safety/compliance gate | 77% | 🟡 Restricted approvals remain | 10/13 explicit gates complete; issue #30 reachable-history remediation is closed and fresh-clone verified |
| Companion intelligence / proactivity | P0 foundation + Clinical Twin + proactive lifecycle + P2-COMPANION-0..8 + P3-HORIZON + P3-EVALS | ✅ Closed through P3-EVALS | P3-EVALS human PASS ALL; PR #204 merge `f508cccb…`; post-merge CI #2116 + drift #1928 green |
| CGM-GW-V1 — Dexcom + Libre ingestion gateway | 100% | ✅ Closed | Runtime PR #276 exact head `706225a4…`; exact-head CI #2568 + drift #2380 green; merge `f8a4ce7f…`; post-merge CI #2569 + drift #2381 green; closeout evidence `docs/assessments/2026-08-16-cgm-gateway-v1-closeout.md` |
| CGM-GW-V1.1 — LinX provenance via external bridge | 100% | ✅ Closed | Runtime PR #281 exact head `da7b2079…`; exact-head CI #2589 + drift #2401 green; merge `8eaadc36…`; post-merge CI #2590 + drift #2402 green; qualification `docs/assessments/2026-08-16-cgm-gateway-v1-1-linx-qualification.md` |
| CGM-GW-V2 — Product Wiring | 100% | ✅ Closed | Runtime PR #285 merge `8231be71…`; exact-head CI #2652 + drift #2464 + UI #265 + Chrome #230 green; post-merge CI #2653 + drift #2465 + UI #266 + Chrome #231 green; closeout `docs/assessments/2026-08-16-cgm-gateway-v2-closeout.md`; real-device proof remains a separate external gate |
| CGM-GW-V2.1 — Premium How to use | 100% | ✅ Closed | Runtime PR #294 merge `d6318790…`; exact-head CI #2684 + drift #2496 + UI #289 + Chrome #254 green; post-merge CI #2685 + Chrome #255 green; final dialog score 9.6/10; closeout `docs/assessments/2026-08-17-cgm-v2-1-how-to-use.md`; live physical-sensor proof remains a separate external gate |

**MENA critical-path completion:** 32 of 41 explicit MENA tasks closed, approximately **78%**.

Gate A is an engineering certification over already-counted foundations and therefore does **not** change the MENA critical-path numerator. The English technical baseline is a gate inside P0-MENA-2 rather than a new numbered MENA task, so its closure also does **not** change the 32/41 numerator. Clinical-intelligence, Journal, UX quality and the closed CGM gateway integration lanes are tracked separately and do not alter the MENA critical-path numerator unless a later pilot gate explicitly depends on them.

---

# Gate A — Secure Core — CERTIFIED 10.0/10

Gate A uses ten equally weighted, independently checkable secure-core dimensions. All ten now pass: API/session safety; deterministic clinical authority; high-risk refusal parity; emergency truthfulness; governed AI/data egress; minimization/DLP/raw-media consent; sovereign authentication; PostgreSQL/migration integrity; current-tree SAST/anti-bypass/secret hygiene; and reachable Git-history hygiene. Issue #30 removed `.claude/settings.local.json` from all reachable branch history and was fresh-clone verified after the force-update.

**Engineering certification:** **10.0/10**.  
**Reachable-history security blocker:** **CLOSED** by issue #30 remediation. Gate A still does not waive restricted compliance/deployment approvals, native-language safety review, or live provider evidence.

Canonical evidence: `docs/assessments/2026-08-14-gate-a-secure-core-certification.md`.
