# V1-03 — Local Summary and Unverified-CGM Safety Review — 2026-10-10

**STATUS: TECHNICAL CANDIDATE / NOT CLINICALLY CERTIFIED / UNMERGED.**

## 2026-10-10 — External raw media gateway fail-closed (code HEAD `d1abf68`)

**BEFORE / risk verified in code:** `backend/media/voice.py` and `backend/media/vision.py` invoke `llm.runtime.execute_external_provider_call` with an audio recording or image bytes. That boundary authorizes patient scope, current consent + per-purpose media grant and processor policy, then executes the provider call. The network processor statuses are PENDING today; **no patient transfer or leak was observed**. However an approved policy in the future was sufficient to permit raw-media egress without a distinct V1-03 proof of safe content. The static generic-only text guard is unrelated. Document image OCR delegates to the governed vision adapter, whose patient-context cloud eligibility is separately denied.

**Goal / observable success:** every external non-text provider invocation remains denied by V1-03 even with a future simulated-approved processor plus signed patient and modality consent. Revocation/no-consent remains a separate earlier denial. No provider callback after any negative gate, including unforeseen media types.

**Implementation:** new `backend/core/external_media_v1.py` contains a fail-closed final-hop media blocker; `backend/llm/runtime.py::execute_external_provider_call` invokes it after original patient/processor authorization and before transport construction. `backend/core/tests/test_v1_03_external_media_egress.py` tests six media purpose/modality pairs with synthetic authorized patient and mocked approved processor, zero vendor callbacks, missing/revoked consent and future unknown modality. `test_multimodal_provider_circuit_breaker.py` and `test_provider_runtime_inventory.py` simulate the historical transport algorithm with only the new gate monkeypatched inside individual test fixtures; this is not a product bypass.

