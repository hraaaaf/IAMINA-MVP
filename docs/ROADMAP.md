# IAmina — Roadmap

> **Last updated:** 2026-08-10 — fresh exact-main UX evidence reopened one narrow surface: UX-2 rebalances the Summary load-error desktop state from 8.1/10 to 9.3/10 and is in final exact-head certification before merge.
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
| UX visual rebase | 95% | 🟡 UX-2 final certification | UX-0/1 remain closed; fresh exact-main density audit opened only Summary error-state desktop; baseline **8.1/10** → remediated **9.3/10** on PR #86 |
| Journal metabolic-event redesign | 100% | ✅ Closed | P0-JOURNAL-1/2 + P1-JOURNAL-3/4/5/6/7 + P2-JOURNAL-8/9 merged; PR #77 merged as `d841d926d1b7fe076827a3086306daa09399e38d`; UX 9.3/10; post-merge CI #1390 + drift #1202 green |
| P0-MENA-1 — outbound AI/data-egress contract | 100% | ✅ Merged | PRs #10–#15 |
| P0-MENA-2 — locale + safety contract | 63% | 🟡 Native review blocked | PR #16, RTL certification PR #36 and review-package PR #37; three human linguistic/parity gates remain |
| P0-MENA-3 — sovereign authentication migration | 100% | ✅ Merged | PR #17, merge `185f680` |
| P0-MENA-4 — multimodal provider benchmark | 29% | 🟡 All execution paths prepared; live runs blocked | Framework PR #18; text/STT/vision preparation PRs #19–#22 |
| Pilot safety/compliance gate | 69% | 🟡 Automated procedures complete; external security/legal/human gates remain | 9 of 13 explicit gates complete; PRs #34–#35 prepare approval gates; PR #38 prepares secret-history remediation; issue #30 remains blocking |

**MENA critical-path completion:** 32 of 41 explicit roadmap tasks closed, approximately **78%**.

The Journal redesign and UX visual rebase are separate product-quality workstreams and do not change the MENA critical-path numerator.

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

# Journal metabolic-event redesign — CLOSED

**Goal:** turn the add-log surface into a fast, truthful metabolic-event journal that records what happened, keeps treatment decisions out of the UI, and can later support evidence-backed personal response patterns without fabricated precision.

## Mandatory execution rule

Each Journal LOT is a separate branch/PR. Clinical/safety, UX/UI, privacy/egress and persistence reviewers are routed according to the touched surface. UX/UI LOTs require the repository UX certification procedure and a final score strictly above 9.0/10. A clinical safety LOT may not be expanded merely to chase visual polish; its visible behavior must remain usable and non-regressive, while the dedicated UX LOT owns full visual certification.

| LOT | Scope | Status | Acceptance boundary |
|---|---|---|---|
| P0-JOURNAL-1 | Clinical truthfulness | ✅ Closed | PR #67 merged as `e8e94f1940d4fca14f6e022f1dac70fb3f161e64`; post-merge CI #1215 + drift #1031 green; no fabricated glucose/nutrition/insulin precision |
| P0-JOURNAL-2 | Express metabolic event | ✅ Closed | PR #68 merged as `9dd5cbe67522f4c8109debb2f831a99ffc268067`; post-merge CI #1239 + drift #1055 green; UX 9.2/10 |
| P1-JOURNAL-3 | Meal capture | ✅ Closed | PR #69 merged as `1fb3882b8a6b6c671348414dae119ea06c88ce9b`; structured recent/habitual/search + governed photo proposal; explicit confirmation; FR/EN/AR + RTL; Drift v6→v7; UX 9.2/10 |
| P1-JOURNAL-4 | Nutrition data v2 | ✅ Closed | PR #71 merged as `9811a3eaf497aa2ee53f53598c1069c478bf8990`; post-merge CI #1323 + drift #1135 green; sourced food/portion model, provenance/uncertainty, Drift v7→v8, Arabic range bidi fix; UX 9.3/10 |
| P1-JOURNAL-5 | Insulin logging v2 | ✅ Closed | PR #72 merged as `72a248671e5115055c9bc6fc219d0007078906f8`; post-merge CI #1330 + drift #1142 green; actual administered dose only; nullable decimal entry/edit; no presets/calculator/scoring/optimization; safe `client_uuid` snapshot sync; UX 9.2/10 |
| P1-JOURNAL-6 | Context intelligence | ✅ Closed | PR #73 merged as `95cf4d75226720386d7e8e55acc30c39fdd5017c`; post-merge CI #1342 + drift #1154 green; optional positive context, unknown-by-default omission, progressive Add + correctable Edit, legacy fatigue sync-compatible; UX 9.2/10 |
| P1-JOURNAL-7 | Ramadan mode v2 | ✅ Closed | PR #75 merged as `5c70e5aeb67274767e56d0eb80f882ea52a45511`; post-merge CI #1372 + drift #1184 green; explicit nullable profile period; no fasting inference/meal preselection; update-only local persistence prevents fabricated medical defaults; UX 9.3/10 |
| P2-JOURNAL-8 | Personal metabolic response | ✅ Closed | PR #76 merged as `a8ff01b9298f49133b3201d72086ade2643a9167`; post-merge CI #1383 + drift #1195 green; deterministic repeated observations, explicit evidence basis, 90-day synced scope, no causal/statistical/treatment claim; UX 9.3/10 |
| P2-JOURNAL-9 | Post-save experience | ✅ Closed | PR #77 merged as `d841d926d1b7fe076827a3086306daa09399e38d`; persistent factual local receipt; no instant interpretation/advice; mobile actions remain reachable; post-merge CI #1390 + drift #1202 green; UX 9.3/10 |

