# IAmina — Roadmap

> **Last updated:** 2026-07-26 — P0-MENA-1B semantic DLP merged; P0-MENA-1C granular raw-media consent in final validation.
>
> **Authority:** this file is the **single forward tracker**. Historical phase numbers, completed chassis work, old provider plans, and prior strategy belong in git history, ADRs, assessments, or `docs/architecture/ARCHITECTURE-TIMELINE.md` — not in the active backlog.

## North star

Ship a **safe, measurable MENA diabetes companion** to one founder-selected pilot cohort, then use real retention and payer evidence to decide whether IAmina deserves expansion.

### Product constraints

- One live condition: **diabetes**.
- MENA is the target region; rollout is country-by-country and locale-by-locale.
- French, Modern Standard Arabic, and English are baseline language options.
- Dialects are user-selected and enabled only after native review + safety parity.
- Location may suggest settings; it never silently determines language, dialect, consent, emergency resources, or clinical behavior.
- IAmina is a **companion**, not a diagnostic or prescribing system.
- Deterministic clinical/safety logic decides. External models may only verbalize approved minimized results or perform explicitly permitted media tasks.
- No second disease module before the Retention Gate passes.

---

# P0 closeout ledger

This section records only recently completed P0 foundations whose operational meaning still affects the next work.

## ✅ P0-A — API safety boundaries — MERGED

Closed on 2026-07-23.

- Session/cookie-authenticated API writes are no longer covered by a blanket `/api/` CSRF exemption.
- Bearer-token/bootstrap behavior remains supported without weakening cookie/session CSRF protection.
- `UnitGuardMiddleware` covers legacy and registry-mounted module paths such as `/api/v1/diabetes/...`.
- Unexpected unit-normalization failures are **fail-closed**, not fail-open.
- Authoritative deterministic triage classification was moved to shared `core` safety ownership instead of creating a `core → diabetes` dependency.
- Regression coverage and the full repository CI were green before merge.

## ✅ P0-B — Server-side AI egress authorization boundary — MERGED

Closed on 2026-07-23.

Implemented foundation:

- central provider-agnostic `core.ai_egress` authorization boundary;
- explicit patient, purpose, and modality scope for live external model/media operations;
- server-side consent check immediately before real egress;
- default-deny behavior for missing scope, missing consent, unknown purpose, or undeclared modality;
- live text, STT/audio, vision/OCR, document, chat, summary, and doctor-brief call paths wired to the boundary;
- CI anti-bypass rule preventing new direct external AI callsites from omitting the authorization assertion;
- deterministic emergency/safety behavior remains usable without AI consent unless a real external call is attempted.

## ✅ P0-MENA-1A — Text payload allowlist and minimisation contract — MERGED

Closed in PR #10 after green SQLite, PostgreSQL, OpenAPI, security, Flutter and migration-drift gates.

- external text providers resolved by `llm.factory` are policy-decorated before network-capable `complete`, `stream`, or `think` operations;
- text egress accepts exactly `system_prompt` and `user_prompt` fields;
- missing/unknown fields, non-string values, NUL bytes, missing consent and oversized purpose-specific payloads fail closed;
- authorized payloads are immutable after validation;
- tests prove a rejected consent or payload cannot invoke the underlying provider;
- concrete provider types, rate guards and provider-name reporting remain unchanged.

## ✅ P0-MENA-1B — Semantic redaction / DLP contract — MERGED

Closed in PR #11 after green SQLite, PostgreSQL, OpenAPI, security, Flutter and migration-drift gates.

- deterministic, provider-agnostic inspection runs at the existing `authorize_text_payload` egress boundary;
- email, phone, Moroccan national identifiers, UUIDs, Firebase-style UIDs and dates of birth are rejected before provider invocation;
- explicit identity labels in French, English and Arabic are rejected;
- Unicode NFKC normalization and invisible-format removal prevent trivial obfuscation bypasses;
- only documented pseudonymization placeholders survive the DLP contract;
- logs record finding categories only and never the rejected payload value;
- `complete`, `stream` and `think` cannot invoke the provider after DLP denial;
- the contract does not claim perfect inference of unlabelled natural-language names or postal addresses.

## 🟡 P0-MENA-1C — Granular raw-media consent — IN VALIDATION

Implementation PR: #12, branch `fix/p0-mena-granular-media-consent`.

- global AI consent remains a mandatory baseline;
- raw audio, image and document egress additionally require an active exact patient + purpose + modality grant;
- historical global consent is deliberately not converted into media authorization;
- grants are unique, revocable and checked immediately before real egress;
- one purpose cannot authorize another purpose and one modality cannot authorize another modality;
- tests prove fail-closed behavior, purpose isolation, modality isolation and immediate revocation;
- migration drift and the first complete SQLite/PostgreSQL CI run are green.

