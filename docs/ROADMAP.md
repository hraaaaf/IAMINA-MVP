# IAmina — Roadmap

> **Last updated:** 2026-08-09 — metabolic-event Journal redesign registered; P0-JOURNAL-1 clinical truthfulness is the first merge unit and P0-JOURNAL-2 is next.
>
> **Authority:** this file is the single forward tracker. Detailed implementation history belongs in git, ADRs and architecture documents.

## North star

Ship a **safe, measurable MENA diabetes companion** to one founder-selected pilot cohort, then use retention, safety and payer evidence to decide whether IAmina deserves expansion.

## Product constraints

- One live condition: diabetes.
- MENA rollout is country-by-country and locale-by-locale.
- French, Modern Standard Arabic and English are baseline languages.
- Dialects require explicit selection, native review and safety parity.
- Location may suggest settings; it never silently determines language, consent, emergency resources or clinical behavior.
- IAmina is a companion, not a diagnostic or prescribing system.
- Deterministic clinical and safety logic decides; external models receive only approved minimized data.
- No second disease module before the retention gate passes.

---

# Progress dashboard

| Workstream | Progress | Status | Evidence |
|---|---:|---|---|
| P0 historical foundations | 100% | ✅ Merged | P0-A, P0-B, P0-C and migration drift |
| P0 product truthfulness | 100% | ✅ Closed | PRs #39–#43; five executable UX truthfulness contracts |
| P0 agent governance | 100% | ✅ Ready for certification | PR #63; Builder → Reviewer → Release Certifier protocol, 6 role briefs and 6 reusable skills |
| P0 visual UX remediation | 100% | ✅ Closed | P0-UX-6 through P2-UX-14 certified; PRs #53–#66; final density/polish recertification run `31267173791` |
| Journal metabolic-event redesign | 11% | 🔵 P0-JOURNAL-1 merge unit | PR #67; truthful glucose/nutrition/insulin capture; P0-JOURNAL-2 next |
| P0-MENA-1 — outbound AI/data-egress contract | 100% | ✅ Merged | PRs #10–#15 |
| P0-MENA-2 — locale + safety contract | 63% | 🟡 Native review blocked | PR #16, RTL certification PR #36 and review-package PR #37; three human linguistic/parity gates remain |
| P0-MENA-3 — sovereign authentication migration | 100% | ✅ Merged | PR #17, merge `185f680` |
| P0-MENA-4 — multimodal provider benchmark | 29% | 🟡 All execution paths prepared; live runs blocked | Framework PR #18; text/STT/vision preparation PRs #19–#22 |
| Pilot safety/compliance gate | 69% | 🟡 Automated procedures complete; external security/legal/human gates remain | 9 of 13 explicit gates complete; PRs #34–#35 prepare approval gates; PR #38 prepares secret-history remediation; issue #30 remains blocking |

**MENA critical-path completion:** 32 of 41 explicit roadmap tasks closed, approximately **78%**.

The Journal redesign is a separate product-quality workstream and does not change the MENA critical-path numerator.

Preparation work does not close a live benchmark, legal/privacy approval, native-review task or external credential-remediation task and does not increase the critical-path numerator.

---

# Completed P0 ledger

## ✅ P0-A — API safety boundaries

- CSRF retained for session/cookie writes.
- Bearer/bootstrap behavior supported.
- Diabetes routes covered by unit guards.
- Unexpected normalization failures fail closed.
- Deterministic triage remains authoritative.

## ✅ P0-B — Server-side AI egress authorization

- Central provider-agnostic patient/purpose/modality boundary.
- Consent checked immediately before egress.
- Text, audio, vision/OCR, documents, chat and summaries wired.
- CI prevents unauthorized provider callsites.

## ✅ P0-C — Clinical analytics and PostgreSQL parity

- GRI corrected against the normative disjoint-zone formula.
- Patient-facing GRI fails closed until CGM coverage is valid.
- SQLite/PostgreSQL analytics parity established.
- PostgreSQL 16 full-suite CI is permanent.

## ✅ P0 migration drift

- Migration state reconciled without unnecessary ALTER operations.
- `makemigrations --check --dry-run` is a permanent CI gate.

## ✅ P0 agent governance

