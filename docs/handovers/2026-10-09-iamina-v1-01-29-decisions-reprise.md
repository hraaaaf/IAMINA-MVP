# IAMINA V1-01 — CANONICAL RESUME HANDOVER — 2026-10-09

> **Authority:** `docs/ROADMAP.md` always wins for progress and next work; this file is a compact operational handover, not a second roadmap. New session: read this file, then check live GitHub branch/PR/CI and Notion before continuing. Evidence does **not** imply clinical certification.

## Goal / observable success / proof

**Goal:** patient-safe, source-traceable deterministic calculations and coherent glucose-unit rendering/storage, with no unsanctioned normative output or external patient-context model call.

**Success:** each CAL-01…12 source/transformation/consumer known; invalid/missing/insufficient-data negative tests, bounded conversions, patient scope, SQLite+PostgreSQL, API and real UI consistent; competent clinical/privacy reviewers approve where required; full exact-head and post-merge evidence. **Current success = not reached.**

**Latest exact clinical-code HEAD proof** `63988a98a9b76ebdc82219b74f0ec42363274baa`: [17/17 PR workflows SUCCESS](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38006733937) on 2026-10-10. Main CI: Ruff/architecture/anti-egress/OpenAPI generated equality green; **SQLite 2806 passed / 5 skipped / 3 xfailed**; **PostgreSQL 2810 passed / 1 skipped / 3 xfailed**; **Flutter 671 passed / 1 skipped**, PWA/web built, Chrome visual workflows all green. Doctor Brief is deterministic using `consultation-brief.v1` source/version/evidence ID/window, same-scope non-demo sample count (>=5), localized literal templates and HTTP auth/cross-patient negative tests; **this is not clinician/privacy/locale sign-off**. Historical [Chrome 12 PNG BEFORE/AFTER](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/37969874302/artifacts/11635771127) on `b0e971e` yielded **8/10 provisional FR visual score**, not a new score or medical release proof. Last checked `main` base for this PR: `13b7cce12c86daf60119fb703f22e8c6c192cf8d`.

## Repository / branches / PRs