**Status rule:** this LOT is not complete until the final documentation commit passes repository CI and PR #12 is merged.

**Operational boundary:** backend enforcement is implemented. A patient-facing grant/revoke workflow remains required before raw-media features can be enabled for real patients.

## ✅ P0-C — Clinical analytics correctness + PostgreSQL parity — MERGED

Closed on 2026-07-23 in PR #4.

- GRI corrected against the normative disjoint-zone formula;
- patient-facing GRI fails closed until valid CGM coverage can be proven;
- SQLite/PostgreSQL daily analytics parity corrected;
- PostgreSQL 16 full-suite CI established as source of truth;
- normative regression fixtures added.

## ✅ P0 Migration Drift — MERGED

Closed on 2026-07-26 in PR #9.

- `DiabetesProfile` migration state reconciled with `SeparateDatabaseAndState` and no unnecessary database ALTER;
- permanent `python manage.py makemigrations --check --dry-run` workflow gate installed.

---

# NOW — pilot-critical path

Work top-down. Do not pull SOON/GATED work forward unless it becomes a direct blocker.

## P0-MENA-1 — Complete the outbound AI/data-egress contract

**Goal:** no uncontrolled or insufficiently governed provider call leaves the application.

### Completed foundation

- [x] Inventory and wire the currently live text, STT/audio, vision/OCR, document, summary/brief, chat and gateway egress paths into one authorization boundary.
- [x] Require a registered purpose + modality + authenticated patient scope for live external operations.
- [x] Enforce server-side AI consent immediately before external egress.
- [x] Add CI enforcement against new unauthorized direct provider callsites.
- [x] Default-deny missing scope, missing consent, unknown purpose, and undeclared modality.
- [x] Enforce a structured text-provider field allowlist at the central factory boundary.
- [x] Enforce and test purpose-specific text payload size ceilings before provider invocation.
- [x] Strengthen deterministic DLP rules for contact details and high-confidence identifiers.
- [ ] Introduce purpose/modality-granular media consent for raw audio/images/documents. **Implementation and first CI complete; awaiting final CI + merge.**

### Remaining P0-MENA-1 work

- [ ] Expose an authenticated patient-facing grant/revoke workflow before enabling raw-media features for real patients.
- [ ] Attach approved processor/subprocessor, residency, retention/no-training, and legal-basis metadata to each egress policy.
- [ ] Remove or deliberately isolate remaining provider-specific/direct runtime seams so provider choice is downstream of policy.
- [ ] Add provider timeouts, streaming timeouts, typed failure handling, and safe frontend error UX.
- [ ] Verify fallback paths cannot bypass the same policy.

### Data-egress acceptance gate

No external model provider receives, by default:

- name, email, phone;
- Django/Firebase UID or national identifier;
- date of birth or address;
- raw conversation history;
- raw unrelated clinical logs;
- unrelated health data.

Raw audio/images/documents remain sensitive even when text fields are absent. Each approved media flow requires explicit purpose, appropriate consent, a documented processor/retention policy, and proof that only the minimum required media is transmitted.

**Done when:** tests and CI prove both **no provider bypass** and a complete explicit outbound payload/media policy contract.

---

## P0-MENA-2 — Define and enforce the locale + safety contract

**Goal:** language expansion cannot weaken safety.

- [ ] Model separately: country/region, UI language(s), response language, script/transliteration preference, dialect(s), units, and time zone.
- [ ] Ask the user to confirm language/dialect choices; location may only suggest.
- [ ] Define deterministic fallback order to MSA / English / French.
- [ ] Complete RTL coverage for enabled Arabic-script experiences.
- [ ] Create country-specific emergency-resource configuration with explicit source/date ownership.
- [ ] Build native-speaker safety-parity corpora for every enabled language/dialect.
- [ ] Close the existing Darija high-severity orthographic-variant gap before any real-patient pilot.
- [ ] Require identical safety intent coverage across text, voice transcript, mixed-language, and transliterated input.

**Done when:** the first pilot locale passes native review, safety-equivalence tests, emergency-resource validation, and UX/script checks.

---

## P0-MENA-3 — Migrate sovereignty-critical authentication

**Goal:** Django-native identity becomes the target source of truth without losing existing users.

- [ ] Specify Django account lifecycle: signup/invite, login/session/token strategy, verification, password reset, abuse controls, account recovery, deletion.
- [ ] Map legacy Firebase identities to Django accounts.
- [ ] Design duplicate/lost-account reconciliation and rollback.
- [ ] Implement migration tests before removing Firebase dependencies.
- [ ] Replace Flutter Firebase auth/token handling only after migration and rollback are proven.
- [ ] Add appropriate rate limiting and stronger authentication controls for staff/professional accounts.