- `AGENTS.md`, `CLAUDE.md` and `docs/CONTRIBUTING.md` require a Builder → applicable Reviewer(s) → Release Certifier chain for every future roadmap LOT, P-level remediation, hotfix and governance change.
- Six role briefs live under `.agents/`; six reusable procedures live under `.skills/`.
- Reviewer routing is explicit by change surface; the Builder may not self-certify.
- Exact-head evidence becomes stale when code or canonical documentation changes and must be rerun.
- Expected-head merge locking and post-merge CI + migration drift are required before a LOT can be declared 100% complete.

**Closure unit:** PR #63. This governance work does not change the MENA critical-path numerator.

## ✅ P0 product truthfulness

- Real actions and the complete local CRUD loop are permanently certified.
- Synchronization and storage labels derive from real typed state.
- Clinical metrics disclose method, coverage and limitations without fabricated precision.
- Mobile Importer and the document picker are certified on narrow and short viewports.
- Privacy wording is deployment-aware in FR/EN/AR and fails closed before external document processing.
- Permanent Flutter contracts prevent regression of all five requirements.

**Closure:** PRs #39–#43. This workstream is separate from the MENA critical-path numerator.

---

# Journal metabolic-event redesign — ACTIVE

**Goal:** turn the add-log surface into a fast, truthful metabolic-event journal that records what happened, keeps treatment decisions out of the UI, and can later support evidence-backed personal response patterns without fabricated precision.

## Mandatory execution rule

Each Journal LOT is a separate branch/PR. Clinical/safety, UX/UI, privacy/egress and persistence reviewers are routed according to the touched surface. UX/UI LOTs require the repository UX certification procedure and a final score strictly above 9.0/10. A clinical safety LOT may not be expanded merely to chase visual polish; its visible behavior must remain usable and non-regressive, while the dedicated UX LOT owns full visual certification.

| LOT | Scope | Status | Acceptance boundary |
|---|---|---|---|
| P0-JOURNAL-1 | Clinical truthfulness | 🔵 PR #67 merge unit | no fabricated default glucose/target verdict; no fabricated carbs/IG/meal-impact score; insulin is already-taken logging only; deterministic `<54` vs `54–69` low-glucose safety; no automatic generative post-save verdict |
| P0-JOURNAL-2 | Express metabolic event | ⏭️ Next | `glycaemia → context → optional meal → save`; glycaemic context separate from meal type; Sport removed from meal taxonomy; FR/EN/AR + RTL/responsive certification >9.0 |
| P1-JOURNAL-3 | Meal capture | ⬜ Planned | recent/habitual/search + confirmed photo recognition; no “food recommendation” implication; user confirms/corrects media recognition |
| P1-JOURNAL-4 | Nutrition data v2 | ⬜ Planned | sourced food/portion model, provenance and uncertainty; Morocco/MENA portions; no patient-facing nutrition number without defensible source |
| P1-JOURNAL-5 | Insulin logging v2 | ⬜ Planned | actual administered dose/context only; no calculator, scoring, optimization or suggested units |
| P1-JOURNAL-6 | Context intelligence | ⬜ Planned | optional illness/stress/activity/sleep context; avoid repeatedly asking low-value information |
| P1-JOURNAL-7 | Ramadan mode v2 | ⬜ Planned | Ramadan becomes a profile/period context; meal vocabulary adapts automatically; no per-log pseudo-clinical toggle |
| P2-JOURNAL-8 | Personal metabolic response | ⬜ Planned | repeated-event associations with explicit evidence count/confidence; observational wording only; no invented causality/treatment advice |
| P2-JOURNAL-9 | Post-save experience | ⬜ Planned | immediate factual confirmation only; longitudinal insights appear separately only when evidence requirements are met |

### P0-JOURNAL-1 durable closeout contract

PR #67 is the merge unit for the first Journal LOT. Its code removes fabricated clinical/nutritional precision from the reachable add-log surface, preserves Drift persistence and `client_uuid`, distinguishes ADA 2026 level-2 `<54 mg/dL` from level-1 `54–69 mg/dL` before persistence, and removes the automatic post-save generative opinion. OCR, meal-photo recognition, voice dictation, richer nutrition, profile-level Ramadan behavior and longitudinal personalization are intentionally not claimed by this LOT; they return only through their dedicated units and existing egress/safety contracts.

