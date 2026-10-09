# IAMINA V1-01 — CANONICAL RESUME HANDOVER — 2026-10-09

> **Authority:** `docs/ROADMAP.md` always wins for progress and next work; this file is a compact operational handover, not a second roadmap. New session: read this file, then check live GitHub branch/PR/CI and Notion before continuing. Evidence does **not** imply clinical certification.

## Goal / observable success / proof

**Goal:** patient-safe, source-traceable deterministic calculations and coherent glucose-unit rendering/storage, with no unsanctioned normative output or external patient-context model call.

**Success:** each CAL-01…12 source/transformation/consumer known; invalid/missing/insufficient-data negative tests, bounded conversions, patient scope, SQLite+PostgreSQL, API and real UI consistent; competent clinical/privacy reviewers approve where required; full exact-head and post-merge evidence. **Current success = not reached.**

**Proof obtained on the last fully tested PR #920 code HEAD** `dddcd7ff7d66d034b74734ff7ad00bcd64ec2c4b`: [17/17 workflows green](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/37971565469), backend/PG/Flutter/Chrome; static import AST regression for the legacy permissive unit converter passed. [Chrome 12 PNG source](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/37969874302/artifacts/11635771127) on predecessor `b0e971e...` confirms six BEFORE/AFTER surface pairs, 390×844 and 768×1024. Provisional visuals **8/10 locally**, not clinical release evidence. Current last tested `main`: `13b7cce12c86daf60119fb703f22e8c6c192cf8d`.

## Repository / branches / PRs

- Repo `hraaaaf/IAMINA-MVP`.
- V1-01 PR [#920](https://github.com/hraaaaf/IAMINA-MVP/pull/920), branch `audit/v1-01-calculation-authority-20261009`, OPEN/DRAFT, last fully-tested code SHA `dddcd7ff7d66d034b74734ff7ad00bcd64ec2c4b`. **Documentation updates after it generate newer SHA and need exact-head CI.**
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
3. Audit CAL-11 nutrition provenance, then CAL-12 reports/export/LLM projection; finish CAL-01–12 source→consumer matrix with SQLite/PG, Flutter/real navigation and adversarial test results.
4. Reconcile V1-02/03 privacy boundary, obtain independent clinical/privacy/UX/RTL reviews; if passed, run exact final-head CI, closeout canonical docs and PR, decide merge subject to true clinical gates, verify post-merge, advance to V1-04. If blocked by clinic/release human gate, stop there and report exact gate; **never deploy to Vercel without explicit approval**.

**Effort next:** 🔴 clinical/timezone audit. **Roadmap forward authority remains `docs/ROADMAP.md`**, not this handover or Notion. Last review status: **OPEN / DRAFT / NOT RELEASE AUTHORIZED**.
