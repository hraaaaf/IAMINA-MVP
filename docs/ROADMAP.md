# IAmina — Roadmap

> **Last updated:** 2026-07-26 — P0-MENA-1C granular raw-media consent merged; P0-MENA-1D patient consent-management API in final validation.
>
> **Authority:** this file is the single forward tracker. Historical implementation detail belongs in git history, ADRs and architecture timelines.

## North star

Ship a **safe, measurable MENA diabetes companion** to one founder-selected pilot cohort, then use real retention and payer evidence to decide whether IAmina deserves expansion.

### Product constraints

- One live condition: diabetes.
- MENA rollout is country-by-country and locale-by-locale.
- French, Modern Standard Arabic and English are baseline languages.
- Dialects require explicit user selection, native review and safety parity.
- Location may suggest settings; it never silently determines language, consent, emergency resources or clinical behavior.
- IAmina is a companion, not a diagnostic or prescribing system.
- Deterministic clinical and safety logic decides; external models receive only approved minimized data.
- No second disease module before the retention gate passes.

---

# P0 closeout ledger

## ✅ P0-A — API safety boundaries — MERGED

Closed on 2026-07-23.

- Session/cookie API writes remain under CSRF protection.
- Bearer-token/bootstrap behavior remains supported.
- `UnitGuardMiddleware` covers legacy and namespaced diabetes routes.
- Unexpected normalization failures fail closed.
- Authoritative deterministic triage lives in shared `core`.

## ✅ P0-B — Server-side AI egress authorization — MERGED

Closed on 2026-07-23.

- Central provider-agnostic `core.ai_egress` boundary.
- Explicit patient, purpose and modality scope.
- Server-side consent checked immediately before real egress.
- Missing scope, consent, purpose or modality fails closed.
- Text, STT/audio, vision/OCR, documents, chat, summaries and doctor briefs are wired.
- CI prevents new unauthorized provider callsites.

## ✅ P0-MENA-1A — Text payload allowlist and minimisation — MERGED

Closed in PR #10.

- External text providers are decorated at the factory boundary.
- Only `system_prompt` and `user_prompt` are accepted.
- Missing or unknown fields, invalid values, NUL bytes and oversized prompts fail closed.
- Authorized payloads are immutable.
- Rejected consent or payload cannot invoke the provider.

## ✅ P0-MENA-1B — Deterministic semantic DLP — MERGED

Closed in PR #11.

- Email, phone, Moroccan identifiers, UUIDs, Firebase-style UIDs and birth dates are rejected before provider invocation.
- Explicit identity labels in French, English and Arabic are rejected.
- Unicode normalization and invisible-character removal block trivial bypasses.
- Only documented pseudonymization placeholders survive.
- Logs record finding categories, never rejected values.
- The contract does not claim perfect inference of unlabelled names or addresses.

## ✅ P0-MENA-1C — Granular raw-media consent — MERGED

Closed in PR #12 after green SQLite, PostgreSQL, OpenAPI, security, Flutter and migration-drift gates.

- Global AI consent remains mandatory.
- Raw audio, image and document egress additionally require an active exact `patient + purpose + modality` grant.
- Historical global consent is not converted into media authorization.
- Grants are unique, revocable and checked immediately before egress.
- Purpose and modality isolation are regression-tested.

## 🟡 P0-MENA-1D — Patient media-consent management API — IN VALIDATION

Implementation PR: #13, branch `feat/p0-mena-media-consent-api`.

- Authenticated patients can list every supported media-consent option and its active or revoked state.
- Grant and revoke operations derive ownership exclusively from `request.user`.
- No client-supplied patient identifier is accepted.
- Grant requires active global AI consent.
- Grant and revocation are idempotent.
- Unsupported purpose/modality pairs fail closed.
- Generated OpenAPI and ownership/isolation tests are included.

**Status rule:** this lot is complete only after the final SHA passes all repository gates and PR #13 is merged.

## ✅ P0-C — Clinical analytics correctness + PostgreSQL parity — MERGED

Closed in PR #4.

- GRI corrected against the normative disjoint-zone formula.
- Patient-facing GRI fails closed until valid CGM coverage is proven.
- SQLite/PostgreSQL analytics parity corrected.
- PostgreSQL 16 full-suite CI is a source-of-truth gate.

## ✅ P0 migration drift — MERGED

Closed in PR #9.

- `DiabetesProfile` migration state reconciled without unnecessary database ALTER.
- Permanent `makemigrations --check --dry-run` CI gate installed.

---

# NOW — pilot-critical path

## P0-MENA-1 — Complete the outbound AI/data-egress contract

**Goal:** no uncontrolled or insufficiently governed provider call leaves the application.

### Completed foundation