### P0-JOURNAL-1 durable closeout contract

PR #67 is the merge unit for the first Journal LOT. Its code removes fabricated clinical/nutritional precision from the reachable add-log surface, preserves Drift persistence and `client_uuid`, distinguishes ADA 2026 level-2 `<54 mg/dL` from level-1 `54–69 mg/dL` before persistence, and removes the automatic post-save generative opinion. OCR, meal-photo recognition, voice dictation, richer nutrition, profile-level Ramadan behavior and longitudinal personalization are intentionally not claimed by this LOT; they return only through their dedicated units and existing egress/safety contracts.

P0-JOURNAL-1 is **100% closed**: PR #67 merged at `e8e94f1940d4fca14f6e022f1dac70fb3f161e64`, post-merge CI #1215 and migration drift #1031 both passed. P0-JOURNAL-2 branched from that verified main.

### P0-JOURNAL-2 durable closeout contract

PR #68 delivered the express metabolic-event flow and is **100% closed**. It merged as `9dd5cbe67522f4c8109debb2f831a99ffc268067`; post-merge CI #1239 and migration drift #1055 both passed. The reachable path is `glycaemia → optional measurement context → optional meal → save`, with measurement context distinct from meal type, no inferred defaults, already-taken insulin logging only, additive persistence and certified FR/EN/AR RTL behavior at **9.2/10**.

### P1-JOURNAL-3 durable closeout contract

PR #69 is the merge unit for confirmed meal capture. Foods are stored as stable structured IDs only after explicit user action. Recent and habitual foods derive only from previously confirmed structured history; legacy free text is never parsed into invented meal history. Search is trilingual FR/EN/AR, including Arabic RTL. Meal-photo recognition reuses the existing governed `meal_vision` image-egress path; provider output is presented only as an unselected proposal and nothing is added until the user selects and confirms it. No carbohydrate, GI, nutrition score, insulin-dose, Ramadan or personalization behavior is introduced by this LOT.

Persistence remains additive: the server already had `meal_items`; API create/update/batch now expose it, while Drift v6→v7 adds nullable `meal_items_json`. The migration proof preserves legacy glucose, context, note and `client_uuid` without fabricating structured history. The first rendered UX pass scored **8.9/10 and was rejected**; first-use density was remediated by hiding empty Recent/Habitual sections, then the full desktop/tablet/390×844/360×560 FR/AR matrix recertified at **9.2/10**.

**Pre-closeout evidence on product head `2e30e1c2d6056bb10fd4af1c76727248b74c5056`:** CI #1273 SUCCESS; migration drift #1086 SUCCESS; visual run `31311731261` SUCCESS; artifact `9037609098`, digest `sha256:06104d1f84b37b72cb923ad4e25b45c5a092250160ff0f1a71524849e42570d6`; 8/8 FR/AR expanded meal views with zero page/console errors; UX Auditor **9.2/10 PASS**; Clinical Safety Reviewer PASS; Security Auditor PASS; Database Migration Reviewer PASS.

P1-JOURNAL-3 is **closed** through PR #69, merged as `1fb3882b8a6b6c671348414dae119ea06c88ce9b`. P1-JOURNAL-4 remains a separate merge unit.

### P1-JOURNAL-4 durable closeout contract

PR #71 is the merge unit for Nutrition Data v2. Numeric carbohydrate output is permitted only when the food/preparation and portion are traceable to an explicit versioned nutrition source. Unsupported Moroccan/MENA foods remain loggable but numeric nutrition fails closed instead of being guessed. Patient-confirmed portions persist separately from derived nutrition; the API enforces that each portion belongs to a selected structured food and rejects duplicate/orphan portions. Drift v7→v8 adds nullable `meal_portions_json` while preserving legacy logs and `client_uuid`. No glycaemic-index score, meal-impact score, insulin recommendation, dose calculation or treatment optimization is introduced.

The first Arabic visual review was rejected because a numeric range could render high→low under RTL. The final implementation isolates the numeric span at runtime without embedding invisible bidi controls in generated localization source. Exact-code visual run `31320713710` on `f909fac3cc57af81955fdee9bbaee4f87689734c` passed the full FR/AR desktop/tablet/390×844/360×560 matrix plus real-font Chromium captures; artifact `9040098902`, digest `sha256:b1b1919c3d329ca13ac77064e0f187dab36ecf4b16ef02ff36be0d30239736ae`; UX Auditor **9.3/10 PASS**. P1-JOURNAL-4 is **100% closed** through PR #71, merged as `9811a3eaf497aa2ee53f53598c1069c478bf8990`; post-merge CI #1323 and migration drift #1135 both passed. P1-JOURNAL-5 branched from that verified main.

### P1-JOURNAL-5 durable merge-unit contract

