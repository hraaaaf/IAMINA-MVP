# IAmina — Fable Assessment Report

**Date:** 2026-06-12
**Branch assessed:** `dev` @ `d96ae44` (post P6-A + P8.1 + audit port)
**Method:** Five parallel deep-dive reviews (architecture/backend, security/privacy, frontend/UX, docs/roadmap/business, testing/DevOps), cross-verified against the repo where claims conflicted. Scores are 0–10; they reflect *state today relative to the project's own stated goals* (Morocco-market Darija/Arabic diabetes companion, pre-PMF, not a medical device).

---

## 1. Scorecard

| # | Dimension | Score | One-line verdict |
|---|-----------|:-----:|------------------|
| 1 | Architecture | **8.5** | Chassis/module split is real, CI-enforced, and honestly debt-tracked |
| 2 | Backend code quality | **8.0** | ~90% type hints, small focused functions; a few oversized files |
| 3 | Security | **8.0** | Solid foundations; no secrets in git (verified); minor hygiene items |
| 4 | Privacy / GDPR | **8.0** | Erasure hooks, audit trail, PHI stripping before LLM; audit-log gaps |
| 5 | Medical safety | **8.5** | Append-only triage registry + unit guard are first-class; keyword gaps known |
| 6 | Testing | **8.0** | 764 real behavioral tests on critical paths; no coverage gate; thin Flutter tests |
| 7 | CI/CD | **7.0** | Meaningful gates (ruff, pytest, bandit, import-linter); no coverage, no deploy |
| 8 | DevOps / operations | **7.0** | Production-grade Docker, good observability code; no alerting/aggregation |
| 9 | Frontend code quality | **7.5** | Clean module seam and robust sync; 2,500-line widgets, silent catches |
| 10 | UX | **7.0** | Thoughtful flows (express log, empty states); held back by i18n/RTL gaps |
| 11 | Localization / market readiness | **5.0** | **Weakest area.** Hardcoded French clinical strings + no RTL scaffold in an Arabic-first market |
| 12 | Documentation | **8.5** | 8 ADRs, living roadmap, MISTAKES.md error log — rare discipline at this stage |
| 13 | Roadmap | **7.5** | Coherent and phased; the business-critical retention gate is under-resourced |
| 14 | Business case | **7.0** | Clear beachhead/monetization story; thin on validation evidence |
| 15 | Product discipline | **6.5** | Heavy platform refactor pre-PMF; Phase 16 (the #1 metric) has no code or owner |
| 16 | Repo hygiene | **7.5** | Clean tracked set, good .gitignore; stale branches, one stray symlink |
| | **Overall (weighted judgment)** | **7.6** | Engineering quality outruns product validation |

---

## 2. The headline finding

**The engineering is ahead of the business.** This codebase is unusually mature for a POC — enforced architectural boundaries, 764 behavioral tests, append-only safety registries, ADR discipline. But the project's own documents declare *90-day retention* the #1 metric and the gate for the entire platform investment, and that measurement loop is the least-built part of the system: the retention SQL exists and is tested, but the dashboard endpoint is only partially wired, the D90 threshold is still a placeholder (≥25%) after 60+ days, and Phase 16 has no owner or subtasks. Meanwhile, the product that must *earn* that retention — a Darija/Arabic companion — still shows hardcoded French meal types and lacks an RTL layout scaffold. The two cheapest, highest-leverage fixes in this repo are i18n string extraction and finishing the retention dashboard; neither is an architecture problem.

---

## 3. Dimension-by-dimension reasoning

### 3.1 Architecture — 8.5

| Aspect | Finding |
|--------|---------|
| Chassis/module seam | Real, not aspirational: `core/contracts/`, `core/registry.py` ModuleRegistry, `diabetes/manifest.py`, dynamic router loop |
| Enforcement | `backend/.importlinter` + CI step: companion⊥modules (strict), core⊥modules (allow-listed debt) — boundaries are machine-checked, not tribal knowledge |
| Honest debt | Remaining core→diabetes leaks (auth→DiabetesProfile, triage→classifier) are explicitly allow-listed and tracked, not hidden |
| Companion contract | Single `analyze() → DomainContext` engine contract (P4.5) replaced ad-hoc coupling; companion imports zero module code (guard-tested) |
| Data split | `BasePatientProfile` / `DiabetesProfile` / `PatientModule` junction done with `SeparateDatabaseAndState` migrations — table preserved, low-risk |

**Why not higher:** the two allow-listed leaks sit on sensitive paths (login, triage); the clinical engine file is ~855 LOC; the triage middleware imports the classifier at runtime (defensible for safety, but it's a coupling the linter can't see). The architecture is also *expensive* relative to one shipped module — see Product discipline.

### 3.2 Backend code quality — 8.0

Strengths: ~90% type-hint coverage with `TYPE_CHECKING` patterns, functions averaging 30–50 LOC, no wildcard imports, consistent docstrings, graceful-degradation error handling matching the documented `except → log → FallbackProvider` convention, clean migration hygiene. Weaknesses: a handful of oversized files, inconsistent logging style across apps, the eager `DiabetesProfile` creation in the auth path (known, queued as next task).

### 3.3 Security — 8.0

| Severity | Finding | Status |
|----------|---------|--------|
| ~~Critical~~ **False positive** | "Real API keys in committed `.env`" | **Verified false**: `git ls-files` shows only `.env.example` files with placeholder values; `.env` and `firebase-credentials.json` are git-ignored. (The historical exposure noted in CLAUDE.md was revoked.) |
| Low | `retention_sql.py:249,280` builds SQL via `.format(acq=...)` | Mitigated: value comes from module manifests (developer-controlled), guarded by a quote-rejection check, endpoint is staff-only. Still, switch to parameterized queries — `.format` into SQL is a habit that eventually bites |
| Low | CSRF exemption ordering for stateless Bearer auth | Correct today, fragile if middleware order changes — document the assumption (middleware order is already a "never touch" rule) |
| Good | Firebase JWT verification, object-level isolation (tested: user A cannot read user B's logs), staff-only analytics, parameterized clinical SQL, bandit in CI | — |

The score reflects strong fundamentals minus the absence of rate limiting on auth-adjacent endpoints and no dependency-audit step (e.g., `pip-audit`) in CI.

### 3.4 Privacy / GDPR — 8.0

`on_account_delete` hooks with Firebase deletion, `ErasureRecord` immutable trail, consent gating in the Flutter router (RGPD Art. 7), `PHIPseudonymizer` (names, DOB, CIN) + `PHIStrippingMiddleware` upstream of all LLM calls, and the "English Pivot Text only" convention. Gaps: audit-log coverage isn't complete across all data-touching endpoints, and there's no documented data-retention schedule for observability events (which store `patient_id`).

### 3.5 Medical safety — 8.5

The strongest design work in the repo. `TriageVitalMiddleware` is upstream of all AI logic, backed by `AppendOnlyTriageRegistry` (registrations cannot be removed at runtime), multilingual (FR/Darija/Arabic) with a 2-class classifier separating suicidal ideation from glycemic emergency, returning fixed pre-validated responses that never touch the LLM. `UnitGuardMiddleware` normalizes glucose units (mg/dL↔g/L↔mmol/L) with physiological bounds before anything downstream sees a value. **Known gap, honestly tracked:** one xfail documents that orthographic variants of suicidal ideation in Darija aren't covered — flagged "to cure with native corpus before real patient pilot." That must be a hard launch blocker, not a soft one.

### 3.6 Testing — 8.0

| What | Evidence |
|------|----------|
| Volume vs. substance | 764 passed / 3 xfailed across 46 files — and they assert behavior (e.g., isolation test asserts user2's log absent from user1's response), not implementation |
| Critical-path coverage | Triage (3 layers incl. malformed JSON), all clinical detectors with P0 regression guards (CV>36% ADA fix), LLM fallback chain + PHI masking, sync idempotency (Dart side too) |
| Fixture hygiene | Single Firebase mock in `conftest.py`, `reset_hooks()` isolation, factory helpers |
| Gaps | No `pytest-cov` → coverage % unmeasured and ungated; Flutter has only ~9 test files (sync, consent, connectivity) with widget/E2E deferred; no parallel execution |

### 3.7 CI/CD — 7.0 and 3.8 DevOps — 7.0

CI runs ruff, import-linter, bandit (HIGH-only), pytest, and `flutter analyze` with sensible caching — every check is meaningful. Missing: coverage reporting, `manage.py check`, Flutter version drift (CI 3.41.0 vs local 3.41.7), and any deployment stage — CI is gates-only. Ops side: multi-stage non-root Dockerfile, compose with health-check-gated startup (Postgres 16, Redis with LRU cap), tuned gunicorn. The observability *code* (ClinicalLogger structured JSON, `track()` events, retention SQL) is good, but nothing ships logs anywhere, and **clinical emergency events trigger no alert** — for a medical companion, that's the first ops gap to close before any pilot.

### 3.9 Frontend code quality — 7.5 and 3.10 UX — 7.0

| Strength | Evidence |
|----------|----------|
| Module seam mirrors backend | `lib/modules/` registry generates routes/nav; offline fallback activates all modules if the API is unreachable |
| Offline-first done right | Drift schema v5 with migrations; `client_uuid` UNIQUE = idempotent batch sync; 3-attempt retry with dead-letter flags |
| Considered UX | Express (3-tap) vs detailed log entry; skeleton/empty states with CTAs; clinical color zones; 401 refresh + exponential backoff in the API client |

| Weakness | Evidence |
|----------|----------|
| Giant widgets | `add_log_sheet.dart` ≈ 2,558 lines; `amina_chat_view.dart` ≈ 967 |
| Silent failures | `catch (_)` blocks in `api_client.dart` return null/empty — timeout, 401, and network errors indistinguishable when debugging field sync issues |
| Accessibility | Touch targets ≥48px mostly hold, but no `Semantics` labels on glucose readings — screen readers lose clinical context |

### 3.11 Localization / market readiness — 5.0 ⚠️

This gets its own row because it is *the* gap between the codebase and the stated business. The strategy says Darija/Arabic-first; the code says:

- Hardcoded French clinical strings in the most-used screen: meal types (`'À jeun'`, `'Iftar'`, `'Suhoor'`) and zone labels (`'Hypoglycémie'`) in `add_log_sheet.dart` bypass the otherwise-good arb files (110+ keys in `app_ar.arb`).
- **No global RTL scaffold.** Only chat bubbles detect RTL via regex; navigation, text fields, and forms assume LTR. An Arabic-locale user gets Arabic text in a mirrored-wrong layout.
- mg/dL appears hardcoded on chart axes rather than respecting the profile unit preference.

None of this is hard to fix (extract strings, wrap in `Directionality`, bind chart units to the profile), which is exactly why a 5 is fair: high impact, low cost, not yet done.

### 3.12 Documentation — 8.5

Eight ADRs including ADR-0008 documenting a strategy *reversal* (most teams bury those), a living phased roadmap, `MISTAKES.md` as a 19-entry error journal, `TECHDEBT.md` with a checked-off history that matches git reality, MEDICAL_DATA_PLAN, migration runbooks, and session-state continuity in CLAUDE.md/STATE.md. Cross-checks between docs claims and code found only minor drift (e.g., detector count 10 vs "8 detectors" in older notes; the retention dashboard described as done in one doc while the endpoint wiring is partial). Deductions for those staleness pockets and for the multi-version architecture docs (v1.0→v3.1) accumulating without a clear "you only need to read X" pointer beyond new-architecture.md.

### 3.13 Roadmap — 7.5, 3.14 Business case — 7.0, 3.15 Product discipline — 6.5

The roadmap is genuinely sequenced (P0 security → P2 data split → P3 registry → P4.5 contract → P6 frontend seam → P8.1 enforcement pulled forward sensibly), with gated items explicitly parked. The business framing is coherent and unusually self-aware on regulation: companion-not-device positioning, with the triage middleware doubling as the compliance argument; Morocco beachhead, Gulf + pharma B2B monetization.

Three things keep these scores from being higher:

1. **The gate has no engine.** D90 retention is named the #1 metric and the go/no-go for platform investment, yet the threshold is a placeholder, Phase 16 has no owner/subtasks, and the measurement dashboard is unfinished. A gate nobody can read is not a gate.
2. **Platform before PMF.** Multiple phases of chassis work (P0–P8.1) were executed for a product with one module and, as far as the docs show, no real patients yet. The docs *do* justify it (multi-condition Gulf/pharma story, seams-not-platform per the DA-03 memo), and the execution was cheap-ish because it was disciplined — but it's still weeks of optionality-building ahead of evidence the core loop retains users.
3. **Monetization is asserted, not evidenced.** Gulf expansion and pharma B2B appear as direction statements; there's no documented customer conversation, pricing hypothesis, or pilot pipeline. Fine at POC stage, but the docs are otherwise so rigorous that the asymmetry stands out.

### 3.16 Repo hygiene — 7.5

484 tracked files, no `db.sqlite3`/`__pycache__`/venv in git, secrets properly ignored, conventional commits consistently applied with phase references. Dings: a stray tracked `flutter_sdk/flutter` symlink, ~20 stale branches, no CODEOWNERS or documented branch protection, no `.gitattributes`.

---

## 4. Corrections to raw review findings (for the record)

| Claimed | Verified reality |
|---------|------------------|
| "Critical: `.env` with real Gemini key + SECRET_KEY committed to git" | **False.** Only `.env.example` placeholders are tracked; `.env` is ignored. (Historical key exposure was already revoked per CLAUDE.md.) |
| "SQL injection in `retention_sql.py:280`" | Overstated. `.format()` into SQL is bad hygiene, but the input is a developer-controlled manifest constant with a quote guard, on a staff-only endpoint. Fix it; don't page anyone. |
| "8 clinical detectors" (docs) | Code has 10 — docs slightly stale, in the good direction. |

---

## 5. Prioritized recommendations

| Priority | Action | Why now |
|:--------:|--------|---------|
| **P0** | Finish the retention dashboard endpoint + set a real (even provisional) D90 threshold with an owner | It's the project's own declared gate; everything else is downstream of this number |
| **P0** | Extract hardcoded French clinical strings to arb files + wrap the app in a locale-driven `Directionality` | Cheapest fix with the largest impact on the actual target user |
| **P1** | Wire ClinicalLogger emergency events to an alert channel before any patient pilot | A triage middleware that fires into an unread log file protects no one |
| **P1** | Close the Darija orthographic-variant xfail with a native corpus — treat as a hard pilot blocker | The one known hole in the safety net |
| **P1** | Fix the auth→DiabetesProfile eager creation (already queued) and parameterize `retention_sql.py` | Burns down both remaining core→diabetes debts on sensitive paths |
| **P2** | Add `pytest-cov` with a threshold; align CI Flutter version; add 3 Flutter integration tests (login→log→sync) | Locks in the test quality you already have |
| **P2** | Split `add_log_sheet.dart`; replace `catch (_)` with typed handling + logging | Maintainability + field debuggability |
| **P3** | Branch cleanup, CODEOWNERS, remove `flutter_sdk` symlink | Hygiene |

---

## 6. Bottom line

A disciplined, safety-conscious codebase with documentation habits most funded teams lack, scoring **~7.6/10 overall**. Its risk is not technical debt but **inverted priorities**: the platform optionality is built and enforced, while the retention measurement that justifies it and the Arabic-first experience that must drive it are both unfinished. Two focused weeks on i18n/RTL + the retention loop would raise the lowest scores on this card by more than any further architecture work could.
