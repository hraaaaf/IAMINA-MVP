# IAmina — Canonical Roadmap

> **Authority:** this is the single canonical forward tracker for IAMINA. If an issue, PR body, handover, assessment, AGENTS note, architecture note or historical phase document conflicts with this file on current status, priority or next work, **this file wins**. Historical documents remain evidence only.
>
> **Global audit:** 2026-09-17, reconciled against `main@df457cfdcc574439adb791fbfc44d484a1224417`, P5-4A merge #639, TD-014 merge #649, P5-6 release-gate evidence, #318/#320, `docs/TECHDEBT.md`, and the clarified local-first runtime boundary. The last explicitly frozen P5-6 candidate is `fb42e4d641b7b057607fe6a2de3d5104ccf15d0b`; later runtime/code changes mean it is retained as historical freeze evidence only, not as the current release candidate. The predecessor `5b27a22fc5c05a06e7eeeb0e841bb0e7dadce7f6` remains the last exact **remote development/certification** deployment proof. Vercel/Django/Neon is not the patient production runtime. No current release candidate exists until an explicit re-freeze is performed when the pre-real-patient gate is reactivated.
>
> **Canonical global progress:** **6/12 atomic roadmap lots CLOSED = 50.0%**. Atomic denominator: P5-0, P5-1, P5-2, P5-3, P5-4A, P5-4B, P5-5, P5-6 consent evidence engineering, P5-6A, P5-6B, P5-7, P5-8. Closed atoms currently retained: P5-0, P5-1, P5-2, P5-4A, P5-5 and P5-6 consent evidence engineering. The P5 whole-lot metric remains **4/9 = 44.4%** because P5-4B remains deferred and P5-6 remains open as a macro release gate. Retained MENA remains **32/38 = 84.2%** for its narrower scope.
>
> **Release posture:** `NOT_RELEASE_AUTHORIZED`. No current release candidate is frozen or authorized for deployment or real-patient processing. Engineering, UX, reliability, security and synthetic/non-patient work may continue. P5-6A/#318 and P5-6B/#320 are retained as mandatory **pre-real-patient gates**, not as the current engineering critical path.

## Product V1 — 29 approved decisions (2026-10-09)