PR #72 is the merge unit for factual insulin logging. `insulin_units` represents only a dose the patient says was already administered; it is nullable and decimal-preserving in create, edit and history surfaces. The patient-facing flow offers no suggested units, presets, dose calculator, dose score, correction advice or treatment optimization. Empty/zero client input is stored as no administered dose, while negative API input is rejected. Editing insulin does not rewrite meal context or the legacy Ramadan field.

Offline/server reconciliation remains keyed by `client_uuid`: a later snapshot for the same patient updates the existing log rather than being acknowledged as a no-op, while a UUID collision owned by another patient is rejected. This makes post-sync insulin corrections durable without weakening patient isolation. No schema migration or new external egress is introduced.

**Final certification evidence:** final product head `819241d92963f87d6cc172b315926c24854f1b1d`; CI #1329 SUCCESS; migration drift #1141 SUCCESS; final visual audit run `31323384228` SUCCESS; Clinical Safety, Persistence/Sync, Security/Privacy and UX/UI reviewers PASS; Release Certifier CERTIFIED; PR #72 merged as `72a248671e5115055c9bc6fc219d0007078906f8`; post-merge CI #1330 and migration drift #1142 SUCCESS. P1-JOURNAL-5 is **100% closed**.

### P1-JOURNAL-6 durable merge-unit contract

PR #73 is the merge unit for Context intelligence. Illness, unusual stress, physical activity and poor sleep are recorded only when the patient explicitly selects them. Omission means **unknown / not reported**; new server writes no longer fabricate `no`, `good` or `ok` defaults. Existing historical rows are preserved unchanged by migration `0022_context_unknown_defaults`.

The Add flow keeps these signals behind one progressive optional action instead of repeatedly presenting four low-value questions. Edit Log can add or remove the same observations without rewriting meal, time or insulin data. Sync transmits only explicit positive context; legacy explicit fatigue (`tired`) remains compatible while an unreported fatigue state no longer becomes fabricated `ok`. Journal history surfaces only context actually recorded. This LOT does not infer causes from glucose, meals or time and adds no treatment advice, clinical score or AI/provider egress.

**Final certification evidence:** final product head `fccbdf5bf69bd72c2cf079091b96cd52dcdf3d0c`; CI #1341 SUCCESS; migration drift #1153 SUCCESS; exact-final-head visual audit run `31326260406` SUCCESS on Add/Edit FR/AR desktop/tablet/390×844/360×560; UX Auditor **9.2/10 PASS**; Clinical Safety, Persistence/Migration, Security/Privacy and UX/UI reviewers PASS; Release Certifier CERTIFIED; PR #73 merged with expected-head locking as `95cf4d75226720386d7e8e55acc30c39fdd5017c`; post-merge CI #1342 and migration drift #1154 SUCCESS. P1-JOURNAL-6 is **100% closed**. P1-JOURNAL-7 is next.

### P1-JOURNAL-7 durable merge-unit contract

PR #75 is the merge unit for Ramadan mode v2. Ramadan is now an optional profile-level period configured explicitly by the patient, not a per-log pseudo-clinical switch and not a state inferred from calendar, country, location, time or meal timing. Both dates are required together and must be ordered; missing, partial or inverted periods fail closed.

For an event whose logged date falls inside the explicitly configured period, Journal uses the neutral meal vocabulary **Suhoor / Iftar / Snack / Other**. No meal is preselected, and neither the configured period nor a meal label proves that the patient fasted. Outside the configured period, standard meal vocabulary remains authoritative. The LOT adds no diagnosis, glucose-threshold change, dose calculation, treatment optimization, causal claim or external AI/provider egress.

Persistence is additive: Django migration `0023` adds nullable profile dates and Drift v8→v9 adds the same local fields while preserving historical Journal rows and stable `client_uuid` values. The legacy per-log `ramadan_mode` column remains compatible but is not retrospectively rewritten or promoted into authoritative fasting evidence. FR/EN/AR copy and Arabic RTL are covered.

**Final certification evidence:** final pre-merge head `3458667a76472829aba5f79b05c74346bf7bbb95`; CI #1371 SUCCESS; migration drift #1183 SUCCESS; PostgreSQL migration validation + full source-of-truth suite SUCCESS; exact-final-head visual audit run `31377323425` (#20) SUCCESS with 24/24 FR/AR Profile + Add Log renders across `1440×1000`, `768×1024`, `390×844` and hostile `360×560`; artifact `9058462463`, digest `sha256:94c6c4f6980b1ff025d56498e2e984be8de05d6949e4ccde86e0d66a4fdde474`; UX Auditor **9.3/10 PASS**; Clinical Safety Reviewer FINAL PASS; Database & Migration Reviewer FINAL PASS; UX Auditor FINAL PASS; Release Certifier CERTIFIED; PR #75 merged with expected-head locking as `5c70e5aeb67274767e56d0eb80f882ea52a45511`; `main` verified on that merge; post-merge CI #1372 and migration drift #1184 SUCCESS.

The independent clinical review found and blocked a fresh-local-profile path that could create a medical profile row with default clinical targets when only Ramadan was being configured. The remediation makes local Ramadan persistence update-only, refuses to manufacture a profile when none exists, preserves existing clinical profile values, reports local/server/degraded/failure save states truthfully in FR/EN/AR, and is protected by permanent regressions. Temporary remediation/audit scaffolding is absent from the merge diff. P1-JOURNAL-7 is **100% closed**.

### P2-JOURNAL-8 durable merge-unit contract