- Repo `hraaaaf/IAMINA-MVP`.
- V1-01 PR [#920](https://github.com/hraaaaf/IAMINA-MVP/pull/920), branch `audit/v1-01-calculation-authority-20261009`, OPEN/DRAFT, last tested clinical-code SHA `63988a98a9b76ebdc82219b74f0ec42363274baa`, **17/17 exact-HEAD SUCCESS**. **This documentation status update creates a newer commit requiring its own CI; do not inherit the earlier check.**
- V1-02 PR [#921](https://github.com/hraaaaf/IAMINA-MVP/pull/921), branch `feat/v1-02-governed-intelligence-envelope-20261009`, HEAD `5b43f01de553a9111a52c5f2d6b228726ef8ef36`, OPEN/DRAFT, 2/2 workflows green. Not merged.
- Canonical audit: [`docs/assessments/2026-10-09-v1-01-calculation-authority-audit.md`](../assessments/2026-10-09-v1-01-calculation-authority-audit.md).
- User decision register [Notion](https://app.notion.com/p/3f377c663362812dbe78cead75e71922), [29-checkbox execution tracker](https://app.notion.com/p/3f477c6633628161aba2c43201805156), [master handover](https://app.notion.com/p/3f477c66336281b28c78eb11c22f5ee6).

## What was actually done

- CAL-07: AddLog and EditLog preserve entered number together with its unit when preference changes; unknown write unit rejected; Profile offers unit before target entries, converts to canonical mg/dL and preserves unchanged stored `69.9` through unit roundtrips; 390×844 overflow fixed. 12 actual Chrome PNGs and real Drift tests passed on verified candidates; no unrelated clinical threshold changed.
- **CAL-10 future-readings guard in candidate:** personal_response had no upper `now` bound while paired_meal did; bounded query and negative tests prevent future-dated journal records from manufacturing evidence sufficiency. On HEAD `40af4dc`, backend/PG CI was RED because an existing companion test advanced `evaluated_at` by one day without advancing its evidence clock. Follow-up test-only clock synchronization and API/memory negative regression are staged; verify exact-head CI before claiming pass. No new clinical threshold or day policy.
- Evidence across UTC/UTC+01 day boundary added for CAL-09/10: three engines count UTC `.date()`, while same samples can be one UTC+01 day. **Characterization, not approval of UTC as patient's clinical day.** Long-duration explicitly UUID-linked meal pair currently remains descriptively paired; no arbitrary time limit introduced.
- Active backend + Flutter glucose factor both `18.016`. Legacy helper still uses `18.018` with permissive fallback; AST test guards direct imports, not all possible dynamically imported callers.
- V1-02 governed engine envelope exists in #921 only partly; no complete Home/Reports/chat integration or patient-info third-party LLM path authorized.

## Open defects / clinical-human gates

1. CAL-01–12 full numerical and producer→consumer coverage incomplete; verify CGM eligibility, no promoted manual TIR/GMI/AGP, patient/consent isolation and PDF/LLM report provenance.
2. **CAL-09/10 timezone/clinical day policy** missing, potentially changes density classification; do not choose a day or pre/post window without clinical/product authority.
3. **CAL-11 nutrition reference truthfulness** and **CAL-12 exports/LLM** source lineage unclosed.
4. Clinical safety and independent adversarial review, security/privacy review, UX + RTL Arabic/a11y, V1-04 country/unit onboarding, release pre-real-patient P5-6A/#318 and P5-6B/#320 open.
5. No merge, no post-merge check and no Vercel or patient rollout. User must explicitly authorize any Vercel deployment; real-patient gate additionally requires professional/legal authorization.

## 29 decisions — delivery state, not coding percentage

**Approved:** 29/29. **Fully certified/delivered:** ✅ 0/29. **Active:** 🟡 #19 calculation/clinical audit, #22 coherent units, #28 governed intelligence. **No complete V1 lot verified underway:** ⬜ #1–18, #20–21, #23–27, #29 (26). Historical P5 engineering **6/12 closed** is a separate denominator.

## Next exact, and full remaining sequence

1. Read `docs/ROADMAP.md`, this handover and current audit. **Verify `main`, both PR HEADs, exact-head workflows** at GitHub (do not trust the static SHA if branch advanced).
2. Resume **CAL-09/10** `test_v1_01_evidence_day_boundaries.py` → verify three new **future-dated evidence exclusion** regressions in `personal_response` (source `logged_at`, legacy `created_at` fallback, paired-meal comparison), plus UTC/patient-local date boundary characterization; record clinician/product timezone and meal-pair policy gate without inventing medical thresholds.
3. CAL-11 supported-food invalid-grams and numeric source registry tests were **17/17 exact-head green on `a56e910`**, but exact individual USDA food rows are still unverified because primary download was inaccessible. Next, run **CAL-12 direct `LocalReportPdf.build` consumer guard** exact-head; do not connect the current untyped ASCII-only primitive to product UI as a clinical PDF. Map local Drift Reports versus guarded backend AI Summary versus administrative patient JSON export; require typed subject/provenance/consent/RTL and professional approval for future report. Complete CAL-01–12 independent oracles.
4. Reconcile V1-02/03 privacy boundary, obtain independent clinical/privacy/UX/RTL reviews; if passed, run exact final-head CI, closeout canonical docs and PR, decide merge subject to true clinical gates, verify post-merge, advance to V1-04. If blocked by clinic/release human gate, stop there and report exact gate; **never deploy to Vercel without explicit approval**.

**Effort next:** 🔴 clinical/timezone audit. **Roadmap forward authority remains `docs/ROADMAP.md`**, not this handover or Notion. Last review status: **OPEN / DRAFT / NOT RELEASE AUTHORIZED**.

## CAL-12 doctor-brief numerical guard — candidate (2026-10-09)

- Parent PR #920 HEAD `acb5a1cc3867619b8da626ee55f4a45b784d3b23`, draft; CI #37988641337 SUCCESS main job, some independent visual workflows in progress at initial inspection.
- Candidate route-only final-output fail-closed check (Unicode numerals and non-string model fields withheld) + isolated FR/EN/AR/Darija adversarial handler tests, no new clinical numeric authority, no schema or DB change.
- Important scope limit: spelled numbers/qualitative claims not covered; require typed evidence-bound deterministic brief, independent reviewers and actual exact-head CI. Clinical certification OPEN, no merge/Vercel.
- Next exact: verify new candidate GitHub Actions; diagnose failures; challenge clinical output in two independent perspectives; close CAL-12 only after qualified review and further typed/provenance controls.

## CI RED — registry throttling triage and repair candidate (2026-10-09)

- PR #920 CAL-12 `9b8df3bd846c62f6969519808c8e52c88749c520` main CI #37989573966: backend Ruff+pytest GREEN, PostgreSQL job #114020065551 RED *before any test*, because 3 unauthenticated `postgres:16-alpine` Docker Hub pulls were rejected with `toomanyrequests` (runner infrastructure, not diagnosed product failure).
- Narrow CI-only candidate: switch `.github/workflows/ci.yml` PostgreSQL service to verified-official repository `public.ecr.aws/docker/library/postgres:16-alpine`. Keep same major+Alpine tag, DB health, migration, tests, runtime unchanged.
- New candidate exact-head CI must prove image pull, healthy PostgreSQL, migrations and test suite + remaining workflows; registry availability is not yet proven by reading docs. If red again inspect exact log. No merge, no deploy. CAL-12 clinical/provenance gates remain open.

## 2026-10-09 CI red #2 — Dashboard Docker Hub pull cap

- **Proof:** parent `b5d799489dc73df5f24c08c36658707cda1070b2`: 16/17 exact-head workflows passed; full `CI` run #37990100247 passed backend, PostgreSQL (service mirror), and frontend. Dashboard visual run #37990100284 job #114021764081 FAILED *before images/test startup*, 3x `toomanyrequests` from independent `postgres:16-alpine` service in dashboard workflow. **No visual defect inferred**.
- **Minimal repair:** switch only `.github/workflows/dashboard-responsive-visual-cert.yml` service to `public.ecr.aws/docker/library/postgres:16-alpine`, same tag, DB, migration and screenshot steps. New exact-head run must prove 9/9 captures; previous 16/17 cannot be transferred as certification.
- **Next:** verify all 17 exact-head runs, inspect/repair any red, preserve clinician provenance/privacy and Vercel gates. No merge or deploy.

## V1-01 CAL-12 typed doctor brief candidate — 2026-10-09

- Last verified prior HEAD `4f49db75c60ddea01f78166996e897ff0af1bcbc`: 17/17 SUCCESS CI; Dashboard 9/9 distinct screenshots; PR #920 draft.
- Candidate removes free-form `GatewayLLM.complete` from `GET /ai/doctor-brief`, uses existing `assemble_consultation_brief` patient-bound typed contract and a new allowlisted deterministic locale formatter with source/version/evidence ID/window/unit/missingness in backward-compatible response metadata. Only descriptive recorded average is surfaced; invalid/unavailable data yields no claim, no third-party patient-context LLM. Synthetic FR/EN/AR/Darija negative and API schema tests; test of old LLM prompt removed, replaced with absence-of-egress negative.
- Need exact candidate SHA backend Ruff/pytest + PostgreSQL and all 17 workflows; inspect real HTTP auth/consent, mixed/demo/other-patient fixtures and mobile route consumers; clinical/privacy/locale independent reviewers required. Stop only on human gate; no merge/Vercel. Roadmap remains 0/29 delivered.
## CAL-12 red fix and sample count safety — 2026-10-09

- `d71258c6` CI #37998993533: SQLite lint/architecture pass; generated OpenAPI mismatch (JSON numeric literal normalization + stale doctor docs); PostgreSQL suite 2806 pass, one static outdated Doctor Brief LLM assertion failed. No proof of full green.
- Corrected OpenAPI via surgical text replacement preserving all unrelated floats/docs; obsolete static test now prohibits LLM in Doctor Brief; P2 assembler emits governed synchronized non-demo patient sample count and original average in one aggregate, with the old >=5 SQL minimum enforced a second time at typed evidence boundary. Exact window enforced; Django test covers other patient/demo never counting toward disclosure.
- New candidate CI needed; if red, inspect exact job logs and fix. Still human clinical/privacy/native-locale gate before merge; no Vercel.
- **HTTP contract regression candidate:** full Django Client GET `/api/v1/ai/doctor-brief?days=14` must reject unauthenticated requests, accept two distinct authenticated SessionAuth users, return strict patient-specific deterministic source-scoped `evidence`+body and never call model gateway. This is synthetic only and requires exact-head CI execution, not treated as authenticated clinical approval.

## CI red #37999657343 — OpenAPI schema ordering (2026-10-09)
- Parent `fa6d2b6`: 16/17 success. Only failed check `Backend — ruff + pytest` at OpenAPI exact-byte comparison; PG and Flutter/PWA jobs SUCCESS. Exporter appends `DoctorBriefEvidence` at end of components.schemas, whereas versioned JSON had it adjacent to `DoctorBriefResponse`. No product/runtime failure inferred.
- Fix candidate moves only that nested schema block to final component position, preserving all parsed schema values and other bytes. Verify via new exact-head CI. No merge or Vercel; clinician/privacy/native-locale gates still open.

## CAL-12 CI red #38005636789 — nested OpenAPI order (09/10/2026)

- Old HEAD `7801d68e` 16/17 SUCCESS, only backend `OpenAPI schema is current` failed; PG and frontend SUCCESS. Exact exporter diff `5883a5884,5943` means DoctorBriefEvidence belongs after SummaryRequest, immediately before DoctorBriefResponse. Previous attempt incorrectly moved it to end; correction limits to schema block order, no property changes.
- New HEAD must pass byte-identical `export_openapi` plus SQLite/PostgreSQL and all 17 workflows. Clinical/privacy/Arabic-Darija/RTL and consent gates still open; PR #920 draft, no merge/Vercel.

## 2026-10-09 CAL-12 CI OpenAPI two-line fix

- Parent `6608ba9`, [CI #38006477206](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38006477206), backend `OpenAPI schema is current` failure: generator deletes the checked-in `"default": null` on `DoctorBriefResponse.window_start` and `window_end`. Exact diff only those 2 lines (`5989d5988`, `6001d5999`), source/projection unchanged.
- Remove 2 generated-schema discrepancies only; JSON roundtrip comparison excludes precisely two default properties. Validate new HEAD and 17/17 workflows. Clinical independent human gates remain; no merge/deploy.

## CAL-12 typed Doctor Brief — engineering CI gate satisfied, clinical gate OPEN (2026-10-10)

**Result (verified last clinical-code HEAD `63988a9`):** [17/17 GitHub Actions PR workflows SUCCESS](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38006733937). Main CI included OpenAPI exact-byte parity (source of prior 4 red candidates), Ruff/import/anti-egress gates, SQLite 2806 passed (5 skipped, 3 xfailed), PostgreSQL 2810 passed (1 skipped, 3 xfailed), Flutter 671 passed (1 skipped), PWA build. Direct-caller test confirms untyped `LocalReportPdf.build` not invoked from the Dart product `lib/` tree; it remains syntactic ASCII-only PDF, deliberately rejecting Arabic/Unicode.

**What is proved:** authenticated GET `/api/v1/ai/doctor-brief?days=14` uses a deterministic `consultation-brief.v1` envelope with verified source/version/window, same patient-scoped/non-demo SQL aggregate count+average, count >=5 and safe literal FR/EN/AR/ar-MA descriptive text. Synthetic tests include untrusted source/version/other-patient/demo/few samples/wrong-window, actual HTTP auth/JSON serializer and absence of `GatewayLLM` on this handler.

**What is NOT proved:** independently medically approved average interpretation or copy, Arabic/Darija idiom or RTL/a11y rendering, clinical report PDF, authorized delivery consent or V1-03 whole-app model egress policy. Legacy `/ai/summary` and chat paths can still interact with models and require **separate** patient-context egress verification and remediation; do not treat this Doctor Brief route as blanket LLM safety. CAL-09/10 patient-local clinical-day policy and CAL-11 exact USDA food source rows unverified; no claim that CAL-01...12 are closed.

**Next (critical path):** new docs-only commit exact-head CI, then independent clinician + privacy/security + native-language/RTL review of Doctor Brief and PDF/clinical claims; authorize source/window/consent policy before exposing patient PDF. Finish CAL-01...12 source-to-consumer oracles and V1-03 other LLM egress audit. PR remains DRAFT/unmerged. Do not deploy Vercel without explicit owner approval; no progress change from 0/29 delivered.

## 2026-10-10 — CAL-09/12 partition safeguard candidate after 17/17 green

- Last independently verified HEAD `5ce6296`: [17/17 GitHub Actions SUCCESS](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38008210817), PR #920 draft/unmerged.
- Independent defect from `consultation_brief_assembler._eligible_logs`: inclusive `window_end` in recorded glucose SQL rows versus exclusive end for Companion review checkpoint, enabling one exact-boundary reading to appear in adjacent dossiers and potentially become the 5th non-demo sample used to authorize Doctor Brief.
- Minimal code fix only `consultation_effective_at__lte=window_end` → `__lt=window_end` (half-open `[start,end)`). Three Django DB tests target partition, null-logged fallback and true endpoint 5th-sample fail-closed behavior. No clinical day, period/meal threshold, localization, PDF or egress policy invented. New candidate requires **new exact-HEAD CI**, no success claimed yet.
- Next exact: run new CI Ruff/pytest/PG/Flutter/visual 17/17, fix any red; update Notion 29-item tracker with checked sub-jalon if proof acquired. Reviewer clinician/privacy/native AR/Darija/RTL remains mandatory, PR DRAFT no merge/Vercel, global 0/29 delivered.