P0-JOURNAL-1 is not declared 100% merely by this roadmap entry: expected-head merge plus post-merge CI and migration drift remain mandatory. P0-JOURNAL-2 must branch from the verified merged main.

---

# P0 visual UX remediation — CLOSED

Canonical defect register and acceptance criteria: `docs/ux/P0_CERT_4_VISUAL_AUDIT.md`.

## Mandatory per-LOT UX/UI quality gate

Every UX/UI LOT must finish with all of the following before it may be marked `100% ✅`:

1. inspect the real implementation and acceptance criteria before changing code;
2. run the relevant automated gates and review the final diff;
3. recapture or exercise the affected user journeys on the required viewport/locale matrix;
4. perform a documented visual/functional double-check against the LOT objective;
5. assign a final UX/UI score based on the real evidence, not on implementation completion alone;
6. if the score is **not strictly above 9.0/10**, continue correcting the same LOT and recertify until it exceeds 9.0/10;
7. update `docs/ROADMAP.md` with the delivered work, evidence, score, merge and next LOT before declaring the LOT closed.

A critical or high-severity unresolved defect prevents a score above 9/10 regardless of the arithmetic average.

## Current UX execution status

| LOT | Scope | Progress | Quality / evidence | Status |
|---|---|---:|---|---|
| P0-UX-6 | Arabe / RTL / i18n | 100% | Closed through PRs #53–#56; canonical ARB source, localized onboarding, deterministic locale resolution, RTL/accessibility contracts | ✅ |
| P0-UX-7 | Desktop / tablette | 100% | **9.3/10** after double-check; PR #57; merge `0a098d8b157c8d030e4d2ed8a6b4b8fcd895cccb`; CI #1062 and drift #878 green; 10-view recertification run `31166646157` with zero page errors | ✅ |
| P0-UX-8 | Navigation mobile | 100% | **9.4/10** after double-check; PR #59; CI #1075 and drift #891 green; 10-view 390×844 FR/AR recertification run `31182127159`, artifact `8995273847`, zero page errors | ✅ |
| P0-UX-9 | Petit écran 360×560 | 100% | **9.2/10** after second visual double-check; PR #60; CI #1092 + drift #908 green; 10-view FR/AR recertification run `31208830202`, artifact `9005910951`, zero page errors | ✅ |
| P0-UX-10 | Importer / document | 100% | **9.4/10** after second visual double-check; PR #61; one primary Importer entry; 16-view FR/AR recertification run `31224557639`, artifact `9011673527`, zero page errors | ✅ |
| P0-UX-11 | Dashboard premier utilisateur | 100% | **9.3/10** after second post-patch visual double-check; PR #62; truthful loading/error/empty/offline states; 8-view FR/AR recertification run `31248641421`, artifact `9019314222`, zero page errors | ✅ |
| P1-UX-12 | Profil progressif | 100% | **9.4/10** after Reviewer double-check; PR #64; three truthful progressive sections; 8-view FR/AR recertification run `31258575687`, artifact `9022145295`, zero page errors | ✅ |
| P1-UX-13 | Wording médical et produit | 100% | **9.3/10** after second visual recertification; PR #65; plain-language CGM/AGP + privacy wording; 32-view FR/AR run `31263898750`, artifact `9023631718`, zero page errors | ✅ |
| P2-UX-14 | Densité et polish | 100% | **9.2/10** after Reviewer double-check; 40-view FR/AR final matrix run `31267173791`, artifact `9024558783`, zero page errors | ✅ |

The visual UX remediation workstream is complete. Detailed implementation history and rejected-baseline narratives remain available in git and PRs #53–#66 rather than being expanded further in this forward tracker.

---

# P0-MENA-1 — Outbound AI/data-egress contract — MERGED

- [x] Text payload allowlist and minimization.
- [x] Deterministic semantic DLP.
- [x] Granular raw-media consent.
- [x] Authenticated patient consent management.
- [x] Executable processor-policy registry.
- [x] Typed provider failures and bounded timeouts.
- [x] Stable non-sensitive API error contract.
- [x] Deterministic Flutter failure UX.
- [x] Safe stream cancellation and partial-failure handling.
- [x] Exhaustive synchronous, streaming and multimodal non-bypass proof.