> **Status:** product decisions **29/29 approved**; the V1 implementation lots below are **PLANNED, not automatically built, tested or clinically certified**. This forward product workstream supplements — and **does not erase or renumber** — the retained P5 pilot-readiness/release workstream, its \`6/12\` historical atomic completion baseline, or the mandatory pre-real-patient P5-6A/P5-6B gates.
>
> **Decisions source:** [IAMINA — 29-discussion register](https://app.notion.com/p/3f377c663362812dbe78cead75e71922). **Linked Notion canonical roadmap:** [01 — ROADMAP CANONIQUE](https://app.notion.com/p/3df77c66336281f5b308ec17f7f0a63b). The original source #28.1 means **intelligence/analytics BEFORE the chatbot**; our workshop subnumber #28.1 refers separately to **LLM isolation**. Do not interchange them.
>
> **Baseline inspected:** \`main@f6f5a0a07b9d9ae243dda699e1f5fe58c69fe192\`, CI run \`37836917174\` success. Existing clinical engines and companion contracts are retained; PRs #865/#866/#869 (Intent Envelope) and #918 (UX tests) are open and must be reconciled, not assumed merged. Existing first-use certification #879/#880 is evidence of that earlier, narrower flow, not certification for these new requirements.

### Goal and architecture

**IAMINA Intelligence Engine is independent of the chat surface.** Patient-scoped, provenance-bearing data → verified eligibility, units and timing → governed deterministic calculations, comparisons and observations → a versioned, evidence/uncertainty-bearing insight/decision envelope → the same authorized result in **Home, Reports and the guided IAmina conversation**.

A generative LLM may **only** generate non-patient generic wording or an opaque-token-only wrapper, with strict egress proof, no clinical authority and local final assembly. No patient message, history, measurements, demographics, clinical facts or correlated metadata may reach a third-party LLM. If privacy/policy/verification fails, **use no LLM**. Clinical predictions remain hidden research-only until independent scientific, clinical and regulatory approvals; no arbitrary one-month forecast.

### New implementation lanes — priority is proposed engineering order, not clinical authority

| Order | Lot | Priority | Deliverable and source decisions |
| --- | --- | --- | --- |
| 01 | **V1-01 — Full calculation and clinical-authority audit** | P0 | Enumerate every clinical, statistical, conversion, report and nutrition calculation and UI consumer; classify normative vs descriptive and fail closed on missing evidence. **#19 #11 #22** |
| 02 | **V1-02 — Intelligence Engine / governed patient context** | P0 | Reuse Clinical Twin, observations, evidence registry, longitudinal and multi-source contracts; one versioned patient-scoped fact/insight envelope with source, eligibility, uncertainty and authority, consumable by all three surfaces. **#28 original source-first intent #7 #18** |
| 03 | **V1-03 — Strict model/AI privacy boundary** | P0 | Enumerate all LLM egress paths, replace/disable patient-context prompts, enforce generic/opaque allowlisted payloads and negative egress tests, preserve effective global AI opt-out. **#28 workshop 28.1 #24 #26** |
| 04 | **V1-04 — True first-use and progressive profile** | P0 | Country/unit before targets, editable multi-treatment and unknown-type profile, no real-account demo records, existing-account continuity, secure recovery/app-lock, first-measure value, opt-in feedback; reuse previous merged first-use work. **#5 #7 #8 #9 #10 #11 #18 #22 #29** |
| 05 | **V1-05 — Guided IAmina conversation** | P0 | Deterministic question graph from opening, 2–4 options, reversible narrowing, repeat/back/free text locally routed, bounded responses, one main message, FR/AR/darija and RTL, non-floating chat mini-avatar. Home-only floating avatar. **#28 workshop 28.2/28.4/28.5 #6 #16 #27** |
| 06 | **V1-06 — Native-feeling CGM Integration Hub** | P1 | Manufacturer/model selection and allowed authorization, read-only connector orchestration behind IAMINA; authorized official APIs first, isolated audited adapters where lawful, legacy Nightscout compatibility, import fallback, real freshness/availability and revocation. No patient-run Nightscout requirement and no claim of universal CGM support. **#1 #25** |
| 07 | **V1-07 — Reliable intelligent capture** | P1 | Premium and precise glucose slider, unsaved-change guard, expandable secondary entry details; one editable meal draft from voice, text, form or assistive photo suggestions, natural portions, explicit human confirmation. **#12 #13 #14 #15 #17** |
| 08 | **V1-08 — Insights, reminders, notifications and deterministic reports** | P1 | Notification bell distinct from reminders, 2–3 upcoming reminders on home, one consented meaningful nonurgent insight per initial 24 h, chat/bell event-ID deduplication, opt-in weight trend, deterministic FR/AR PDF and CSV/XLSX exports. **#2 #3 #4 #20 #28 workshop 28.3** |
| 09 | **V1-09 — Premium UX, settings and accessibility** | P1 | Global and AI preference hierarchy, effective AI off without losing measurements, separate privacy/account actions and logout, Ramadan feature flag disabled, text copy/selection, home avatar target and reduced motion. **#16 #21 #23 #24 #26 #27** |
| 10 | **V1-10 — Predictive ML research in shadow** | P2 | Predefine scientifically meaningful target/horizon and population; ethical, isolated study data, temporal/external/prospective validation, calibration, bias and subgroups; no patient-facing predictions or effects on clinical advice or notifications. **#28 workshop 28.6** |
| 11 | **V1-11 — Whole-product certification and pilot safety gate** | Release gate | Cross-feature true first-use to first measurement/insight/chat, CGM and exports; clinical validation, egress/patient isolation, security/accessibility and exact-head CI/post-merge. P5-6A/P5-6B pre-real-patient/legal/data-residency/processor prerequisites remain mandatory. No Vercel deploy without explicit approval. **All 29** |

### V1-03 — Verified local AI notice required at patient network boundary (2026-10-10)

- **Goal / risk:** prior code correctly blocked an explicit session-local AI refusal, but allowed client AI calls to proceed when `hasDeclinedLocally == false` yet `ConsentService.hasConsent == false` (no currently verified notice). In addition, the legacy `ApiClient.chatWithAmina` REST path had no local guard. Backend global consent/egress protections remained independent and fail-closed; this was a **source-level defense-in-depth gap, not a demonstrated patient leak**.
- **Fix on code HEAD** `cf169c80960b4f404de630aaae91782a3356bdb9` in [PR #922](https://github.com/hraaaaf/IAMINA-MVP/pull/922): injected `ApiClient` now rejects locally unverified or explicitly declined AI before bearer/HTTP on patient chat stream, legacy chat, voice, transcription, meal image and web glucometer OCR. `CompanionService` similarly prevents patient text/voice egress before bearer or HTTP while preserving public synthetic audit demo without patient consent and honoring explicit local refusal. Typed refusal codes are distinct (`ai_declined_locally` vs `ai_consent_unverified_locally`) with FR/EN/AR screen copy. No server consent mutation; optional service constructors remain for legacy/testing and cannot prove global coverage alone.
- **Observable proof:** synthetic tests in `frontend/test/services/v1_03_local_decline_network_gate_test.dart` assert zero calls to bearer or mock HTTP for refusal and absent local proof. **Exact code HEAD 15/15 GitHub workflows SUCCESS**: [CI #38062688614](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38062688614) Ruff ✅; SQLite **2821 pass/5 skip/3 xfail**; PostgreSQL **2825 pass/1 skip/3 xfail**; Flutter **658 pass/1 skip** and PWA build ✅. [iOS packaging #38062688533](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38062688533), [Android packaging #38062688639](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38062688639), [Chrome screenshots #38062688623](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38062688623), [global routes #38062688570](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38062688570) and 10 other exact-head workflows also SUCCESS.
- **State / next:** exact-green **technical PR draft, not released**. Separate privacy follow-ups: [#924](https://github.com/hraaaaf/IAMINA-MVP/issues/924) user/product decision on device/session vs server-wide consent withdrawal, persistence/restart/multidevice; [#925](https://github.com/hraaaaf/IAMINA-MVP/issues/925) patient `GET /ai/chat/stream?message=...` query-string potentially entering request logs, no observed leak (migrate safely to POST streaming); clinician [#923](https://github.com/hraaaaf/IAMINA-MVP/issues/923) OCR unit provenance. New unverified-consent error copy has **no dedicated tri-viewport error-state BEFORE/AFTER**; earlier photo-CTA tri-viewport proof is valid only for that previous UI change. Formal a11y, clinical, CNDP/privacy, Groq processor, P5-6A/B and release/merge gates remain OPEN; no real patient use, Vercel deploy, or merge. **29 V1 decisions approved, zero fully delivered.** This docs commit needs its own exact-head workflows.

### V1-03 — Photo consent UI truthful, three-viewport visual proof, exact code HEAD GREEN (2026-10-10)

- **Goal:** local AI decline / missing current verified consent prevents the photo AI action while *manual food search, categories and logging remain accessible*. Strict provider-bound raw patient media block and patient server consent authority remain independent and unchanged.
- **Implementation since previous handover:** `ConsentService.hasConsent` now masks explicit local decline; shared consent-aware `ApiClient` and `CompanionService` deny local-declined patient AI network paths before auth/HTTP; meal photo and meal voice use shared client. `AddLogSheet` no longer derives photo AI eligibility from historic `aiConsentGivenAt`, but `context.watch<ConsentService?>()?.hasConsent ?? false`. `MealCapturePanel` disables `meal-photo-button` when false. Regression includes synthetic no-bearer/no-HTTP tests, static consent and client wiring, plus real Flutter widget test **verified consent → photo enabled → `declineLocally` → photo disabled, manual food search remains**.
- **Code HEAD VERIFIED:** `c96b69c4314744e727e10bcdcf700286a1daa7f1`, PR [#922](https://github.com/hraaaaf/IAMINA-MVP/pull/922) **OPEN/DRAFT/UNMERGED**. **15/15 exact-head workflows SUCCESS**, including [CI #38060367097](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38060367097) (backend SQLite/PostgreSQL and Flutter/PWA), [browser #38060366996](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38060366996), [iOS #38060367106](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38060367106), [Android #38060367195](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38060367195), and 11 other certification runs on this SHA.
- **BEFORE → Goal → reference/mockup → AFTER:** BEFORE exact Chrome patient screen `add-log-meal` from [run #38059314922](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38059314922); AFTER from [run #38060366996](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38060366996). Same 390×844, 768×1024 and 1280×900 screenshot fixtures, same layout/reference; only disabled CTA styling intended. Pillow pixel-level RGB comparison (non-zero channel difference, aligned image dimensions) shows **0.4366%**, **0.1775%**, **0.1198%** changed pixels respectively, i.e. **99.5634%**, **99.8225%**, **99.8802%** identical pixels, no viewport resizing. Screenshot observation confirms manual `meal-food-search`, categories, meal note and Save placement retained. **Visual stability score 9.9/10 (layout-only, not clinical/privacy/a11y certification)**; functional no-click widget test is separate. CI screenshot workflow green, but full manual a11y/language acceptance remains open.
- **Limits/human gate:** local decline is **ephemeral** and does not revoke authenticated server consent; optional service constructors and device restart/multidevice behavior need explicit privacy/product choice [#924](https://github.com/hraaaaf/IAMINA-MVP/issues/924). Unverified CGM/glucometer OCR unit authority [#923](https://github.com/hraaaaf/IAMINA-MVP/issues/923) needs clinician review; external patient raw media remains denied. P5-6A/B, CNDP, processor contracts, a11y/FR-AR-Darija remain open. **29 V1 decisions approved, 0 fully delivered**. The docs-only closeout SHA created from this checkpoint **must receive its own exact-head CI**; do not merge, deploy Vercel or authorize real patients.

### V1-03 — Media API manual fallback after privacy denial: exact-head 7/7 green (2026-10-10)

- **Code HEAD** `d48b5cbb7b3ad5cc3d817ea491033c9600b38f3f`, [PR #922](https://github.com/hraaaaf/IAMINA-MVP/pull/922) **DRAFT/UNMERGED**. **7/7 exact-head workflows SUCCESS**: [CI #38045938976](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38045938976) (SQLite **2821 passed, 5 skipped, 3 xfailed**; PostgreSQL **2825 passed, 1 skipped, 3 xfailed**, each 125 subtests); [migration #38045938953](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38045938953), [Companion E2E #38045938949](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38045938949), [Protected Shadow #38045938993](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38045938993), [UI geometry #38045939002](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38045939002), [Chrome screenshot #38045939111](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38045939111), [P5-5 rehearsal #38045938972](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38045938972) all **SUCCESS**.
- **PRE / bug:** new V1-03 external media guard intentionally raises `AIProcessorPolicyDenied` to prevent raw patient audio/image/document reaching external processors even with simulated approved processor + consent. `media/vision.py` and `media/voice.py` propagate this refusal; `ai/api/v1/ai.py` image and `ai/api/v1/voice.py` STT callers did not handle it, potentially returning an API error instead of the existing manual/low-confidence response.
- **Change:** only the API boundary catches `AIProcessorPolicyDenied`: meal image → empty food list + `fallback=true`; glucometer web OCR → `value=null` + `fallback=true` (unit field is response placeholder, **not a measured unit**); voice chat → empty transcript + existing error text; transcription-only → empty transcript/low confidence. `AIEgressDenied` (scope/consent denial) is **not** misreported as successful media interpretation. Seven synthetic tests cover six refused-provider scenarios plus voice absent-consent case; no provider network calls or patient data. Flutter `meal_capture_panel.dart` already shows unavailable notice and preserves manual food selection; no UI layout was changed.
- **CI regression honestly recorded:** [first new candidate CI #38045796018](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38045796018) failed pytest collection because fixture name `request` is reserved. Renamed test-only fixture to `fake_request` on `d48b5cb`, followed by 7/7 green. **Separate medical safety finding, not fixed or clinically signed off:** `backend/media/vision.py::_GLUCO_USER` asks external OCR to guess unit from number magnitude and normalizes invalid/missing unit to `mg/dL`; `frontend/lib/core/clinical/glucose_ocr_shield.dart` assumes mg/dL when no mmol token. External cloud OCR is currently blocked; native OCR still merits high-priority deterministic unit-evidence review with a clinician, explicit user confirmation and synthetic adversarial tests before release.
- **Status:** V1-03 remains **OPEN**; independent clinician/privacy/CNDP/Groq/security/natives FR-AR-Darija/RTL/a11y reviews, visual same-viewport BEFORE/AFTER for future UI changes, global AI opt-out coverage and P5-6A/B release gates outstanding. This closeout documentation commit requires its **own exact-head CI**; no merge, Vercel deployment or real patient authorization. **29 decisions approved, 0 fully delivered**.

### V1-03 — Raw patient media external egress fail-closed, code HEAD green (2026-10-10)

- [PR #922](https://github.com/hraaaaf/IAMINA-MVP/pull/922) code candidate `d1abf68056f0b5d4ded534a5f2afb8aff2e3c0dd`, **OPEN/DRAFT/unmerged**. Exact-head [CI #38043299895](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38043299895) **SUCCESS** (SQLite **2814 passed/5 skipped/3 xfailed**, PostgreSQL **2818 passed/1 skipped/3 xfailed**, 125 subtests; Ruff and LLM/AI egress anti-bypass succeeded); [migration drift #38043299841](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38043299841), [Companion E2E #38043299888](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38043299888) and [Protected Shadow token-only synthetic live #38043299942](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38043299942) all **SUCCESS**. Dedicated Flutter job skipped; not frontend certification.
- **PRE:** `media/voice.py` and `media/vision.py` send raw audio/image to Gemini through `llm.runtime.execute_external_provider_call` once scope+granular consent and approved processor policy succeed. `media/documents/extractors/image.py` delegates to VisionBackend with its own local eligibility check. Current Gemini policy is **PENDING**, so no actual network patient-data leak was demonstrated, but future approval alone could previously open raw-media egress without V1 privacy evidence. The `llm.factory` static-generic text check does **not** protect image/audio.
- **Fix and proof:** new `backend/core/external_media_v1.py` rejects every non-text external operation **including future unknown modalities**; invoked in `backend/llm/runtime.py` after scope/processor checks and before provider/circuit-breaker/transport construction. Six synthetic scenarios `meal_vision`, `glucometer_ocr`, `voice_chat`, `voice_transcription`, `document_ingest` (image/document) simulate approved processor plus real synthetic patient+granular consent and require **zero vendor calls**; additional negative consent absent/revoked and unknown future modality tests. Legacy circuit-breaker/error tests mock only this new gate in isolated synthetic transport simulations. No network media test sends patients.
- **Real red resolved, not hidden:** previous [CI #38042757860](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38042757860) failed at Ruff I001 for import spacing in `external_media_v1.py`; PostgreSQL and other three workflows were green. Commit `d1abf68` only corrected the import spacing, then exact-head CI **4/4 green**. Media capture/vision/STT cloud capability is therefore **intentionally unavailable** until a separately governed privacy-preserving transport contract exists. Do not claim feature equivalence, approved external media or all V1-03 gates closed.
- Remains **OPEN**: true global AI opt-out/intentional-local UX, other direct model routes and complete egress inventory, native FR/AR/Darija/RTL and a11y review, qualified clinician/privacy/legal/CNDP/Groq reviewers and true-release gate. This new docs-only SHA needs exact-head CI before closeout. No merge, Vercel, pilot or real patient authorization.

### V1-03 — Protected Shadow provider-direct edge tightened, 4/4 code workflows green (2026-10-10)

- [PR #922](https://github.com/hraaaaf/IAMINA-MVP/pull/922) technical HEAD `bc31fe06d4efb9279968893d1c5399d54b6882bb` **OPEN/DRAFT/unmerged**. Exact-head [CI #38042006742](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38042006742) **SUCCESS** (SQLite **2802 pass/5 skip/3 xfail**, PostgreSQL **2806 pass/1 skip/3 xfail**, 125 subtests; Ruff and gateway/egress anti-bypass passed), [migrations #38042006680](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38042006680) **SUCCESS**, [Companion E2E #38042006751](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38042006751) **SUCCESS**, and [Protected Shadow three-call synthetic live probe #38042006598](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38042006598) **SUCCESS** (43 targeted tests passed; machine_passed true; 3 planned non-patient token-only Groq calls; FR, Darija Arabic and Latin all passed). Flutter dedicated job skipped; not certified.
- The OFF-by-default staff-only `companion/protected_provider_shadow.py` adapter calls `complete_text` **outside** `llm.factory`. Independent last-hop validation now rejects all unapproved locale/script pairs and nonopaque token forms **before** processor check or provider construction in both normal and internal-live shadow modes; negative tests include injected metadata. Only locales `fr/en/ar/ar-MA` with predefined scripts are allowed. This **does not** authorize unrestricted patient-context prompts, clinician use, release or patient processing.
- First shadow candidate `9fd4e30` [probe #38041934929](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38041934929) FAILED at Ruff import ordering **before network**; corrected to `bc31fe0` without weakening validation. Clinical/native language/privacy/accessibility and UX BEFORE/AFTER reviews, consent/opt-out, image/audio boundaries and pilot gate remain OPEN. **No merge, Vercel or patient release.** This new docs-only commit still needs exact-head CI.

### V1-03 — Strict external text egress gate technically green (2026-10-10, NOT released)

- [PR #922](https://github.com/hraaaaf/IAMINA-MVP/pull/922) code HEAD `8292a130a674e132f011aea3d1d819547fba0571` **OPEN/DRAFT/unmerged**. Exact-head [CI #38037493525](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38037493525) **SUCCESS** (SQLite **2791 passed / 5 skipped / 3 xfailed**; PostgreSQL **2795 passed / 1 skipped / 3 xfailed**; 125 subtests). Ruff, gateway anti-bypass and egress anti-bypass succeeded. [Migration #38037493457](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38037493457) **SUCCESS**; [Companion E2E #38037493521](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38037493521) **SUCCESS**. The dedicated Flutter job was **SKIPPED by scope**, NOT a Flutter certification.
- New fail-closed boundary: `backend/core/external_text_v1.py` enforces an **exact static generic (non-patient) prompt pair** at `backend/llm/factory.py::_execute_external_complete`, before the network operation. Anonymization by regex alone is not anonymity proof; even when processor, consent and FinOps would otherwise permit text egress, any dynamic patient-content prompt is denied. Six synthetic adversarial values/languages were tested at the actual guarded outbound provider call path. Existing synthetic FinOps tests use the fixed approved generic fixture. This gate is for the `llm.factory` **text-provider boundary**, not evidence that all media or directly invoked shadow adapters are certified.
- New gate is intentionally *not* a general-purpose patient narration capability. Chat/stream and the legacy narrator may still **construct** patient-derived prompts internally; the external text gateway now refuses their transmission. Local-only behavior and failure UX must be checked separately. `companion/protected_provider_shadow.py` uses an independent OFF-by-default, staff-gated, opaque-token `complete_text` adapter; verify that specific boundary independently before any experimental use. Audit image/audio and global opt-out separately.
- V1-03 and **all 29 approved decisions remain OPEN/not fully delivered**. Mandatory security/privacy and qualified clinician, native FR/AR/Darija/RTL, accessibility, egress/UX BEFORE→AFTER and release gates still apply. No merge, real patient, Vercel or pilot authorization. This documentation update is a **new HEAD** and requires its own exact-head CI.

### V1-03 — Second safety slice technically green, release still gated (2026-10-10)

- [PR #922](https://github.com/hraaaaf/IAMINA-MVP/pull/922), code HEAD `c2effc096f86eb08e7c73118e17042fec3106ba2` **OPEN/DRAFT, unmerged**. [CI #38036057381](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38036057381) **SUCCESS**: SQLite 2785 passed / 5 skipped / 3 xfailed; PostgreSQL 2789 passed / 1 skipped / 3 xfailed, 125 subtests; anti-bypass and OpenAPI SUCCESS. [Migration #38036057344](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38036057344) and [Companion E2E #38036057367](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38036057367) **SUCCESS**. Dedicated Flutter test/PWA CI job **SKIPPED by scope**; do not claim its certification.
- Additional local-only `/ai/doctor-brief`: patient-authenticated deterministic recorded-count / descriptive-mean summary, with no LLM prompt, no CGM TIR/CV/GMI promotion, synthetic tests for no consent, authorization, patient separation, insufficient data, and FR/EN/AR/ar-MA candidate copy. `companion/narrator.py` no longer logs text of a model-authored Doctor Brief or patient ID in its success log; regression added. Translations/clinical language require independent qualified review.
- Previous failing CI [#38035782616](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38035782616) correctly identified two stale gateway-reference tests plus a forbidden mock string in anti-bypass scanner; tests corrected **without weakening the scanner or restoring patient egress**.
- **V1-03 remains OPEN**: `companion/conversation.py` still forms user/history/memory/clinical prompts in chat and stream; `companion/narrator.py.summarize` builds a patient-derived prompt; final provider-bound payload, external-model generic/opaque allowlist, global opt-out, UI `ai_provider=fallback` and clinical/native-locale/a11y proof remain unclosed. Processor network PENDING; **no actual external patient-data transfer is proven**. Clinical/privacy approvals, merge, post-merge, real patients and Vercel are NOT authorized by green CI. Reconfirm the new docs-only SHA with exact-head workflows before treating this closeout as current.

### V1-03 — Technical candidate in draft (2026-10-10, NOT released)

- [PR #922](https://github.com/hraaaaf/IAMINA-MVP/pull/922), candidate clinical-code HEAD `8ca3ac69657b5c2c7014286514af8231292f82e2`, separate branch `security/v1-03-summary-local-only-20261010`, **OPEN/DRAFT/unmerged**. This does not close V1-03 or any of the 29 complete decisions.
- Bounded fixes: `/ai/summary` emits one local deterministic pattern report without its former double model-formatting path; `run_clinical_analysis` prevents raw CGM row fraction from authorizing normative patterns; `/ai/summary` returns `project_public_kpis` rather than raw SQL CV/TIR/TAR/TBR/GMI; `DiabetesEngine.analyze` masks unverified normative CGM and suppresses the raw TIR trend/label.
- **Technical parent-HEAD proof only:** [CI #38034929969](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38034929969) SUCCESS, SQLite **2780 passed / 5 skipped / 3 xfailed**, PostgreSQL **2784 passed / 1 skipped / 3 xfailed**, [migration drift #38034930096](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38034930096) SUCCESS, [Companion real-chat E2E #38034930097](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38034930097) SUCCESS. The main CI's dedicated Flutter analyze/test/PWA job was **SKIPPED by scope**, not counted as a tested frontend.
- Remaining P0/privacy and clinical gates: actual final provider-bound prompt of Doctor Brief, chat/stream and other LLM routes; global opt-out, consent, identity, language and access-negative testing; recorded AGP/chart truthfulness; `ai_provider=fallback` may misleadingly display degraded AI mode; qualified clinician, security/privacy, native FR/AR/Darija/RTL + accessibility and release review. V1-01 #920 / V1-02 #921 remain draft. **No authorization for merge, real patients or Vercel deployment**.
- Detailed proof: [V1-03 assessment](assessments/2026-10-10-v1-03-summary-cgm-safety-audit.md) and [handover](handovers/2026-10-10-iamina-v1-03-summary-cgm-handover.md). Documentation commit requires **fresh exact-HEAD CI**; the parent-HEAD success does not certify later commits.

### Critical path, parallelism and evidence

1. **Start with V1-01** (audit register, actual backend→frontend call graph, bad/unknown inputs, units and model authority). In parallel, non-invasive inventory of reused V1-02 contracts and external egress paths V1-03. Do not replace an already certified module merely because a new layer name exists.
2. **One vertical proving slice**: authenticated patient → eligible existing measurement → versioned, provenance-bearing deterministic observation → exact same fact, uncertainty and status in Home, Reports and guided Chat → prove no patient information can exit via LLM. This is the first functional milestone before broad visual changes.
3. **V1-04 and V1-05** follow the certified data/safety contracts; **V1-06** may progress in parallel once consent, patient isolation and manufacturer access checks are proven. Manual measurement remains usable without any CGM account.
4. **V1-07/V1-08/V1-09** converge capture, actionable observations and design consistency; refine against actual screenshots. **V1-10** is independent research and never a release dependency for descriptive V1.
5. Each lot requires exact **Goal → observable success → test evidence**. Backend Django/SQLite+PostgreSQL where relevant, provenance/negative/cross-patient tests, API/frontend/real navigation, and **BEFORE → written target → approved mockup → implementation → AFTER at identical viewports**, including 390×844, accessibility and honest visual score when UI changes.
6. **Never present an unverified CGM feed as real-time safety monitoring, a descriptive trend as causal/predictive medical advice, a demo record as real patient data, or an unreviewed narrator as clinical authority.** Emergency safety routing is independent from the 24-hour nonurgent attention budget and global AI toggle.
7. Deployment to Vercel remains human-approved separately. The historical P5 pilot release gate requires explicit release re-freeze and competent professional/legal authorization before identifiable real-patient processing. Historical progress figures are not transferable to V1-01…V1-11. **No V1 implementation completion percentage is claimed yet.**

### Traceability — all original 29 issue numbers

| Original remarks | Assigned implementation lots |
| --- | --- |
| #1 #25 | V1-06 |
| #2 #3 #4 #20 | V1-08 |
| #5 #7 #8 #9 #10 #18 #22 #29 | V1-04 (also V1-01/V1-02 for evidence and context) |
| #6 #16 #27 | V1-05 / V1-09 |
| #11 #19 | V1-01 / V1-04 |
| #12 #13 #14 #15 #17 | V1-07 |
| #21 #23 #24 #26 | V1-03 / V1-09 |
| #28 | V1-02 / V1-03 / V1-05 / V1-08 / V1-10 |

**Next exact:** establish the V1-01 full-calculation audit manifest on current main; check source→derivation→patient output, mark evidence gaps, author tests with no unsupported clinical promotion; then run exact-head checks and proceed with the first vertical proving slice. Keep P5 release gates untouched.

---

## North star

Ship one safe, measurable Morocco/MENA diabetes-companion PWA pilot, collect real evidence, then make an explicit go/no-go decision before broader rollout or a second disease capsule.

## Non-negotiable product boundaries

- Diabetes is the only live condition.
- IAMINA is a patient companion, not a physician replacement.
- Deterministic clinical/safety logic is authoritative; generative models may only narrate approved bounded output.
- No diagnosis, prescription, dose calculation, treatment optimization/change or autonomous medical instruction.
- Language/dialect enablement requires explicit safety parity; location never silently determines language or emergency jurisdiction.
- Pilot delivery is PWA-first. Native Android/iOS is deferred unless explicitly activated.
- **Patient runtime is local-first:** first device enrollment, subsequent reopen, core clinical persistence and required local workflows must not require Vercel, Neon, Firebase, SMTP or another remote processor to be reachable.
- `iamina-certified` on Vercel, its Django runtime and its dedicated Neon database are **development/integration/certification infrastructure**, not the patient production runtime.
- Remote account creation is disabled by default in the patient path and may be enabled only explicitly for a remote DEV/certification account flow. Remote account, synchronization or auxiliary services may degrade independently; their outage or credential rejection must not destroy local enrollment or valid local clinical state.
- Local enrollment is continuity state; Web/PWA patient access is additionally protected by the merged strong device-local WebAuthn app-lock from #649. IAMINA does not own a weak PIN/password fallback for this lock and does not receive biometric material.
- Engineering proof, human approval, legal/CNDP approval and real-patient authorization are separate gates.
- No identifiable real-patient health data may enter IAMINA until the pre-real-patient gate is explicitly completed and release is authorized.

---

# 1. Executive status

| Area | Canonical status | Forward consequence |
|---|---|---|
| **Global canonical roadmap** | **🟡 6/12 = 50.0%** | continue verified non-patient engineering and remaining unresolved debt |
| Gate A Secure Core | ✅ CLOSED / certified 10.0/10 | maintenance only |
| Historical P0 foundations / product truthfulness / agent governance | ✅ CLOSED | no reopening without new defect/evidence |
| Global UX / Dashboard / Journal | ✅ CLOSED | regressions only |
| Clinical Data Layer & Privacy foundation | ✅ MERGED | residual privacy debt remains under `docs/TECHDEBT.md` |
| Companion intelligence / proactive lifecycle | ✅ CLOSED through current convergence | no active forward feature lot |
| CGM gateway V1/V1.1/V2/V2.1 | ✅ CLOSED | physical-sensor evidence remains external if later claimed |
| P4-FRUGAL PRE-PILOT | ✅ CLOSED 10.0/10 | real pilot economics belong to P5-7 |
| MENA retained tracker | 🟡 32/38 = 84.2% | informational only |
| P5 whole-lot tracker | 🟡 4/9 = 44.4% | active program |
| P5-4A offline packaging | ✅ CLOSED / AUTH_LOCAL_FIRST + STRONG_LOCAL_APP_LOCK | local-first availability and WebAuthn app-lock are merged; keep regression coverage |
| P5-6 consent evidence engineering | ✅ CLOSED atomic sublot | retained as merged engineering evidence |
| P5-6 remote dev/cert infrastructure | ✅ EXACT_REMOTE_PATH_HEALTHY / NOT_PATIENT_PROD | proves Vercel/Neon dev/cert path for `5b27a22…`; does not define patient production topology |
| P5-6 last frozen candidate evidence | 🟠 HISTORICAL_FREEZE / NOT_CURRENT | `fb42e4d…`; runtime/code advanced later, so explicit re-freeze is required before any release attempt |
| P5-6 current release candidate | ⚪ NONE | must be created by an explicit exact-SHA re-freeze when the pre-real-patient gate is reactivated |
| P5-6A / P5-6B | ⏸️ PRE_REAL_PATIENT_GATE / DEFERRED | mandatory before first identifiable real-patient health data; not current engineering critical path |
| Real-patient release | 🟠 NOT_AUTHORIZED | blocked until pre-real-patient gate is completed and explicitly authorized |

### Progress arithmetic

1. **Canonical global progress: 6/12 = 50.0%.** Equal-weight atomic forward lots; P5-4A is re-closed after merged local-first remediation and exact-head proof.
2. **P5 Pilot Readiness: 4/9 = 44.4%.** Historical whole-lot P5 accounting; P5-4 and P5-6 remain open as macro lots.
3. **Retained MENA: 32/38 = 84.2%.** Informational only; never a release gate.

No partial credit is assigned inside an atomic lot. Deferring a gate does not close it and does not increase progress.

---

# 2. One critical path

**Current non-patient engineering path:** continue verified product/security/reliability/UX work on synthetic or non-patient data, prioritizing reproduced defects and the unresolved items that remain in `docs/TECHDEBT.md`.

**Mandatory pre-real-patient path, activated before the first identifiable real-patient health data:** explicit exact-SHA re-freeze → P5-6A restricted safety evidence + P5-6B processor/CNDP evidence bound to the **actual local-first patient runtime and genuinely enabled external processors** → actual patient-runtime topology proof → three exact-SHA approved audits → explicit human release decision → controlled PWA pilot → P5-7 observed evidence → P5-8 go/no-go.

The Vercel/Django/Neon development/certification stack is not a mandatory patient-production dependency and must not be inserted into the patient processor/residency inventory solely because it exists for engineering. The pre-real-patient path is deferred, not waived. No release, deployment authorization or regulatory approval is implied by current engineering progress.

---

# 3. P5 Pilot Readiness

## P5-0 — Security reconciliation

**Status:** ✅ CLOSED.

## P5-1 — Morocco linguistic certification

**Status:** ✅ CLOSED / HUMAN_APPROVED / retained exact-main evidence.

Retained proof includes PR #579, exact-main evidence SHA `2d18428a0c59a18c82a1c0dfb410469f17f81e04`, green post-merge CI/migration, packet #34683056185, artifact #10295285314 and human approval in #515.

## P5-2 — Arabic OCR real-world evidence

**Status:** ✅ CLOSED with negative qualification result.

Real-camera Tesseract `ara` failed the required quality floor. No local Arabic full-document primary is qualified.

## P5-3 — Native TTS real-device evidence

**Status:** 🟡 DEFERRED / HUMAN_DEVICE_GATE.

Tracker: #518. Required only before a native pilot/distribution claim; it does not block the current PWA-first pilot.

## P5-4 — Pilot packaging

**Status:** 🟡 SPLIT / P5-4A CLOSED / P5-4B DEFERRED.

### P5-4A — PWA packaging engineering

**Status:** ✅ CLOSED / AUTH_LOCAL_FIRST_VERIFIED / STRONG_LOCAL_APP_LOCK_MERGED.

The reproduced offline-auth regression is resolved. PR #639 (`fix(auth): restore local-first offline reopen boundary`) merged as `bd13e8ad0c6f3ff2c4376b00c43fb8c54068d053`; its final candidate head was `05d02a0def7b909b83615c506ccf97f9623f1c6b`.

Retained local-first contract:

- first patient-device enrollment creates only a device-local enrollment marker plus opaque installation identifier and performs **zero required network requests**;
- subsequent local boot/reopen performs **zero required auth-network requests**;
- the default patient enrollment UI requests no email/password and makes no online-account claim;
- remote account registration is disabled by default and `registerWithEmail()` fails closed unless `IAMINA_REMOTE_ACCOUNT_ENROLLMENT=true` is explicitly enabled for the remote DEV/certification flow;
- local enrollment/session and the Django-signed remote API bearer are separate states;
- remote bearer rejection/expiry clears remote credential use only and cannot erase local enrollment or local clinical state;
- explicit sign-out clears the remote bearer, local marker and opaque local device identifier even if remote logout is unavailable;
- malformed secure-storage text never bootstraps local enrollment.

The separate strong local-auth debt was then resolved by PR #649 (`feat(auth): add strong local WebAuthn app-lock`), merged as `main@df457cfdcc574439adb791fbfc44d484a1224417`. The final exact candidate `fd5bc4392ceda6b411b72f3ceb9254119024ac5c` passed all 15 pull-request workflows, including CI #4454, TD-014 local app-lock certification #14 and TD-008 device integration baseline #14.

Fresh TD-014 artifact `10517999169`, digest `sha256:a0d17487f8cdca0bed18979e650eab6efc6679c76d834938dbae58de3e4f0255`, was inspected and retained:

- WebAuthn platform authenticator with required user verification;
- local/offline unlock with application network unavailable;
- user-verification failure fails closed;
- a genuinely mutated public key fails closed;
- no application network is required for unlock;
- BEFORE / setup / locked captures at `390×844`, `768×1024`, `1280×900`;
- zero horizontal overflow in the retained visual report;
- final P5-4A `AuthService` remained byte-identical through the app-lock lot.

Controlled pilot URL, physical target-browser installation, any patient distribution hosting, production release and real-patient authorization remain external.

### P5-4B — Native Android/iOS alignment

**Status:** 🟡 DEFERRED.

Future native-only work includes permanent signing/provisioning and physical-device install/update/recovery evidence.

## P5-5 — End-to-end pilot rehearsal

**Status:** ✅ CLOSED / `PASS_WITH_BOUNDARIES`.

Retained synthetic/non-patient proof includes main `88b78e036ce3494dfe37921e70e064fbfdabd6bb`, rehearsal #34573137446, CI #34573137452 and artifact #10188573954.

## P5-6 — Real-patient release gate

**Status:** ⏸️ PRE_REAL_PATIENT_GATE / DEFERRED / NOT_RELEASE_AUTHORIZED.

This gate is mandatory before the first identifiable real-patient health data enters IAMINA. It is not the current day-to-day engineering priority while work remains synthetic/non-patient. Deferral does not constitute approval, closure or waiver.

### Last retained frozen candidate evidence

The last explicitly frozen release SHA was `fb42e4d641b7b057607fe6a2de3d5104ccf15d0b`, with:

- safety corpus: 59 exact cases;
- parity coverage: 10 technical tuples;
- safety fingerprint: `823d109b0ddd10d1874eec53027eafd9d65884f14810304af3681c57c82cf7e5`;
- consent notice version: `2026-09-12.1`.

That SHA is retained as historical exact-freeze evidence. It is **not** the current release candidate because later runtime/code changes have advanced `main`. A new exact release candidate must be explicitly re-frozen before the pre-real-patient gate is executed.

### Historical candidate re-freeze proof

The predecessor candidate `5b27a22fc5c05a06e7eeeb0e841bb0e7dadce7f6` proved the **remote Vercel/Django/Neon development/certification path**. It did not prove or define the patient production runtime. Two release-gate/runtime defects were then fixed:

- PR #602 made the local-only consent audit consume the restricted residency manifest and bind genuine CNDP health-processing evidence to the exact release SHA;
- PR #603 made native password recovery require an explicit provider-neutral SMTP contract when that remote recovery path is enabled, removed silent delivery assumptions and preserved account-enumeration resistance.

Validation retained for the historical `fb42e4d…` freeze:

- #602 exact-head CI #4186 / workflow `34771054574` SUCCESS;
- #602 exact-head migration drift #3733 / workflow `34771054541` SUCCESS;
- #603 exact-head CI #4189 / workflow `34771391814` SUCCESS;
- #603 exact-head migration drift #3736 / workflow `34771391809` SUCCESS;
- #603 merge `main@fb42e4d641b7b057607fe6a2de3d5104ccf15d0b`;
- post-merge CI #4190 / workflow `34773613905` SUCCESS;
- post-merge migration drift #3737 / workflow `34773613814` SUCCESS.

Clinical rebind proof retained for that historical freeze:

- `backend/core/safety_corpora.py` blob is identical between `5b27a22…` and `fb42e4d…`: `bf046c298ee8e77591f5c5b1049b806a6255bfcf`;
- `backend/core/triage_classification.py` blob is identical between those candidates: `eba7a57967eeec1ba4b264c90ccab1a30e516b38`;
- the retained corpus therefore remains 59 exact cases / 10 tuples with fingerprint `823d109b0ddd10d1874eec53027eafd9d65884f14810304af3681c57c82cf7e5`.

This is historical technical exact-corpus evidence only. It does not fabricate reviewer identity, qualification or a new human approval. Any later runtime/code change invalidates use of that historical freeze as the current release candidate and requires another explicit re-freeze before a real-patient release attempt.

### P5-6 consent evidence engineering

**Status:** ✅ CLOSED atomic sublot / MERGED / GREEN.

Retained from #591: exact notice version/hash/locale, legacy consent invalidation, server acceptance receipts, withdrawal revocation, current-consent AI-egress verification, consent-epoch isolation, Flutter/server fail-closed behavior and Secure Storage + Drift local gating.

### P5-6 remote development/certification deployment state

**Status:** ✅ PREDECESSOR_REMOTE_PATH_HEALTHY / NOT_PATIENT_PROD / NO_CURRENT_CANDIDATE.

Proven predecessor **remote development/certification** topology:

- Vercel project `iamina-certified` / `prj_Pn9FnyconF3h2w9gOU74iV98kJoU`;
- exact source `5b27a22fc5c05a06e7eeeb0e841bb0e7dadce7f6`;
- deployment `dpl_8ex2k82KaozE6Fxc8wQBYJuRU43y`;
- state `READY`, target `production` in Vercel's deployment terminology, runtime region `cdg1`, one Python serverless function;
- stable alias `iamina-certified.vercel.app` resolved to that deployment;
- dedicated Neon project `IAMINA` / `square-sun-82359137`, PostgreSQL 16, region `aws-eu-central-1`, default branch `production` / `br-fragrant-frost-b1lbdfzs`;
- migrations current and health HTTP 200 with `status=ok`, `db=ok`, `cache=unavailable`;
- cache unavailability is non-fatal under the existing health contract; no Redis readiness claim is made;
- no AqarFinder/Supabase database and no unrelated Neon database was reused.

The words `production` above describe Vercel/Neon environment labels only. They do **not** mean patient production. `docs/LOCAL_FIRST_RUNTIME_BOUNDARY.md` defines the runtime boundary.

The historical `fb42e4d…` freeze was **not deployed**. PR #603 deliberately made the remote Django production-settings path fail closed until an explicit SMTP/reset contract is configured. That is a remote dev/cert deployment condition, not a requirement for local clinical availability. No future Vercel deployment may occur without separate explicit owner authorization.

### P5-6A — Safety qualification manifest

**Tracker:** #318.

Current state: `OPEN / PRE_REAL_PATIENT_GATE / DEFERRED / REVIEW_ATTESTED / OWNER_QUALIFICATION_ATTESTATION_RETAINED / HISTORICAL_EXACT_CORPUS_EVIDENCE_RETAINED / CURRENT_CANDIDATE_PENDING_REFREEZE / RESTRICTED_QUALIFICATION_REFERENCES_PENDING`.

Already retained: owner-attested safety/clinical review, Darija adjudication/runtime cutover, safety-owner/parity attestation and English-locale validation. Owner qualification wording: **« professionnels qualifiés »**, reference `issue-318:owner-attestation:professionnels-qualifies`.

Still missing before real-patient release:

- explicit exact-SHA re-freeze of the future release candidate;
- real opaque native-reviewer references for `fr`, `ar`, `en`, `ar-MA`;
- real qualification references required by the manifest contract;
- non-stale `reviewed_on` / `review_due_on`;
- approved coverage of all 59 exact case IDs;
- approved coverage of all 10 exact parity tuples;
- restricted safety manifest bound to the newly refrozen exact candidate and exact safety fingerprint;
- exact-SHA safety audit PASS.

### P5-6B — CNDP / consent / processor / residency

**Tracker:** #320.

Current state: `OPEN / PRE_REAL_PATIENT_GATE / DEFERRED / REMOTE_DEV_CERT_PATH_PROVEN / PATIENT_RUNTIME_TOPOLOGY_PENDING / COMPLIANCE_EVIDENCE_PENDING`.

Still required before real-patient release:

- explicit exact-SHA re-freeze of the future release candidate;
- freeze the **actual local-first patient runtime topology** and enumerate only the external processors genuinely enabled for that pilot;
- account-specific processor/DPA/subprocessor/retention/deletion/privacy/security evidence for every genuinely enabled external processor;
- if remote password recovery is enabled for the pilot, choose/configure its mail processor and include it in that evidence inventory; if it is not enabled, do not fabricate it as a runtime dependency;
- deployment/distribution-specific patient notice/consent approval evidence for the actual pilot architecture;
- applicable CNDP health-data processing evidence;
- foreign-transfer basis/evidence for every actual external destination where applicable;
- restricted residency manifest bound to the newly refrozen exact candidate and actual patient topology;
- exact-SHA consent and residency audit PASS outputs.

Public provider/CNDP documentation can define requirements but cannot substitute for account-specific approvals. Development-only Vercel/Neon infrastructure is excluded from the patient processor/residency inventory unless the actual pilot architecture later enables it for patient data.

The current pilot scope enables no external AI processor. `--local-only` remains mandatory for the consent audit when the gate is activated; it does not waive the global CNDP health-processing authorization gate.

### P5-6 success proof

When preparation for the first real-patient pilot starts, first explicitly re-freeze the exact release SHA and bind all restricted manifests to that same SHA and the actual patient runtime topology. Then all three fail-closed audits must PASS against it:

```bash
python manage.py audit_pilot_consent_governance \
  --local-only \
  --residency-manifest /restricted/iamina/pilot-residency.json \
  --require-approved \
  --expected-source-commit-sha <EXACT_REFROZEN_SHA>