PR #76 is the merge unit for Personal metabolic response. The Journal now computes deterministic, patient-scoped repeated-observation patterns from already-synchronized source logs; no derived pattern is persisted. Context patterns are eligible only from explicit positive patient-entered states (`stress=yes`, `activity=yes`, `illness=yes`, `sleep=bad`, explicit fatigue), and meal patterns require an explicit `post_meal` glycaemic context plus meal type. Historical `no/good/ok` values are never treated as a control cohort because older schemas may have materialized such defaults. Demo rows are excluded, the analysis window is bounded to 90 days, and insufficient repetition fails closed.

Each visible pattern exposes its observation count, distinct-day count, pattern median, whole synced-window median and a **descriptive repetition grade**. That grade is product evidence density, not a probability, statistical significance test or clinical confidence score. The patient-facing contract explicitly states that an observed association does not establish cause and must not guide treatment or dosing. No predicted glucose, diagnosis, causal delta, treatment optimization, dose calculation or new AI/provider egress is introduced. API scope derives only from the authenticated `request.user.id`, and the UI states that only server-synchronized readings are analyzed.

The first real FR/AR max-density visual pass was rejected at **8.8/10** because three simultaneous pattern cards displaced Journal history too aggressively on `360×560`. The same LOT was remediated to show one strongest pattern by default with an explicit accessible disclosure for secondary patterns.

**Final certification evidence:** final pre-merge head `7f4003c4511c5eb27e9d01528a71269cc9511548`; canonical CI #1382 SUCCESS including PostgreSQL source-of-truth; migration drift #1194 SUCCESS; exact-final-head visual audit run `31384539082` SUCCESS with 24/24 FR/AR compact/expanded/insufficient renders across `1440×1000`, `768×1024`, `390×844` and `360×560`; artifact `9061180931`, digest `sha256:d9dbf85b7df8785b0af139a5a1ee63f6a98f55362d3575db3f1a9482bf66e006`; UX Auditor **9.3/10 PASS** after an initial 8.8/10 density rejection and remediation; Clinical Safety, Security, Database/Migration and UX reviewers FINAL PASS; Release Certifier CERTIFIED; PR #76 merged with expected-head locking as `a8ff01b9298f49133b3201d72086ade2643a9167`; post-merge CI #1383 and migration drift #1195 SUCCESS. P2-JOURNAL-8 is **100% closed**. P2-JOURNAL-9 is next.

### P2-JOURNAL-9 durable merge-unit contract

PR #77 is the merge unit for the post-save experience. After the existing Drift insertion succeeds, the Add Log flow now remains on a persistent factual receipt instead of showing a transient snackbar and immediately redirecting away. The receipt restates only the facts just recorded: glucose, timestamp and any explicitly entered measurement context, meal, already-taken insulin and additional context observations. It states only that the entry was saved on the device; it does not claim server synchronization or external persistence.

The receipt does not classify a non-low glucose value as good/bad or inside a personal target, does not call AI, and does not generate prediction, diagnosis, causal explanation, treatment optimization or dose advice. Longitudinal personal-response patterns remain a separate Journal surface governed by P2-JOURNAL-8 evidence requirements. The existing deterministic low-glucose safety classification continues to execute before persistence and is unchanged by this LOT.

After a successful save, the prior draft is cleared before another entry can begin, preventing previous meal/context/insulin facts from being silently reused. The next actions are explicit: **View in Journal / Add another reading / Done**. The first real FR/AR visual pass scored **8.9/10 and was rejected** because a rich receipt on `360×560` pushed all next actions below the fold. The same LOT was remediated so the receipt body scrolls independently while the action panel remains persistently reachable on mobile; Arabic numeric insulin values remain LTR.

**Pre-closeout evidence on product head `ec701826a2f2be6edc075742d3c6d349564b77db`:** canonical CI #1387 SUCCESS; migration drift #1199 SUCCESS; focused FR persistence→render/reset and AR/RTL tests PASS; exact-code visual audit run `31389858816` SUCCESS with 16/16 FR/AR minimal/rich receipt renders across `1440×1000`, `768×1024`, `390×844` and `360×560`; artifact `9063210662`, digest `sha256:62b67588d47b0f5a441f38ebb11cbc362d6e7e56b4e3b8deef0e22213bba77f6`; UX Auditor **9.3/10 PASS**; Clinical Safety, Security/Privacy, Persistence/Database and UX reviewers FINAL PASS; unresolved review threads 0. Canonical documentation changed the pre-merge head to `cc529c378eea7cb4908a57fdad2e85db5bde75bd`; exact-final-head CI #1389, drift #1201 and visual audit #4 all passed, the four specialist reviewers re-anchored FINAL PASS, and Release Certifier authorized the expected-head merge. PR #77 merged as `d841d926d1b7fe076827a3086306daa09399e38d`; post-merge CI #1390 and migration drift #1202 passed. **P2-JOURNAL-9 and the complete Journal metabolic-event redesign are 100% closed.**

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
| P2-UX-14 | Densité et polish | 100% | **9.2/10** after Reviewer double-check; PR #66; 40-view FR/AR final matrix run `31267173791`, artifact `9024558783`, zero page errors | ✅ |

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

### P0-UX-8 delivered work