**Exact-head proof:** `d1abf68056f0b5d4ded534a5f2afb8aff2e3c0dd`: [CI #38043299895](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38043299895) **SUCCESS**, SQLite **2814 pass/5 skip/3 xfail**, PostgreSQL **2818 pass/1 skip/3 xfail**, 125 subtests; Ruff, LLM gateway and AI egress anti-bypass passed. [Migration #38043299841](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38043299841), [Companion E2E #38043299888](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38043299888) and [Protected Shadow #38043299942](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38043299942) **SUCCESS**. Flutter dedicated job skipped. [Earlier CI #38042757860](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38042757860) actually FAILED Ruff I001 over one missing blank line in new module; corrected in `d1abf68` with no safety logic removed.

**Operational limitation:** this explicitly disables external meal photo/glucometer image interpretation and external voice STT; manual/local alternatives and honest UX must be validated before any rollout. Does not prove global UI or privacy certification, and does not license image/audio patient egress when Gemini's policy becomes approved. This documentation update itself creates an unverified new HEAD until the exact workflows complete.

## 2026-10-10 — Protected Shadow independent direct-adapter hardening (code HEAD `bc31fe0`)

**PRE:** patient-context text calls through `llm.factory` were previously restricted by the external static-generic pair, but `companion/protected_provider_shadow.py` invokes the OpenAI-compatible `complete_text` transport directly in a gated experimental token-only path. `LocaleContract` accepts arbitrary nonempty locale strings, so locale/script metadata was not a separate strict network allowlist.

**Goal/success:** reject arbitrary/dynamic or clinical-looking locale metadata, mismatched script and a malformed protected-body token before provider construction, including the staff-only internal-live branch. Preserve fixed FR/Darija scripts and original local patient reply.

**Change:** `_verify_provider_shadow_payload` now permits only `fr/default`, `en/default`, `ar/default`, `ar-MA/arabic`, `ar-MA/latin` with `{{NVB_[A-F0-9]{32}}}` token. Called once before either processor/network branch; added negative/positive parametric tests. Feature remains OFF by default, internal-live requires active staff and explicit allowlist, patient visible reply unchanged.

**Proof:** exact code HEAD `bc31fe06d4efb9279968893d1c5399d54b6882bb`: [CI #38042006742](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38042006742) SUCCESS, SQLite **2802 pass/5 skip/3 xfail**, PostgreSQL **2806 pass/1 skip/3 xfail**, 125 subtests, Ruff + security anti-bypass green; [migrations #38042006680](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38042006680) SUCCESS; [Companion E2E #38042006751](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38042006751) SUCCESS. [Protected Shadow live probe #38042006598](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38042006598) SUCCESS: Ruff green, **43 targeted tests passed**, synthetic 3-call machine proof `machine_passed=true`, `patient_data=false`, FR/Darija Arabic/Latin passed with zero violations. Previous [probe #38041934929](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38041934929) FAILED at test import sorting before provider; corrected without changing safeguards.

**Limits:** bounded synthetic token-only internal live transport is not general patient model authorization, not native clinical copy signoff, not certification of AI optout/media/UX, and not pilot/merge/deployment approval. Other patient-origin prompts may still be constructed internally but externally denied by `llm.factory`. New docs-only HEAD must be rechecked.

## 2026-10-10 — External text last-hop generic-only gate (code HEAD `8292a13`)

**PRE / risk (code read):** `companion/conversation.py` builds free-text message, history, memory and clinical-context prompts for chat and buffered stream; `companion/narrator.py.summarize` also prepares patient-derived text. `llm.factory` formerly relied on a regex minimizer and DLP risk rules before a potentially approved external model request. Numeric/history clinical context without units need not be caught by anonymization heuristics. Network processors remain PENDING; **no actual external patient transfer was demonstrated or performed**.

**Goal:** regardless of future consent, processor-policy or FinOps settings, final external LLM text call never receives dynamic patient context.

**Implementation:** `backend/core/external_text_v1.py` contains one immutable nonclinical generic prompt pair; `backend/llm/factory.py::_execute_external_complete` checks the exact pair before invoking the external provider. Any other payload raises `AIProcessorPolicyDenied`. Existing local fallback remains available; this test-only generic exception is **not** a general AI patient capability. Opaque-token `companion/protected_provider_shadow.py` uses a distinct direct adapter, OFF by default/staff gated, so needs its own audit.

**Proof:** [CI #38037493525](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38037493525) on exact `8292a130a674e132f011aea3d1d819547fba0571` **SUCCESS** (SQLite **2791 passed/5 skipped/3 xfailed**; PostgreSQL **2795 passed/1 skipped/3 xfailed**; 125 subtests). Ruff, gateway and egress anti-bypass gates passed. [Migration #38037493457](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38037493457) **SUCCESS**; [Companion E2E #38037493521](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38037493521) **SUCCESS**. `backend/llm/tests/test_runtime_finops_wiring.py` verifies six synthetic dynamic prompts (unitless numerical evidence, FR/Darija, medication, memory/locale) produce **zero provider calls** even with mocked-approved processor and complete FinOps; legacy synthetic FinOps exercises the exact static pair. Dedicated Flutter job skipped; no native medical or UX certification.

**Adversarial history:** first code HEAD `eec1e0e` failed Ruff I001 (new import ordering). Fixed without removing the security guard in `8292a13`; exact-head CI then green.

**Unclosed:** actual chat/stream/narrator local failure behavior with patient context, protected shadow token-only direct adapter, media, consent/opt-out, `ai_provider=fallback` UI perception and screenshots, all clinical/linguistic/privacy independent reviews. No release/merge/deploy. This documentation itself creates a new HEAD needing exact-head CI.

## 2026-10-10 — Second slice: Doctor Brief local and log privacy (code HEAD `c2effc0`)

- `backend/ai/api/v1/ai.py` replaces the legacy Doctor Brief LLM prompt and call with `build_local_doctor_brief`. This is an authenticated, local, non-prescriptive count/mean summary; output schema unchanged. No raw CGM TIR, CV, TAR, TBR or GMI promoted. Four language templates are **translation candidates**, not native-certified clinical copy.
- `backend/diabetes/tests/test_v1_03_local_doctor_brief.py`: synthetic two-patient separation, no-consent local display, 401 anonymous, insufficient data, no gateway construction/inference, and normative CGM exclusion. `backend/companion/narrator.py` removes successful Doctor Brief content + patient ID log; `backend/companion/test_narrator_privacy.py` exercises the log with synthetic text.
- **Code-head evidence:** [CI #38036057381](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38036057381) SUCCESS (SQLite **2785 passed, 5 skipped, 3 xfailed**; PG **2789 passed, 1 skipped, 3 xfailed**; 125 subtests). Ruff, gateway anti-bypass, egress authorization anti-bypass, OpenAPI guard passed. [Migration #38036057344](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38036057344) SUCCESS; [Companion E2E #38036057367](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38036057367) SUCCESS. Flutter job SKIPPED and is not proof of frontend.
- **Contradictory check and remediation:** [CI #38035782616](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38035782616) FAILED because static tests required removed `get_gateway_llm` import and a new test had an unsupported direct-`get_llm` mock string. Fixed stale tests; scanner left intact. No external patient call was made to validate these changes.
- **Limit:** `companion/conversation.py` and `companion/narrator.py.summarize` retain patient-derived text gateway paths; processor network status PENDING means no actual leak proven. Verify final provider-bound payload and enforce generic/opaque-only or zero external model. No clinical/native-language/privacy reviewer signoff, before/after UX, merge, or release.
- This note is a **new docs-only HEAD** relative to `c2effc0`; no exact-head CI success can be claimed for it until freshly checked.

## PRE → Goal → Observable success → Proof

- Repository `hraaaaf/IAMINA-MVP`; base `main@13b7cce12c86daf60119fb703f22e8c6c192cf8d`.
- Working branch `security/v1-03-summary-local-only-20261010`, [PR #922](https://github.com/hraaaaf/IAMINA-MVP/pull/922) OPEN/DRAFT.
- Goal: a patient summary route cannot build a patient-data model prompt or present clinical CGM metrics from merely CGM-labeled rows. Same invariants in the companion clinical context.
- Success criterion: nonempty and empty authenticated summary does not call model gateway/formatter; structured clinical pattern remains deterministic; unverified CGM row provenance returns `None` for clinical CV/TIR/TAR/TBR/GMI, no `CGM_HIGH_VARIABILITY` and no unverified TIR trend in Companion; baseline negative tests continue passing.

## Implementation reviewed

1. `backend/diabetes/services/clinical/engine.py`: local `_format_fallback` replaces `_format_with_llm` on `run_clinical_analysis`. `guard_normative_kpis` precedes normative pattern construction and is applied in `DiabetesEngine.analyze`; ungoverned TIR trend/label are suppressed.
2. `backend/ai/api/v1/ai.py`: `get_summary` reuses the engine's single localized `report.insights` rather than formatting a second time; the legacy summary helper is local. The response uses `project_public_kpis` for normative values and reports `ai_provider=fallback`.
3. `backend/diabetes/tests/test_v1_03_local_summary_egress.py`: synthetic Django endpoint tests with 5 readings and zero readings; direct legacy helper; 100 readings/16 days with 80% rows `source=cgm` but no persisted sensor sessions; companion negative path. Mocks deny model entry.
4. `backend/diabetes/tests/test_api.py`: historical one-reading high/low tests require descriptive means but do not imply continuous CGM TAR/TBR. `docs/api/openapi.json` synchronized with the new route docstring.

## Exact parent-HEAD evidence

- Candidate code/doc snapshot `8ca3ac69657b5c2c7014286514af8231292f82e2`.
- [CI #38034929969](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38034929969): **SUCCESS**. Actual Django/pytest results: SQLite `2780 passed / 5 skipped / 3 xfailed` (121 subtests), PostgreSQL `2784 passed / 1 skipped / 3 xfailed` (121 subtests). CI Ruff and OpenAPI guard passed. **Frontend analyze/tests/PWA job SKIPPED**, do not claim Flutter evidence from this workflow.
- [Django migration drift #38034930096](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38034930096): SUCCESS.
- [Companion real chat E2E #38034930097](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38034930097): SUCCESS.
- Superseded `41fa1b25` [CI #38034682093](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38034682093) FAILED on the old single-reading TAR/TBR test assumptions plus a stale OpenAPI description. Both issues were corrected on `8ca3ac6`; do not mask or rewrite that history.
- All proofs above apply to the **parent**. This documentation closeout is a new commit and therefore needs its own exact-HEAD CI.

## Adversarial observations / unresolved risk

- Existing `/ai/doctor-brief` and companion chat/stream can still construct patient-derived text for the governed LLM gateway. No actual final provider-bound payload capture or external data leakage is proven by this lot; strict V1-03 zero-patient-context external LLM policy remains unresolved.
- `ai_provider=fallback` is truthful about zero model use but the Flutter summary model treats `fallback` as degraded. User-visible copy may thus be misleading. **No AFTER visual certification of this specific behavior**.
- Raw AGP output and existing descriptive SQL analytics require a separate clinical nomenclature and source-sufficiency review; normative fields are masked in the affected JSON summary and companion context, not magically throughout the product.
- Remaining CAL-09/10 patient-local clinical day / episode duration; CAL-11 USDA per-row primary provenance; CAL-12 typed/consented multilingual clinical PDF; reviews on other AI routes.
- Clinical, privacy/security, linguist-native FR/AR/Darija/RTL and accessibility reviewers remain unrecorded. Same-executor checks are not independent human review. No complete V1 decision is delivered.

## Next exact

1. Prove new documentation HEAD CI, migration drift and expected tests; inspect any new failure.
2. Review final outgoing provider payloads from Doctor Brief/chat/stream with wholly synthetic fixtures, including patient opt-out, denied processor policy, auth and locale. Do not send patient data to providers.
3. Resolve truthful UI state and capture BEFORE/AFTER at canonical viewports before a merge decision.
4. Independent specialist review, adversarial convergence, release certifier, then any approved merge and exact-main post-merge tests. Human patient/regulatory gates and explicit Vercel authorization remain separate.
