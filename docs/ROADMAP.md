# IAmina — Roadmap

> **Last updated:** 2026-07-30 — P0-MENA-2 automated scope implemented and validated through emergency registry and safety-corpus gates in draft PR #16.
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

# Progress dashboard

| Workstream | Progress | Status | Evidence |
|---|---:|---|---|
| P0 historical foundations | 100% | ✅ Complete | P0-A, P0-B, P0-C and migration drift merged |
| P0-MENA-1 — outbound AI/data-egress contract | 100% | ✅ Merged | 10 of 10 explicit controls merged through PR #15 |
| P0-MENA-2 — locale + safety contract | 50% | 🟡 Human review blocked | 4 of 8 tasks closed; native-speaker corpus approval and full RTL screen audit remain open |
| P0-MENA-3 — sovereign authentication migration | 0% | ⚪ Not started | Design and migration work pending |
| P0-MENA-4 — multimodal provider benchmark | 0% | ⚪ Not started | Evaluation set and benchmark pending |
| Pilot safety/compliance gate | 15% | 🔴 Incomplete | 2 of 13 explicit gates complete |

**MENA critical-path completion:** 16 of 41 explicit roadmap tasks closed, approximately **39%**.

This percentage measures the new MENA safety, sovereignty and pilot-readiness path. It is not a percentage of the complete product codebase.

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

## ✅ P0-MENA-1D — Patient media-consent management API — MERGED

Closed in PR #13 after green SQLite, PostgreSQL, OpenAPI, security, Flutter and migration-drift gates.

- Authenticated patients can list every supported media-consent option and its active or revoked state.
- Grant and revoke operations derive ownership exclusively from `request.user`.
- No client-supplied patient identifier is accepted.
- Grant requires active global AI consent.
- Grant and revocation are idempotent.
- Unsupported purpose/modality pairs fail closed.

## ✅ P0-MENA-1E — Executable processor policy registry — MERGED

Closed in PR #14 on 2026-07-28. Merge commit: `8883acad2191f22a23ebe0617e109d4c0e92d4ec`.

- Every provider resolves to an immutable processor policy before invocation.
- The policy records processor, subprocessors, regions, residence, retention, maximum retention, training use, legal basis, purposes and modalities.
- Unknown, forbidden, pending or incomplete external policies fail closed.
- Network providers remain pending until contractual and deployment-specific facts are explicitly approved; configuration alone cannot authorize patient-data egress.
- Local/static fallbacks are separately registered as no-external-egress policies.
- Regression tests prove processor denial prevents provider invocation.
- Final SQLite, PostgreSQL, migration drift, Ruff, import-linter, anti-bypass, Bandit, OpenAPI, Flutter and secret-hygiene gates passed before merge.

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
- [x] Expose authenticated patient grant/revoke management.
- [x] Attach processor/subprocessor, residency, retention/no-training, legal-basis and approval metadata to every provider policy.

### Remaining work

- [x] Remove or deliberately isolate provider-specific runtime seams.
- [x] Add provider and streaming timeouts, typed failures and safe frontend error UX.
- [x] Prove fallback paths cannot bypass the same policy.

### P0-MENA-1F — Provider runtime resilience — COMPLETE IN PR #15

**Goal:** an approved provider must fail safely, predictably and without bypassing consent, DLP or processor policy.

- [x] Inventory every synchronous, streaming and multimodal provider execution path. **Text complete/stream/think, STT audio, meal vision, glucometer OCR and document-image OCR are covered by executable inventory tests.**
- [x] Define one typed provider-failure taxonomy for timeout, unavailable, quota, malformed response, policy denial and internal failure. **Implemented and validated in PR #15; final completion remains gated by full-lot merge.**
- [x] Enforce explicit bounded timeouts at the provider boundary. **Gemini complete/stream/think and Kimi complete/stream are bounded; retries are disabled for Kimi.**
- [x] Ensure streaming cancellation and partial failures close safely. **The authorized wrapper closes the underlying provider iterator on cancellation, normal completion and partial failure; vendor failures after partial output remain typed and non-sensitive.**
- [x] Map backend failures to stable non-sensitive API errors. **Timeout/unavailable→503, quota→429, malformed response→502 and internal failure→500; the response exposes only stable code, safe message and retryability.**
- [x] Add deterministic Flutter UX for retryable and non-retryable failures. **The client parses the stable error contract, converts transport timeouts/unavailability into typed failures, closes the HTTP client in `finally`, and presents distinct safe messages without vendor details.**
- [x] Prove timeout, error and fallback paths cannot bypass egress scope, consent, DLP or processor policy. **Permanent tests prove authorization and processor policy run before provider invocation, multimodal calls are bounded, errors are normalized and local fallbacks cannot bypass scope.**
- [x] Pass SQLite, PostgreSQL, OpenAPI, security, Flutter and migration-drift gates before merge. **All permanent gates passed on the clean tranche-6 SHA before this checkpoint was closed.**