- The existing Material `NavigationBar` is retained because inspection showed that P0-UX-6.4 had already delivered the required permanent labels and explicit active indicator; no cosmetic rewrite was introduced without evidence.
- A permanent real-widget contract now mounts the actual `MainShell` at `390×844` in French and Arabic.
- All five destinations remain visible and labelled: Dashboard, IAmina, Journal, Importer and Settings.
- The contract proves route-derived active state, real taps to Importer and Journal, Arabic RTL direction, touch targets of at least 48 px and screen-reader semantics containing each localized destination label.
- The complete frontend suite passed after the semantics contract was corrected to match Flutter's composite semantics labels and to dispose its test handle before end-of-test verification.
- Mobile FR and AR were visually recaptured at `390×844` across Dashboard, Summary, Journal, Importer and Profile: 10 views, one Flutter view per capture and zero page errors.
- Visual double-check found permanent labels legible, selected-state pills unambiguous, RTL ordering correctly mirrored and no navigation overlap at the certified viewport.
- Visual artifact: `8995273847`, digest `sha256:ce0fb1cb2f46855e30c0ed8c4eb9dd22fc67375a646ed3ef55ff91afdf4de607`.
- Certified pre-roadmap test head `dc70dbcedc56300f811087d0f75312b3460e9232` passed CI #1075 and migration drift #891.

**Final P0-UX-8 score: 9.4/10 — PASS.** No critical or high-severity navigation defect remains in the certified 390×844 FR/AR scope. P0-UX-9 remains separate and will certify the harsher `360×560` viewport and transient overlays.

### P0-UX-9 delivered work

- The five certified user journeys were audited at the harsher `360×560` viewport in both French and Arabic/RTL before remediation.
- The first visual pass scored only **8.6/10** and was explicitly rejected rather than closed: Dashboard CTA crowding, an under-designed Summary error state, a redundant IAmina FAB, French residue in Arabic Summary, cramped Arabic period chips and excessive Profile emphasis remained.
- Dashboard first-use composition now adapts to short heights: illustration, spacing and CTA padding compact without hiding the secondary import action behind mobile navigation.
- Summary mobile now uses a localized IAmina header instead of a desktop breadcrumb, removes the redundant IAmina FAB, localizes loaded-state greeting/observation and presents failure as a deliberate bounded product card with a 48 px retry action.
- Arabic period labels no longer collapse into forms such as `7ي`; the compact label uses the readable `يوم` token and the Summary capture contains no French residue.
- Profile reduces the promotional elevation of the IAmina configuration card and displays completion percentage only once.
- The Profile sign-out sheet remains scroll-controlled and safe-area aware for short screens; a permanent `p0_ux_9_small_screen_contract_test.dart` prevents regression of the certified small-screen contracts.
- The second FR/AR `360×560` matrix covers Dashboard, Summary, Journal, Importer and Profile: **10/10 rendered views, zero page errors**, no observed overlap or RTL regression.
- Certified product head `0d421f2dc36fd295a4d69f302c7596a5950a9f50` passed CI #1092 and migration drift #908. Visual evidence: run `31208830202`, artifact `9005910951`, digest `sha256:eeeda5f517eaf0c6d0f6a3a6124335bc1250fc2942cb6e7636712a3563a91a14`.

**Final P0-UX-9 score: 9.2/10 — PASS.** The score was assigned only after the rejected 8.6/10 pass was corrected and recaptured. No critical/high small-screen defect remains in the certified FR/AR `360×560` scope. PR #60 is the merge unit; P0-UX-10 is next.

### P0-UX-10 delivered work

- Code inspection established that Importer and the historical Pulper screen are not competing acquisition products: `/importer` is the sole primary acquisition hub, while `/pulper` is a subordinate document workflow that performs pick → ingest → preview → explicit confirmation.
- The technical `/pulper` route and internal `PulperPreview` / `PulperConfirmResult` model names remain implementation details; no backend, persistence or confirmation semantics were changed.
- User-facing `Pulper IAmina` branding was removed. The Importer hub now presents the localized task **Importer un document**, and the document screen uses the same task-first title without duplicating it in the hero.
- UI implementation names were aligned to the product model (`DocumentImportCard`, `DocumentFormatChip`, `DocumentImportIcon`) while preserving the historical internal route to avoid an unnecessary navigation migration.
- A permanent `p0_ux_10_importer_document_entry_contract_test.dart` proves that Importer is the only primary navigation entry, the document workflow remains subordinate and no user-facing Pulper branding returns.
- The first 16-view visual pass was explicitly rejected: the French `360×560` document screen partially clipped the primary **Choisir un document** CTA at the bottom.
- The same LOT was corrected with a short-height layout contract (`≤600 px`) that reduces only vertical spacing, icon size and CTA padding while preserving the complete privacy notice and all document-format choices.
- The second matrix covers Importer plus document import in FR/AR at `1440×1000`, `768×1024`, `390×844` and `360×560`: **16/16 rendered views, zero page errors**, no visible Pulper branding, clean RTL and a fully visible primary CTA at the harshest viewport.
- Certified product head `14e7a6d605aeb31d6c1813c614f9b72bbbf71d53`; visual evidence: run `31224557639`, artifact `9011673527`, digest `sha256:8e064f44d31f5422d8662cb8f88a962d74fcc8a676a6139cf5906110f2893710`.