**Merge:** PR #15. All SQLite, PostgreSQL, migration, OpenAPI, security and Flutter gates passed.

---

# P0-MENA-2 — Locale + safety contract — PARTIAL

## Closed

- [x] Separate country, UI language, response language, script/transliteration, dialect, units and timezone.
- [x] Require explicit user confirmation; location only suggests.
- [x] Deterministic fallback to MSA, English or French.
- [x] Versioned Morocco emergency-resource registry with confirmed-country-only selection.
- [x] Complete technical RTL coverage screen by screen. **PR #36 registers every routed screen and shell, replaces physical left/right primitives with directional equivalents, proves Arabic `TextDirection.rtl`, and makes Flutter tests a permanent CI gate.**

## Remaining human-language gates

- [ ] Obtain native-speaker approval for every enabled safety corpus. **PR #37 exports the exact fingerprinted corpus and requires one opaque qualified-review reference per enabled locale.**
- [ ] Close remaining Darija high-severity orthographic variants through native review. **PR #37 binds every exact Darija phrase recognized by the classifier to a stable mandatory case ID.**
- [ ] Approve safety parity across text, voice transcript, mixed language and transliteration. **PR #37 derives and enforces every represented locale/channel/input-form review tuple.**

Automated corpus, route coverage and directionality groundwork is green. `audit_safety_corpus_review --require-approved` remains fail-closed until current restricted native, clinical and safety-owner evidence covers the exact corpus fingerprint.

---

# P0-MENA-3 — Sovereign authentication migration — MERGED

## Delivered

- [x] Django-owned registration, login and logout.
- [x] Signed, expiring IAMINA bearer tokens.
- [x] Server-side global token revocation.
- [x] Password establishment and enumeration-safe native recovery.
- [x] Native password-reset deep-link UX in Flutter.
- [x] Controlled Firebase-to-Django migration boundary.
- [x] No silent merge by email.
- [x] Explicit Firebase identity link and unlink.
- [x] Collision handling, readiness audit and executable rollback contract.
- [x] IAMINA-native-first Flutter initialization and secure token storage.
- [x] SQLite/PostgreSQL migrations `0011` and `0012` reconciled.
- [x] Temporary diagnostic and application workflows removed.

## Permanent operational gates

```bash
python manage.py audit_auth_migration
python manage.py audit_auth_migration --require-zero-firebase
```

The first command measures migration readiness. The second is the final gate before removing the remaining Firebase migration bridge and runtime dependencies.

**Validation before merge:** SQLite, PostgreSQL 16, migration drift, Ruff, import-linter, anti-bypass checks, Bandit, OpenAPI, Flutter analyze and secret hygiene all green.

**Merge:** PR #17, merge commit `185f68008179de76ebcd7b99f9d9ef17e8e6f5c3`.

---

# P0-MENA-4 — Multimodal provider benchmark — PREPARED, LIVE RUNS DEFERRED

**Goal:** select text, STT and vision providers using evidence rather than configuration convenience.

- [x] Build representative minimized and synthetic evaluation sets. **Strict contracts, stable fingerprints, modality/locale coverage and identity-data rejection are green in PR #18.**
- [x] Define scoring for privacy, residency, no-training/no-retention terms, MENA quality, safety, latency, availability and cost. **Safety/privacy hard floors, evidence expiry, deterministic judges, versioned reports and fail-closed cutover are green in PR #18.**
- [ ] Benchmark text providers independently.
- [ ] Benchmark STT providers independently.
- [ ] Benchmark vision/OCR providers independently.
- [ ] Document the evidence-backed decision matrix and rejected alternatives.
- [ ] Approve provider cutover only after privacy, quality and human-review gates pass.

## Preparation checkpoint

- **Framework merged:** PR #18.
- **Text execution boundary merged:** PR #19.
- **STT execution boundary merged:** PR #20.
- **Vision/OCR execution boundary merged:** PR #21.
- **Cutover package merged:** readiness aggregation and execution runbook delivered in PR #22.
- **Live work deferred:** exact providers, models, regions, credentials, contractual evidence, budgets and human reviews remain external prerequisites.