#### Checkpoints

- **Tranche 1 — typed provider failures:** implemented on 2026-07-28. Raw vendor exception messages are normalized at the authorized provider boundary; processor-policy denial still prevents invocation.
- **Tranche 2 — bounded provider timeouts:** implemented and validated on 2026-07-28. Gemini complete/stream/think and Kimi complete/stream are bounded; the full SQLite and PostgreSQL suites, migration drift, OpenAPI, security and Flutter gates passed before this checkpoint was closed.
- **Tranche 3 — stable API provider errors:** implemented and validated on 2026-07-29. A global Ninja handler maps the typed taxonomy to deterministic HTTP statuses and a non-sensitive `{error: {code, message, retryable}}` body. SQLite, PostgreSQL, OpenAPI, security, Flutter and migration-drift gates passed before this checkpoint was closed.
- **Tranche 4 — deterministic Flutter provider-error UX:** implemented and validated on 2026-07-29. SSE transport failures now surface as typed `ProviderApiException` values; retryable timeout/unavailability and non-retryable safe failures produce distinct patient-facing messages, malformed payloads fail closed, and the HTTP client is always closed. SQLite, PostgreSQL, OpenAPI, security, Flutter analyze and migration-drift gates passed before this checkpoint was closed.

- **Tranche 5 — stream cancellation, partial failure and fallback non-bypass:** implemented and validated on 2026-07-29. Provider iterators are closed deterministically on consumer cancellation and partial failure; failures are normalized without vendor leakage; processor-policy denial and missing egress scope stop streaming before the provider iterator starts. SQLite, PostgreSQL, OpenAPI, security, Flutter analyze and migration-drift gates passed before this checkpoint was closed.

- **Tranche 6 — exhaustive runtime inventory and multimodal boundary:** implemented and validated on 2026-07-30. STT audio, meal vision, glucometer OCR and document-image OCR now execute through one bounded runtime that checks patient scope/consent and processor policy before SDK invocation, normalizes vendor failures and fails closed while network-provider policies remain pending. Executable inventory tests prevent future direct multimodal SDK bypass. SQLite, PostgreSQL, Ruff, import-linter, anti-bypass, Bandit, OpenAPI, Flutter analyze, secret hygiene and migration drift passed before P0-MENA-1F was closed.

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

- [x] Model country, UI language, response language, script/transliteration, dialect, units and timezone separately.
- [x] Require user confirmation; location may only suggest.
- [x] Define deterministic fallback to MSA, English or French.
- [ ] Complete RTL coverage.
- [x] Configure country-specific emergency resources with source/date ownership. **Morocco registry is versioned, confirmed-country-only and fails closed when absent or stale.**
- [ ] Build native-speaker safety corpora for every enabled locale.
- [ ] Close the Darija high-severity orthographic-variant gap.
- [ ] Prove safety parity across text, voice transcript, mixed language and transliteration.

### P0-MENA-2 checkpoints

- **2A — canonical model:** one authoritative per-patient record separates country, UI language, response language, script, transliteration, dialect, glucose units and IANA timezone with independent provenance. Suggested/defaulted values cannot control runtime.
- **2B — authenticated confirmation API:** GET/PATCH/DELETE operations derive ownership from `request.user`; explicit confirmation is dimension-scoped, revocation is isolated, invalid values fail closed, and no patient identifier is accepted.
- **2C — runtime fallback wiring:** text and voice resolve only confirmed settings; historical silent Darija defaults are removed. RTL/rendering completion remains active.
- **2C — Flutter locale/RTL foundation:** the application locale comes only from the confirmed server-resolved UI language, supports French/English/Arabic, defaults deterministically to French, and proves Arabic RTL directionality. Full screen-by-screen RTL coverage remains open.
- **2D — emergency-resource registry:** Morocco contacts are stored with source ownership, verification/review dates and confirmed-country-only selection; absent, unknown or stale configuration fails closed.
- **2E — automated corpus groundwork:** executable high-severity glycemic cases cover baseline languages, Darija Arabic script, Latin transliteration, mixed-language text and voice transcripts. Automated parity is green, but every locale remains `pending_native_review`; no native approval is claimed.

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
- [ ] Emergency events route to a monitored human channel or the product explicitly adopts a documented self-care-only mode.
- [ ] Darija high-severity orthographic gap closed.
- [x] Base AI/model consent enforced server-side.
- [x] Granular raw-media consent management exposed through the authenticated patient API.
- [ ] Consent matrix and processor/subprocessor register approved for the pilot deployment.
- [ ] Cross-border/data-residency assumptions documented for the pilot country.
- [ ] Data export implemented or an operationally valid export process documented.
- [ ] Retention/deletion schedule defined.
- [ ] Incident response and escalation procedure defined.
- [ ] Pilot onboarding, monitoring, escalation and exit checklist approved.
- [ ] No committed/reachable secrets remain; exposed keys are rotated.
