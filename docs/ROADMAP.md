# IAmina — Roadmap

> **Last updated:** 2026-08-01 — P0-MENA-4 automated benchmark framework validated in PR #18; live provider runs remain evidence-gated.
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
| P0-MENA-1 — outbound AI/data-egress contract | 100% | ✅ Merged | PRs #10–#15 |
| P0-MENA-2 — locale + safety contract | 50% | 🟡 Human review blocked | PR #16; native review and full RTL audit remain |
| P0-MENA-3 — sovereign authentication migration | 100% | ✅ Merged | PR #17, merge `185f680` |
| P0-MENA-4 — multimodal provider benchmark | 29% | 🟡 Framework green; live runs blocked | 2 of 7 tasks closed in PR #18; live text/STT/vision runs require approved evidence and credentials |
| Pilot safety/compliance gate | 15% | 🔴 Incomplete | 2 of 13 explicit gates complete |

**MENA critical-path completion:** 24 of 41 explicit roadmap tasks closed, approximately **59%**.

This percentage measures the MENA safety, sovereignty and pilot-readiness path, not the complete product codebase.

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

## Remaining human/UX gates

- [ ] Complete RTL coverage screen by screen.
- [ ] Obtain native-speaker approval for every enabled safety corpus.
- [ ] Close remaining Darija high-severity orthographic variants through native review.
- [ ] Approve safety parity across text, voice transcript, mixed language and transliteration.

Automated corpus and parity groundwork is green, but no native or clinical approval is inferred from automated tests.

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

# NOW — P0-MENA-4: Multimodal provider benchmark

**Goal:** select text, STT and vision providers using evidence rather than configuration convenience.

- [x] Build representative minimized and synthetic evaluation sets. **Strict contracts, stable fingerprints, modality/locale coverage and identity-data rejection are green in PR #18.**
- [x] Define scoring for privacy, residency, no-training/no-retention terms, MENA quality, safety, latency, availability and cost. **Safety/privacy hard floors, evidence expiry, deterministic judges, versioned reports and fail-closed cutover are green in PR #18.**
- [ ] Benchmark text providers independently.
- [ ] Benchmark STT providers independently.
- [ ] Benchmark vision/OCR providers independently.
- [ ] Document the decision matrix and rejected alternatives.
- [ ] Approve provider cutover only after privacy and quality gates pass.

## P0-MENA-4 checkpoint — PR #18

- **4A complete:** canonical synthetic/minimized corpus for text, STT, document OCR, glucometer OCR and meal vision.
- **4B complete:** provider-neutral runner, deterministic judges and weighted scoring.
- **4C infrastructure complete:** explicit provider evidence contract, expiry and disqualification rules, candidate registry and provenance-preserving reports.
- **4D infrastructure complete:** modality-specific ranking, rejected-alternative ledger and production cutover gate.
- **Live benchmark blocked:** no provider may be scored from fabricated values. Network runs require current legal/processor evidence, approved synthetic-only credentials and an authorized benchmark environment.

One evaluation unit must remain one PR and one ROADMAP responsibility.

---

# Pilot safety/compliance gate — before one real patient

- [ ] Prove insulin-dose and treatment requests are refused deterministically without an LLM call.
- [ ] Prove doctor-facing and summary outputs pass the same no-prescription policy.
- [ ] Route emergencies to a monitored human channel or formally adopt a documented self-care-only mode.
- [ ] Close Darija high-severity review.
- [x] Enforce base AI/model consent server-side.
- [x] Expose granular raw-media consent through the authenticated patient API.
- [ ] Approve the pilot consent matrix and processor/subprocessor register.
- [ ] Document cross-border and data-residency assumptions for the pilot country.
- [ ] Implement data export or document a valid operational export process.
- [ ] Define retention and deletion schedules.
- [ ] Approve incident-response and escalation procedures.
- [ ] Approve pilot onboarding, monitoring, escalation and exit checklists.
- [ ] Prove no committed or reachable secrets remain and rotate any exposed keys.

---

# Next sequence

1. **P0-MENA-4B live:** text-provider benchmark after evidence/credentials approval.
2. **P0-MENA-4C live:** STT benchmark after evidence/credentials approval.
3. **P0-MENA-4D live:** vision/OCR benchmark after evidence/credentials approval.
4. **P0-MENA-4E:** final evidence-backed decision matrix and cutover gate.
5. Return to the remaining P0-MENA-2 human/RTL gates and the Pilot Safety Gate.