**Final P0-UX-10 score: 9.4/10 — PASS.** The LOT was not closed on the first successful implementation: the clipped 360×560 French CTA forced a second remediation and complete recertification. PR #61 is the merge unit; P0-UX-11 is next.

### P0-UX-11 delivered work

- The existing first-use Dashboard was audited before modification across FR/AR at `1440×1000`, `768×1024`, `390×844` and `360×560`. The baseline scored **8.4/10** and was rejected: desktop was under-composed, the empty state could appear while local streams were still loading, and feature pills such as real-time AGP / AI analysis could imply capabilities before any patient data existed.
- Local data states are now explicit and truthful: loading and local-read error are distinct from an actually empty Dashboard, with a localized retry action for errors; offline state remains derived from the real `SyncService` state.
- The empty state presents no fabricated KPI, graph or sample patient value. The primary action is the real **add first measurement** route and document import remains a real secondary action.
- Ambiguous feature-promise pills and the emoji illustration were removed. A clinical Material icon and factual FR/AR/EN copy explain that the Dashboard is built only from real recorded data.
- Wide layouts use a two-zone first-use composition instead of a narrow mobile block stretched across desktop; mobile and RTL use a single directional column with 48 px actions.
- The first post-patch visual pass was also rejected because the French truth-note card was partially obscured by the bottom navigation at `360×560`. The same LOT was corrected so short-height screens prioritize the factual body and both acquisition actions without hiding content.
- The final matrix covers the Dashboard in FR/AR at `1440×1000`, `768×1024`, `390×844` and `360×560`: **8/8 rendered views, zero page errors**, stable RTL and fully visible primary/secondary actions. Baseline local API connection-refused console noise remains unchanged and is not presented as a new runtime regression.
- Certified product head `2b65e9c4357b59bbc2d53cdde2e6a3271e65911c` passed CI #1128 and migration drift #944. Visual evidence: run `31248641421`, artifact `9019314222`, digest `sha256:b1846c10a68a918ad0ea5484fe50726da3ae69710944b072bf88e947eb45dd03`.

**Final P0-UX-11 score: 9.3/10 — PASS.** The LOT exceeded the mandatory threshold only after the baseline and the first post-patch small-screen result were both rejected and remediated. PR #62 is the merge unit; P1-UX-12 is next.

### P1-UX-12 delivered work

- The existing Profile was inspected before modification and found to mix medical configuration, IAmina preferences, account/privacy actions and a fabricated completion percentage in one long surface.
- The Profile is now organized into three explicit progressive sections: **Suivi médical**, **IAmina & préférences**, and **Confidentialité & compte**, all collapsed by default for fast scanning on narrow screens.
- The former completion percentage was removed because default values could make an unconfigured profile look partially complete.
- Empty medical state is fail-closed and truthful: it shows a neutral “À compléter ou vérifier” summary until a persisted profile actually exists; real diabetes/treatment/unit values are summarized only after persisted data is loaded or successfully saved.
- Medical target inputs stack on compact widths, account/consent actions remain isolated with 48 px controls, and existing safe-area/scroll behavior is preserved.
- FR/EN/AR localization owns all new section labels and hints; Arabic RTL remained visually coherent across the certified matrix.
- A permanent `p1_ux_12_progressive_profile_contract_test.dart` locks the progressive structure, collapsed defaults, truthful persisted-profile summary and sensitive-action grouping.
- Builder/Reviewer remediation run `31254691325` passed `flutter analyze --no-fatal-infos` and **8/8 targeted tests**.
- Final full CI then caught a real non-regression: P1-UX-12 had narrowed the Profile surface from the P0-UX-7 certified `1040` px contract to `920` px. The LOT stayed open; run `31258415090` restored `maxWidth: 1040` and passed the P1-UX-12, P0-UX-7 and P0-UX-9 targeted contracts before commit.
- Exact product head `322be3bf82e3f112e4ebf89aea732353a0c72d59` was visually recertified in FR/AR at `1440×1000`, `768×1024`, `390×844` and `360×560`: **8/8 rendered views, one Flutter view each, zero page errors**. Expected local API `ERR_CONNECTION_REFUSED` console noise is unchanged and not treated as a new runtime regression.
- Visual evidence: run `31258575687`, artifact `9022145295`, digest `sha256:091faa01cb4c4b7004844a0eb29e3f6bf3328f2588dbf6e6ebbed1a5048fb996`.
- Independent visual Reviewer found no critical/high defect after remediation and scored the final Profile **9.4/10**.

**Final P1-UX-12 score: 9.4/10 — PASS.** PR #64 is the merge unit; P1-UX-13 is next.

### P1-UX-13 delivered work