- [x] Centralize live text, audio, image/OCR and document egress.
- [x] Require registered purpose, modality and authenticated patient scope.
- [x] Enforce global AI consent immediately before egress.
- [x] Enforce text payload allowlists, size ceilings and deterministic DLP.
- [x] Enforce purpose/modality-granular raw-media consent.
- [ ] Expose authenticated patient grant/revoke management. **API implemented in PR #13; awaiting final CI + merge.**

### Remaining work

- [ ] Attach approved processor/subprocessor, residency, retention/no-training and legal-basis metadata to every egress policy.
- [ ] Remove or deliberately isolate provider-specific runtime seams.
- [ ] Add provider and streaming timeouts, typed failures and safe frontend error UX.
- [ ] Prove fallback paths cannot bypass the same policy.

### Acceptance gate

No provider receives by default:

- name, email, phone, address or birth date;
- Django/Firebase UID or national identifier;
- raw conversation history or unrelated clinical logs;
- unrelated health data;
- raw audio, image or document without an exact active grant and documented processor policy.

**Done when:** tests and CI prove no provider bypass and a complete explicit outbound policy contract.

---

## P0-MENA-2 — Locale + safety contract

- [ ] Model country, UI language, response language, script/transliteration, dialect, units and timezone separately.
- [ ] Require user confirmation; location may only suggest.
- [ ] Define deterministic fallback to MSA, English or French.
- [ ] Complete RTL coverage.
- [ ] Configure country-specific emergency resources with source/date ownership.
- [ ] Build native-speaker safety corpora for every enabled locale.
- [ ] Close the Darija high-severity orthographic-variant gap.
- [ ] Prove safety parity across text, voice transcript, mixed language and transliteration.

## P0-MENA-3 — Sovereignty-critical authentication migration

- [ ] Specify Django account lifecycle and recovery.
- [ ] Map Firebase identities to Django accounts.
- [ ] Design duplicate/lost-account reconciliation and rollback.
- [ ] Implement migration tests before removing Firebase dependencies.
- [ ] Replace Flutter Firebase handling only after rollback is proven.
- [ ] Add stronger controls for staff and professional accounts.

## P0-MENA-4 — Multimodal provider benchmark

Benchmark text, STT and vision independently on privacy, residency, no-training/no-retention terms, MENA quality, safety, latency, availability, cost and fallback options.

- [ ] Build representative minimized/synthetic evaluation sets.
- [ ] Run the benchmark.
- [ ] Document the decision matrix and rejected alternatives.
- [ ] Approve cutover only after privacy and quality gates pass.

---

# Pilot safety/compliance gate — before one real patient

- [ ] Deterministic insulin-dose/treatment refusal proven not to call an LLM.
- [ ] Doctor-facing and summary outputs proven to pass the same no-prescription policy.
- [ ] Emergency events route to a monitored human channel or an explicit self-care-only mode.
- [ ] Darija high-severity safety gap closed.
- [x] Base AI/model consent enforced server-side.
- [ ] Patient media-consent workflow available; backend enforcement is merged and API is in PR #13.
- [ ] Processor/subprocessor register and consent matrix documented.
- [ ] Cross-border and residency assumptions documented for the pilot country.
- [ ] Export process documented or implemented.
- [ ] Retention/deletion schedule defined.
- [ ] Incident response and escalation procedure defined.
- [ ] Pilot onboarding, monitoring and exit checklist approved.
- [ ] Historical exposed secrets rotated and unreachable.

---

# Deployment + pilot

- [ ] Validate a reproducible development path.
- [ ] Deploy staging with PostgreSQL, Redis, TLS, backups, logging and smoke tests.
- [ ] Select the first pilot country and cohort.
- [ ] Pass the first locale safety gate.
- [ ] Recruit approximately 30 controlled pilot patients.
- [ ] Enable retention instrumentation.
- [ ] Set the D90 go/stop threshold before reading outcomes.

# RETENTION GATE

Do not build condition #2 or broad platform scope until both are true:

1. D90 retention meets the founder-set threshold.
2. One credible payer or distribution signal exists.

# SOON

- [ ] Frontend integration tests for pilot-critical flows.
- [ ] Accessibility baseline.
- [ ] Dependency/security scanning and measured coverage thresholds.
- [ ] Production-grade load and failure testing.
- [ ] MFA/strong auth for staff.
- [ ] Complete observability retention policy.
- [ ] Retire legacy development scripts after Docker-first workflow is proven.
- [ ] Remove dead provider/Firebase code only after migration and rollback windows close.

# BUSINESS VALIDATION — founder-owned, parallel

- [ ] One-page monetization memo.
- [ ] Competitive landscape for selected MENA cohorts.
- [ ] At least five structured market conversations.
- [ ] Re-source market claims before external use.

# GATED — explicitly not now

- Second disease module, including hypertension.
- Third-party plugin marketplace.
- Worldwide language coverage.
- Multi-tenant enterprise machinery without validated demand.
- Any expansion into diagnosis, prescribing or treatment optimization without a separate regulatory/product decision.