**Done when:** account-preserving migration is tested end-to-end and Firebase is no longer sovereignty-critical.

---

## P0-MENA-4 — Benchmark the multimodal provider stack

**Goal:** choose providers by evidence, not preference.

Benchmark **text, STT, and vision independently** on:

- privacy and data residency;
- contractual no-training/no-retention terms;
- MENA language/dialect quality;
- safety consistency;
- latency and availability;
- cost per active patient;
- operational fallback options;
- local/on-device feasibility where useful.

- [ ] Build representative MENA evaluation sets.
- [ ] Run benchmark with minimized/synthetic test data only.
- [ ] Document decision matrix and rejected alternatives.
- [ ] Approve provider cutover only after privacy + quality gates pass.

**Done when:** each modality has an explicit approved architecture and fallback policy.

---

## Pilot safety/compliance gate — before one real patient

All items below are hard blockers unless the founder records an explicit defer decision with rationale.

- [ ] Deterministic insulin-dose/treatment request refusal proven not to call an LLM.
- [ ] Doctor-facing/summary outputs proven to pass the same no-prescription policy.
- [ ] Emergency events route to a **monitored human channel** or the product explicitly adopts a documented self-care-only operating mode.
- [ ] Darija orthographic high-severity safety gap closed.
- [x] Base AI/model consent enforced server-side at the outbound boundary.
- [ ] Granular raw-media consent workflow exposed to patients; backend enforcement is in PR #12.
- [ ] Consent matrix + processor/subprocessor register documented.
- [ ] Cross-border/data-residency assumptions documented for the pilot country.
- [ ] Data export implemented or an operationally valid export process documented for the closed pilot.
- [ ] Retention/deletion schedule defined.
- [ ] Incident response and escalation procedure defined.
- [ ] Pilot onboarding, monitoring, escalation, and exit checklist approved.
- [ ] No committed/reachable secrets remain; exposed keys are rotated.

---

## Deployment + pilot

- [ ] Reproducible development path validated on supported developer environments.
- [ ] Backend deployed to staging with PostgreSQL, Redis, TLS, domain, backups, logging, and smoke tests.
- [ ] First pilot country/cohort selected by founder.
- [ ] First pilot locale passes P0-MENA-2 gate.
- [ ] Recruit approximately 30 real patients through an appropriate supervised/controlled channel.
- [ ] Turn on retention instrumentation against real users.
- [ ] Founder sets explicit D90 go/stop threshold before reading outcomes.

---

# RETENTION GATE — expansion decision

Do not build condition #2 or broad platform scope until **both** are true:

1. **D90 retention meets the founder-set go threshold** (25% may be used only as a provisional placeholder until explicitly decided).
2. **One credible payer/distribution signal exists**, such as a named pharma adherence pilot, insurer/clinic commitment, or meaningful Gulf consumer traction.

If the gate fails, diagnose retention/business-model causes before adding conditions or platform complexity.

---

# SOON — after pilot-critical blockers, before broader release

- [ ] Frontend widget/integration testing for pilot-critical flows.
- [ ] Accessibility baseline for high-value patient flows.
- [ ] Dependency/security scanning and measured coverage thresholds.
- [ ] Production-grade load and failure testing.
- [ ] MFA/strong auth for staff and future professional roles.
- [ ] Complete observability-data retention policy.
- [ ] Retire legacy `dev.sh` / `dev.ps1` after Docker-first workflow is proven.
- [ ] Remove dead provider/Firebase code only after migration/cutover is complete and rollback window closes.

---

# BUSINESS VALIDATION — founder-owned, parallel

- [ ] One-page monetization memo: channel hypotheses, cost per active patient, payer logic.
- [ ] Competitive landscape focused on why IAmina wins for selected MENA language/dialect cohorts.
- [ ] At least 5 structured market conversations: clinicians/distributors + pharma/insurer/patient-support stakeholders.
- [ ] Re-source any market claims before external/investor use.

---

# GATED — explicitly not now

- Second disease module, including hypertension.
- Third-party plugin marketplace or broad external module ecosystem.
- Worldwide language coverage.
- Multi-tenant enterprise platform machinery without a validated business need.
- Any feature that expands clinical decision authority into diagnosis, prescribing, or treatment optimization without a separate regulatory/product decision.

---

# Completed foundations — summary only

See git history and `docs/architecture/ARCHITECTURE-TIMELINE.md` for the detailed chronology. The completed platform chassis includes modular registry/routing, first-party diabetes extraction, legacy compatibility, unified patient data, analytics foundations, security/compliance foundations, testing infrastructure, schema governance, migration drift enforcement, and the initial MENA outbound-AI authorization and text-payload contracts.