- Baseline audit covered Summary, Importer, document import and consent in FR/AR at `1440×1000`, `768×1024`, `390×844` and `360×560`: **32/32 rendered views, zero page errors**. The baseline scored **7.9/10** and was rejected because expert/internal wording such as `Export CGM` and `Traitement externe contrôlé` required unnecessary domain knowledge.
- CGM is now expanded in patient-facing acquisition copy, while the acronym remains as the complementary medical term. The former `AGP en temps réel` wording was removed because AGP is a standardized summary/report concept rather than a truthful real-time capability label; the UI now uses a plain-language sensor-trend summary with `(AGP)` in complement.
- Reading coverage copy now explicitly distinguishes the proportion of recorded readings from CGM time in range, avoiding a clinically misleading equivalence.
- External-processing copy was simplified to task-first language while retaining the already-certified privacy conditions: consent, provider authorization, hosting region, retention period and fail-closed behavior when approval is missing.
- The permanent `p0_privacy_truthfulness_contract_test.dart` was migrated rather than weakened: it continues to require deployment/provider evidence and reject unsupported privacy claims, while no longer forcing the obsolete internal phrase `Traitement externe contrôlé`.
- Permanent `p1_ux_13_wording_contract_test.dart` and `p1_ux_13_compact_consent_contract_test.dart` lock the new terminology and harsh small-screen behavior.
- The first post-patch visual recertification was **rejected at 8.8/10**: on `360×560` FR/AR the longer, safer consent copy pushed both user choices below the initial viewport. The LOT remained open.
- Compact-height consent remediation (`≤600 px`) reduces only layout density and typography; it does **not** remove consent conditions. Builder validation run `31263759746` passed Flutter analyze, P1-UX-13 wording, compact-consent, privacy-truthfulness and P0-UX-9 small-screen contracts.
- Final exact product head `6b283650d055fbb073273734b91ae79eb68fcfe4` was recaptured across the complete 32-view FR/AR matrix. Both **Accept & continue** and **Continue without AI** are visible at `360×560` in FR and AR, RTL remains coherent, and no other audited surface regressed.
- Final visual evidence: run `31263898750`, artifact `9023631718`, digest `sha256:8cfe6334d10e555d9fc407ff4a82789ebc377dace9e7d5986865e0b7b19ef3e6`; `source-sha.txt` matches the product head, all 32 entries have exactly one Flutter view and zero page errors.
- Clinical Safety Reviewer PASS: no diagnostic, treatment, dose, clinical threshold or calculation behavior changed; wording remains non-prescriptive and privacy egress conditions remain fail-closed.

**Final P1-UX-13 score: 9.3/10 — PASS.** The LOT exceeded the mandatory threshold only after the 7.9 baseline and 8.8 first recertification were both rejected and remediated. PR #65 is the merge unit; P2-UX-14 is next.

### P2-UX-14 delivered work

- The canonical UX-A09/UX-A10 baseline covered Dashboard, Summary, Journal, Importer and Profile in FR/AR at `1440×1000`, `768×1024`, `390×844` and `360×560`: **40/40 rendered views**, one Flutter view per capture and zero page errors. Baseline evidence: run `31266321341`, artifact `9024312935`, digest `sha256:6f402c09185e5fcde6be8bbd09f856ecf072a7bd390c115884375491e5958ef1`.
- The baseline scored **8.5/10 — CHANGES_REQUIRED**. Wide layouts still felt under-structured: the Summary error state was too small for desktop, Journal empty state floated in excessive whitespace, and Profile lacked a sufficiently coherent clinical grouping.
- Remediation stayed deliberately cosmetic/structural: no business logic, clinical calculation, privacy behavior, persistence, route contract or patient-facing medical meaning changed.
- Summary now uses a proportionate wide error composition while preserving the compact `360×560` state and 48 px retry action. Journal wide empty state is anchored to the readable content region rather than centered in unused canvas. Profile progressive sections gain a coherent desktop grouping with shared clinical radii and shadows.
- Existing Dashboard and Importer layouts were intentionally left unchanged after review showed they already met the density objective. P0 desktop/tablet width contracts, mobile navigation, small-screen behavior and RTL remained stable.
- Builder double-check caught and removed generated Flutter metadata/lockfile noise plus broad formatter churn before review; the final product diff contains only the three targeted screens and permanent `p2_ux_14_density_polish_contract_test.dart`.
- Final exact visual product head `b6f42319207fff380b634f0d390dd3c8b45221b4` was recaptured across the complete **40-view** matrix. `source-sha.txt` matches; all 40 report rows have one Flutter view and zero page errors. Final evidence: run `31267173791`, artifact `9024558783`, digest `sha256:fcb730b7c32b8b2a8435072109f6a879170414f81e39ec8f139c28b421d5e902`.
- Independent UX Reviewer PASS review `4889215432`: no critical/high defect observed; final score **9.2/10**. Pre-ROADMAP PR-head gates on the reviewed SHA were green: CI `31267596592` and migration drift `31267596575`.

**Final P2-UX-14 score: 9.2/10 — PASS.** PR #66 is the merge unit. The visual UX remediation workstream has now completed all canonical P0-CERT-4 defect lots; merge still requires exact-final-head CI/drift, Release Certifier GO and post-merge verification.

This UX remediation workstream is separate from the MENA critical-path numerator.

---

# UX visual rebase — ACTIVE

**Goal:** re-audit only product states not covered by the historical global matrix, preserve already certified surfaces, and open remediation LOTs only when fresh rendered evidence requires them.

Canonical visual rules and evidence hierarchy: `docs/ux/UX_VISUAL_CONSTITUTION.md`.

