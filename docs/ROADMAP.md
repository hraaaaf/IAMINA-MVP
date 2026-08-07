# IAmina — Roadmap

> **Last updated:** 2026-08-07 — P0-UX-7 desktop/tablet remediation certified and merged; P0-UX execution now requires a documented UX/UI score strictly above 9/10 before closure.
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
| P0 visual UX remediation | 22% | 🟡 Active — P0-UX-8 next | P0-UX-6 and P0-UX-7 closed; PRs #53–#57; P0-UX-7 visual recertification run `31166646157` |
| P0-MENA-1 — outbound AI/data-egress contract | 100% | ✅ Merged | PRs #10–#15 |
| P0-MENA-2 — locale + safety contract | 63% | 🟡 Native review blocked | PR #16, RTL certification PR #36 and review-package PR #37; three human linguistic/parity gates remain |
| P0-MENA-3 — sovereign authentication migration | 100% | ✅ Merged | PR #17, merge `185f680` |
| P0-MENA-4 — multimodal provider benchmark | 29% | 🟡 All execution paths prepared; live runs blocked | Framework PR #18; text/STT/vision preparation PRs #19–#22 |
| Pilot safety/compliance gate | 69% | 🟡 Automated procedures complete; external security/legal/human gates remain | 9 of 13 explicit gates complete; PRs #34–#35 prepare approval gates; PR #38 prepares secret-history remediation; issue #30 remains blocking |

**MENA critical-path completion:** 32 of 41 explicit roadmap tasks closed, approximately **78%**.

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

## ✅ P0 product truthfulness

- Real actions and the complete local CRUD loop are permanently certified.
- Synchronization and storage labels derive from real typed state.
- Clinical metrics disclose method, coverage and limitations without fabricated precision.
- Mobile Importer and the document picker are certified on narrow and short viewports.
- Privacy wording is deployment-aware in FR/EN/AR and fails closed before external document processing.
- Permanent Flutter contracts prevent regression of all five requirements.

**Closure:** PRs #39–#43. This workstream is separate from the MENA critical-path numerator.

---

# P0 visual UX remediation — ACTIVE

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
| P0-UX-8 | Navigation mobile | 0% | Next LOT — permanent labels, explicit active state, FR/AR, touch targets and screen reader | ⏭️ |
| P0-UX-9 | Petit écran 360×560 | 0% | Queued after P0-UX-8 | ⬜ |
| P0-UX-10 | Importer / Pulper | 0% | Queued | ⬜ |
| P0-UX-11 | Dashboard premier utilisateur | 0% | Queued | ⬜ |
| P1-UX-12 | Profil progressif | 0% | Queued | ⬜ |
| P1-UX-13 | Wording médical et produit | 0% | Queued | ⬜ |
| P2-UX-14 | Densité et polish | 0% | Queued | ⬜ |

### P0-UX-7 delivered work

- Routed pages receive the true post-sidebar viewport instead of the full window width.
- Dashboard first-use content keeps a readable width while data views may use more space.
- Journal long-history content is constrained to a readable desktop measure.
- Importer uses a two-column desktop composition for direct connection cards when space permits.
- Profile and Pulper use bounded, centered desktop surfaces without shrinking tablet layouts.
- A shared responsive surface and permanent Flutter non-regression contract were added.
- Desktop FR `1440×1000` and tablet AR/RTL `768×1024` were recaptured across Dashboard, Journal, Importer, Pulper and Profile.
- Visual comparison found the desktop composition materially improved and tablet RTL stable, with no new runtime/page error.
- Product head `bf633bc1524f7d52c179f0edc33150d93c5d8431` passed the full pre-merge CI and migration gates; post-merge `main` at `0a098d8b157c8d030e4d2ed8a6b4b8fcd895cccb` also passed CI #1062 and migration drift #878.

**Final P0-UX-7 score: 9.3/10 — PASS.** The score is above the mandatory 9.0 threshold, so no additional remediation iteration is required for this LOT.

This UX remediation workstream is separate from the MENA critical-path numerator.

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