No provider score, decision or production approval may be inferred from preparation status.

---

# Pilot safety/compliance gate — before one real patient

- [x] Prove insulin-dose and treatment requests are refused deterministically without a generative chat LLM call. **PR #23 covers sync chat, SSE and post-STT voice paths across FR/EN/AR/Darija.**
- [x] Prove doctor-facing and summary outputs pass the same no-prescription policy. **PR #23 recursively sanitizes generated and fallback structures and verifies observation-only OCR schemas.**
- [x] Route emergencies to a monitored human channel or formally adopt a documented self-care-only mode. **PR #24 adopts truthful `SELF_CARE_ONLY` behavior and prevents false claims of automatic human monitoring.**
- [ ] Close Darija high-severity review. **The exact-variant review gate is prepared in PR #37; no human approval is recorded in source control.**
- [x] Enforce base AI/model consent server-side.
- [x] Expose granular raw-media consent through the authenticated patient API.
- [ ] Approve the pilot consent matrix and processor/subprocessor register. **PR #34 provides the complete executable matrix, processor evidence registry and fail-closed `--require-approved` command; restricted CNDP, contract, privacy and security approvals remain external.**
- [ ] Document and approve cross-border and data-residency assumptions for the pilot country. **PR #35 provides the exact-flow deployment manifest schema and fail-closed release command; the restricted manifest for the actual deployed SHA remains external.**
- [x] Implement data export or document a valid operational export process. **PR #25 provides ownership-scoped, audited, mode-0600 JSON export with deterministic integrity evidence.**
- [x] Define retention and deletion schedules. **PR #26 provides a versioned schedule, policy audit, staged-export purge and guarded transactional account deletion.**
- [x] Approve incident-response and escalation procedures. **PR #27 provides the SEV1–SEV4 matrix, mandatory roles, minimized incident records and tabletop requirements.**
- [x] Approve pilot onboarding, monitoring, escalation and exit checklists. **PR #28 provides a versioned registry, restricted cohort packet and fail-closed completion validator.**
- [ ] Prove no committed or reachable secrets remain and rotate any exposed keys. **PR #38 provides the full-history scanner, synthetic tests, weekly/manual preflight and rotation/rewrite runbook. The current tree passes, but reachable history still contains one forbidden blob with six PekPik service-token findings; rotation and history rewrite remain blocked by issue #30.**

## Current automated Pilot Safety checkpoint

Merged technical and operational units:

- PR #23 — deterministic therapeutic refusal and visible-output parity;
- PR #24 — truthful self-care-only emergency operating mode;
- PR #25 — audited patient data portability export;
- PR #26 — executable retention and guarded deletion schedules;
- PR #27 — incident response and escalation procedure;
- PR #28 — onboarding, monitoring, escalation and exit checklists;
- PR #34 — consent and processor-approval readiness gate;
- PR #35 — Morocco residency and foreign-transfer deployment gate;
- PR #37 — fingerprinted native, clinical and multilingual parity review package;
- PR #38 — secret-history remediation preflight and safe rewrite procedure.

These units close procedures and executable controls. They do not imply native-language approval, country-specific legal approval, processor approval, credential rotation, history remediation, completion of a real cohort checklist, completion of an incident drill or approval of the actual production deployment manifest.

---

# Current blockers and next sequence

1. **Security emergency:** revoke or rotate all potentially affected PekPik credentials and review provider activity under issue #30.
2. After rotation confirmation, rewrite all affected refs, require fresh clones, obtain a passing non-shallow PR #38 scan and activate the blocking push/pull-request history gate. The older draft PR #29 is superseded.
3. Complete restricted CNDP, contract, processor, privacy, security and deployment-manifest approvals, then run the PR #34 and PR #35 `--require-approved` gates.
4. Complete the restricted PR #37 native/clinical review manifest and run `audit_safety_corpus_review --require-approved`.
5. Run the deferred live text, STT and vision/OCR benchmarks when approved evidence, credentials, budget and human review are available.
6. In the product-quality lane, close P0-JOURNAL-1 through expected-head merge/post-merge verification, then execute P0-JOURNAL-2 as the next Journal LOT without changing the MENA critical-path numerator.