| LOT | Scope | Progress | Evidence / acceptance | Status |
|---|---|---:|---|---|
| UX-0 | Baseline + visual constitution | 100% | PR #83 merged as `0a9e026638021ea3e565d5cf870da7ed9ec1c5ee`; post-merge CI #1447 + drift #1259 green; fresh populated Dashboard baseline **8.4/10** established without reopening already certified surfaces | ✅ Closed |
| UX-1 | Populated Dashboard locale parity + hierarchy | 100% | PR #84 merged as `0c2e0ee18da003ccc413ffeffef18334a77c6ad9`; exact-head CI #1452 + drift #1264 + visual run `31409668306` green; UX **9.2/10**; post-merge CI #1453 + drift #1265 green | ✅ Closed |
| UX-2 | Summary load-error desktop composition | 90% | Fresh exact-main baseline run `31413385769` isolated Summary desktop at **8.1/10** while Profile/Importer stayed >=9; product head `97df55865a13916c9bdf7f01796a60ba2d827ee2` remediated to **9.3/10**, CI #1458 + drift #1270 + visual run `31414604776` green; final docs-head recertification, Certifier, merge and post-merge gates pending | 🟡 |

UX-1 was intentionally narrower than the historical UX plan. A fresh exact-main audit later found one new <=9.0 state: Summary load-error desktop composition. UX-2 is limited to that evidence; Dashboard, Journal, Profile, Importer and post-save surfaces stay protected by their existing rendered certifications.

### UX-1 pre-closeout evidence

- Baseline: populated Dashboard **8.4/10** cross-locale on run `31403179971`, artifact `9068596037`; raw `dinner` and French KPI/chart/insight residue were visible in Arabic.
- Product remediation localizes canonical/legacy meal IDs plus all high-salience populated Dashboard Hero, GMI, CV, AGP, event, insight and recent-entry copy in FR/EN/AR. Clinical calculations, thresholds, persistence and data semantics are unchanged.
- The clinical explainability contract was migrated rather than weakened: GMI method/coverage/laboratory limitation and CV general-reference/non-personalized wording are now asserted through the same l10n keys and explicit FR/EN/AR corpus.
- Exact product head `2b1483fb89b6dcbb6885f017085a98b48d0d7e76` passed CI #1449 and migration drift #1261, including the complete Flutter suite and PostgreSQL source-of-truth.
- First post-fix visual matrix run `31407376293`, artifact `9070305707`, digest `sha256:ea150de67056d74d6209ea3d862445d1235aaf9084e7f0b4ff971a23e604d`: 32 FR/AR top/mid/lower/full screenshots across `1440×1000`, `768×1024`, `390×844`, `360×560`, zero page errors; visual read approximately **9.2/10**. A second product-head render run `31408059463`, artifact `9070602793`, digest `sha256:13d13788927edd5e29cafe5915b6ed2a33cb7fdadc92599b8aac680abbc5e2b7` reproduced the same corrected runtime before the test-only contract migration.
- Exact final head `27ee9b00c2326add7642bb0f544f5658ebf4d949` passed CI #1452 and migration drift #1264. Final visual run `31409668306`, artifact `9071144760`, digest `sha256:fb2490f8a4d293206917adbcfb56dbc57c24a49f67a61f27eea3a9db391e088f` rendered 24/24 FR/AR top/mid/lower views with one Flutter view each and zero page errors. UX Auditor FINAL PASS **9.2/10**, Clinical Safety Reviewer FINAL PASS, Release Certifier CERTIFIED. PR #84 merged with expected-head locking as `0c2e0ee18da003ccc413ffeffef18334a77c6ad9`; post-merge CI #1453 and drift #1265 passed. **UX-1 is 100% closed.**

### UX-2 pre-closeout evidence

- Fresh exact-main audit source `f65b0d6619b233442c0df6baaf70ad70d74593fa`: valid run `31413385769`, artifact `9072572476`, digest `sha256:f111bd8af928c4ef96a83fd2924782ff3acd85dc9c1efba002aa01cf22ed7aae`; 24/24 Summary/Importer/Profile FR/AR renders across `1440×1000`, `768×1024`, `390×844`, `360×560`, one Flutter view each and zero page errors.
- Product Design baseline kept Profile (~9.1–9.2) and Importer (~9.0–9.1) closed; only Summary load-error desktop was reopened at **8.1/10** because the horizontal error strip was visually stranded in a large empty canvas.
- UX-2 changes presentation only: a compact focal error card on wide layouts, preserving localized copy, `_fetchData`, period controls, mobile behavior, clinical/data semantics, persistence, API and egress boundaries.
- Product head `97df55865a13916c9bdf7f01796a60ba2d827ee2`: canonical PR CI #1458 and migration drift #1270 passed. Exact-product visual run `31414604776`, artifact `9072965994`, digest `sha256:ada98ce81842ce59354a09ba7dd3158f43d5711517d5fce6eab2b3dfe3d66e2a`: 8/8 Summary FR/AR renders, one Flutter view each, zero page errors. UX Auditor / Product Design **PASS — 9.3/10**; no critical/high visual finding; mobile and RTL remain stable.
- UX-2 remains open until the final documentation head is revalidated, Release Certifier authorizes expected-head merge, PR #86 merges and post-merge CI/drift pass.

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
6. **UX product-quality lane:** UX visual rebase is closed. Do not open another UX remediation LOT unless fresh rendered evidence exposes a new <=9.0 state or a new requirement changes a certified surface.
7. **Journal product-quality lane is closed.** Do not reopen it without a new evidence-backed roadmap decision; after blockers 1–5 are cleared, move to the real-patient pilot go/no-go and cohort execution gates.