python manage.py audit_pilot_data_residency \
  --manifest /restricted/iamina/pilot-residency.json \
  --require-approved \
  --expected-source-commit-sha <EXACT_REFROZEN_SHA>

python manage.py audit_safety_corpus_review \
  --manifest /restricted/iamina/safety-review-manifest.json \
  --require-approved \
  --expected-source-commit-sha <EXACT_REFROZEN_SHA>
```

Then and only then: explicit human real-patient release decision.

## P5-7 — Observed pilot evidence

**Status:** ⚪ PENDING P5-6.

Collect real pilot MAU/activation/retention, safety incidents, reliability/offline/update failures, LLM route/cost and zero-model rate, storage/egress cost, satisfaction/support burden and clinically safe usefulness signals. Synthetic evidence cannot become P5-7 proof.

## P5-8 — Go / No-Go

**Status:** ⚪ PENDING P5-7.

No second disease capsule before this evidence-based decision gate.

**P5 whole-lot tracker:** 4/9 = 44.4%.  
**Canonical global atomic tracker:** 6/12 = 50.0% with P5-4A closed.

---

# 4. MENA / multimodal residuals

## P0-MENA-2 — Locale + safety contract

**Status:** 🟡 IMPLEMENTATION CLOSED / PRE_REAL_PATIENT_EVIDENCE DEFERRED.

Runtime locale/high-severity variant coverage is implemented and bound into the exact safety corpus. Remaining release-relevant work is external/restricted review evidence under #318/P5-6A, activated before real-patient use rather than treated as current implementation debt.

## P0-MENA-4 — Multimodal provider benchmark

**Status:** 🟡 DEFERRED / EXTERNAL-HUMAN EVIDENCE, issue #319.

Groq + `openai/gpt-oss-120b` remains the conversational candidate; no local Arabic full-document OCR primary qualifies under the current strict floor; native TTS evidence is deferred to P5-3; STT remains deferred by owner decision.

Retained MENA metric: 32/38 = 84.2%, informational only.

---

# 5. Parallel engineering debt

`docs/TECHDEBT.md` owns unresolved compromises; it is not a competing roadmap. Critical/high debt is promoted into the current engineering path only when the corresponding feature is active or a current defect is reproduced. Pre-real-patient compliance evidence remains a separate future release gate.

Reconciliation retained through 2026-09-17:

- TD-010 observability retention lifecycle is CLOSED by PR #610, merge `e9c04beee31638ff86d7fd0b50d5eddccc313c4e`, post-merge CI #4206 / workflow `34787203311` SUCCESS and migration drift #3742 SUCCESS;
- former TD-005 and TD-006 were removed from the unresolved-debt register because current runtime safety variant coverage is implemented and the only remaining release gate is the restricted human qualification/approval evidence already owned by #318/P5-6A;
- former TD-007 was removed after verifying the explicitly approved/documented `SELF_CARE_ONLY` pilot operating model: PR #24 formalized no human monitoring, mandatory disclosure and fail-closed evidence requirements for any future `MONITORED_HUMAN` mode; P0.6 PR #128 later centralized all patient-facing urgent responses through that policy;
- TD-008 device-level critical-flow coverage is CLOSED by PR #636 / merge `532376020d4696d4098994a97a764a1994c7f92f`; the dedicated integration baseline landed, the resolved debt was removed in `8d54168674c316ddcc64846384b0bcac72650fe4`, and handover `4e7b04a3387da68374e00ab858e63b914faa1884` retained the closeout;
- historical TD-013 authentication abuse protection is CLOSED by PR #623, merged as `main@f045491a3e07db388067fe54c60fd0c4b543e050`; exact-head CI #4238 and drift #3760 succeeded, then exact-main post-merge CI #4241 and drift #3761 succeeded. Tracker #622 is closed. The retained limiter is PostgreSQL-backed, covers login/registration/password-reset, is independent of Redis availability, stores HMAC-derived identifiers rather than raw IP/email, and has typed 429/recovery tests;
- TD-003 provider timeout/circuit-breaker/failure UX is CLOSED by backend breaker PR #628, frontend typed-error UX PR #629 and docs closeout PR #630. Exact-head #629 CI #4280, Companion E2E #98, UI browser #710, UI geometry #707 and missing-routes #66 succeeded; #630 exact-head CI #4291 and post-merge CI #4292 succeeded;
- TD-014 patient local app-lock/re-authentication is CLOSED by PR #649 / merge `df457cfdcc574439adb791fbfc44d484a1224417`; final candidate `fd5bc4392ceda6b411b72f3ceb9254119024ac5c` passed 15/15 workflows and its fresh WebAuthn/offline/visual artifact was inspected. TD-014 is removed from the unresolved debt register.
- TD-012 remains OPEN. AISummary phase 2 is merged by PR #689; DocumentImport remains CLOSED by PR #692; Companion remains CLOSED by PR #695. Reports is CLOSED by PR #698 / `6920c20b67af466ac69a1be292a9afcd3b17ca91`, reducing `reports_screen.dart` from ~29.0k to ~3.8k characters while retaining DB/stream/period orchestration in the state file. Exact-head CI #4599, browser #970, geometry #855, Offline UI #97 and P5-5 #354 succeeded. Visual comparison: 390×844 pixel-identical; 768×1024 and 1280×900 differed only in the time-dependent timestamp text (158 pixels each), with no geometry change; visual score 9.9/10. IAmina chat remains CLOSED by PR #671; Profile remains CLOSED by PR #675.

---

# 6. CI / cost optimization

CI-FRUGAL-2 / #442 remains parallel and non-blocking. Runner-cost work must not weaken retained visual certification or safety/security gates.

---

# 7. Repository hygiene

Open GitHub items are not automatically active roadmap work. Historical Companion/OCR evidence issues and stale PRs remain evidence/hygiene until current-main reproduction proves forward work. Stale issue/PR state never changes product status without code + tests + retained evidence.

---

# 8. Closed workstreams retained as history

Closed unless a new reproduced regression opens a scoped lot: Gate A Secure Core; P0 foundations; product truthfulness; agent governance; global UX/Dashboard/Journal convergence; outbound AI/data-egress foundation; current sovereign-auth migration work recorded as merged; Companion intelligence/proactivity convergence; CGM gateway V1/V1.1/V2/V2.1; P4-FRUGAL PRE-PILOT; P5-0; P5-1; P5-2; P5-4A; P5-5; the P5-6 consent-evidence engineering atomic sublot; and TD-014 strong local app-lock.

Closed does not imply legal/CNDP authorization, physical-device proof, real-patient authorization or production approval unless that exact evidence is retained.

---

# 9. Execution order

1. **Current engineering:** continue auditing remaining `docs/TECHDEBT.md` items for staleness and prioritize reproduced security/reliability/accessibility defects solvable with synthetic/non-patient data.
2. Continue product/UX/reliability/security engineering while preserving fail-closed real-patient boundaries, the local-first runtime contract and the merged strong local app-lock boundary.
3. **Before the first identifiable real-patient health data:** explicitly re-freeze the chosen exact release SHA, reactivate P5-6A #318 and P5-6B #320, freeze the actual patient runtime topology, enumerate only genuinely enabled processors, and collect genuine restricted evidence/approvals.
4. If the pilot requires any remote deployment/distribution change, obtain separate explicit owner authorization before that deployment. Development Vercel deployment remains separately authorization-gated and is not patient production proof.
5. Freeze the actual pilot topology/residency evidence after every authorized deployment/distribution step relevant to patient processing.
6. Run the three exact-SHA fail-closed audits.
7. Explicit human real-patient release decision.
8. Controlled PWA pilot.
9. P5-7 observed evidence.
10. P5-8 go/no-go.

No Vercel deployment is authorized by this execution order.

---

# 10. Canonical governance

- `docs/ROADMAP.md` owns all forward status, priority, sequencing and completion percentages.
- `docs/LOCAL_FIRST_RUNTIME_BOUNDARY.md` owns the patient-runtime vs remote-dev/cert architecture boundary and is subordinate only to an explicit later change in this roadmap.
- Overall progress is the atomic 12-lot metric. Its denominator changes only through an explicit roadmap governance change.
- `docs/TECHDEBT.md` owns unresolved compromises only.
- `AGENTS.md` owns execution rules only and is subordinate to this roadmap for status.
- Issues/PRs are execution/evidence containers, not canonical portfolio status.
- Assessments/handovers/ADRs are evidence/history, not forward authority.
- Never declare a lot closed from a title, branch, PR state or old score alone.
- No Vercel deployment without explicit owner authorization; technical deployment authorization never implies real-patient release.
- Deferring P5-6A/P5-6B does not waive them. The boundary is before the first identifiable real-patient health data enters IAMINA.

## Current canonical snapshot

- repo: `hraaaaf/IAMINA-MVP`
- main reconciled for this lot: `6920c20b67af466ac69a1be292a9afcd3b17ca91`
- P5-4A AUTH-LOCAL-FIRST: **CLOSED**, PR #639 merged as `bd13e8ad0c6f3ff2c4376b00c43fb8c54068d053`
- TD-014 strong local app-lock: **CLOSED**, PR #649 merged as `df457cfdcc574439adb791fbfc44d484a1224417`; final candidate `fd5bc4392ceda6b411b72f3ceb9254119024ac5c` had 15/15 SUCCESS
- last explicitly frozen P5-6 SHA: `fb42e4d641b7b057607fe6a2de3d5104ccf15d0b` — **historical freeze evidence, not current release candidate**
- current release candidate: **NONE / PENDING EXPLICIT REFREEZE**
- historical freeze proof: PRs #602/#603; #603 post-merge CI #4190 / workflow `34773613905`; post-merge drift #3737 / workflow `34773613814`
- patient production runtime boundary: **LOCAL-FIRST; Vercel/Django/Neon excluded unless a future explicit architecture change says otherwise**
- proven predecessor remote dev/cert deployment: `dpl_8ex2k82KaozE6Fxc8wQBYJuRU43y`, source `5b27a22fc5c05a06e7eeeb0e841bb0e7dadce7f6`, Python function, `cdg1`, health HTTP 200 / `db=ok`
- dedicated remote dev/cert database proof: Neon `IAMINA` / `square-sun-82359137`, PG16, `aws-eu-central-1`, branch `production`, migrations current for the predecessor remote deployment
- safety fingerprint retained from historical freeze: `823d109b0ddd10d1874eec53027eafd9d65884f14810304af3681c57c82cf7e5`
- qualification wording: **professionnels qualifiés** — owner attestation reference `issue-318:owner-attestation:professionnels-qualifies`
- consent notice: `2026-09-12.1`
- canonical global progress: **6/12 = 50.0% with P5-4A closed**
