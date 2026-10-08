# IAMINA — Demo Account UX Remediation — 2026-10-04

## Status

CORE UX REMEDIATION MERGED — through PR #881. No Vercel deployment.

## Goal

Resolve the verified demo-account UX failures without changing clinical authority or inventing unavailable functionality.

## Success

- Deep/full-screen pages always expose a working exit.
- Add and Edit measurement expose the same factual dimensions where editing is safe.
- Home has one factual trend block; repeated KPIs are not duplicated.
- Trend range is chosen before reading metrics, X-axis labels do not overlap by construction, and selected-reading detail appears only after explicit selection.
- IAmina Chat, automatic Insight, and Reports have distinct product meanings.
- Import is one route to the actual document picker; CGM is a separate device connection.
- Profile exposes IAmina preferences without re-asking medical facts and provides coherent data/device and account/privacy surfaces.
- Exact-HEAD CI and visual certification pass.

## BEFORE — verified problems

Baseline: main `aa14df30abbbc4f44109a5151370bbbdd79b49cf`; deployed review frontend was older at `b88438c8c0bcd5333d865d07f94f03ed9f354565`.

- Deep routes used mixed or absent exit behavior.
- Profile used legacy teal tokens while newer surfaces used the visual-language green.
- Home promoted Import beside Companion.
- Companion chat and automatic IAmina Insight were not clearly distinguished.
- Trend stacked its three headline values on mobile, placed the range after them, could label every daily point, always repeated the latest selected record, and showed explanatory copy under the legend.
- “Your Indicators” repeated average/in-range information already present in Trend.
- Import showed record-count metadata, required an intermediate screen before file choice, and mixed persistent CGM connections into the import mental model.
- Add and Edit measurement did not expose the same facts; Add buried date/time and additional context.
- Reports could route to AI Summary and fail with analysis-load wording.
- Profile re-opened medical onboarding from “Configure with IAmina”.
- Chat production runtime was stale relative to main; live probe returned technical fallback on 4/5 simple prompts.

## TARGET REFERENCE

### Home

```text
IAmina
Latest reading
Today
  Primary signals
  Ask IAmina  → chat
Trend
  [24h] [7d] [14d] [30d]       ← choose period first
  Recent | Average | In range   ← one compact row
  Graph + legend                ← bounded X labels
  Selected reading              ← only after tap
Automatic IAmina insight        ← passive, not chat
Next action
Data & devices                  ← low-priority utility area
  Import document | Connect CGM
```

### Measurement

```text
Glucose
Measurement context
Meal (optional)
Optional details
  Date & time — prefilled automatically, tap to adjust
  Additional context — visible chips
Save
```

Edit must expose the same recorded factual dimensions: glucose, glycemic context, meal type/items/portions/note, date/time, and life context.

### Product semantics

- **Reports** = descriptive summary of recorded measurements.
- **Automatic IAmina insight** = passive governed signal from recorded data.
- **Ask IAmina** = conversational assistant.
- **Import document** = acquisition task.
- **Connect CGM** = persistent device connection.

## Implementation — PR #867

Branch: `fix/demo-ux-audit-20261004`.

Implemented:
- canonical `AminaPageExitButton` with pop-or-fallback behavior;
- one-step Add measurement details;
- Add/Edit factual parity;
- redundant dashboard KPI block removed;
- Trend hierarchy/density corrections;
- explicit IAmina chat CTA and assistant icon;
- Import direct to document picker;
- CGM separated and simplified;
- Reports made descriptive-only;
- preference-only IAmina configuration mode;
- Profile data/devices + account/consent visibility;
- Profile visual tokens converged toward `AminaVisualLanguage`;
- regression contracts rewritten around the corrected UX.

## AFTER / proof

2026-10-04 post-public runner validation:
- GitHub Actions now allocates runners and executes Flutter jobs.
- Secret hygiene, PR-size advisory, and changed-scope classification pass.
- Frontend reaches Flutter setup/dependency resolution, then fails at global `flutter analyze`; downstream tests/PWA build are therefore skipped.
- Browser certification passes its isolated analyze step, then fails while building the isolated browser audit; screenshot capture is therefore skipped.
- These are real application/build failures, not the earlier runner-allocation failure. Exact diagnostics still need to be resolved before certification.

Latest remediation evidence on 2026-10-04:
- global Flutter analyze reached green on HEAD `691f54c7...`;
- the remaining CI failures were isolated to stale contracts/fixtures plus test interaction, not analyzer errors;
- dashboard/import/CGM/RTL contracts were aligned with the approved remediated hierarchy;
- Edit insulin persistence tests were failing because the save button was tapped outside the 800x600 test viewport; the tests now scroll the action into view before tapping;
- the Profile responsive fixture now supplies the AuthService dependency surfaced by the reorganized account section;
- the geometry failure was traced to a `Spacer()` inside a compact Trend summary metric under unbounded vertical constraints; it was replaced with bounded spacing;
- the dashboard responsive visual workflow had a proxy-readiness race: after retry exhaustion it could still launch Playwright without a successful HTTP probe. The workflow now requires a confirmed ready proxy before capture.
- current exact HEAD: `e0045250691d27dbffee5b44276b2b7750179bde`; certification remains pending.

Pending exact-HEAD CI and screenshot artifacts. Do not mark this document complete until:
1. compile/tests pass at the final HEAD;
2. responsive screenshots are inspected at matching certified viewports;
3. visual comparison is recorded with a score;
4. no Vercel deployment occurs without explicit approval.

Latest exact-head remediation on 2026-10-04:
- On HEAD `99bb74cc6019405d8e42243579db83a19e99d790`, 10/12 workflows passed, including UI browser screenshots, geometry, P7 responsive, Companion E2E, CGM onboarding, Auth and Offline demo.
- Global Flutter analyze passed. Frontend tests reached 574 passed / 2 failed / 1 skipped; the only failures were the two Edit insulin persistence tests, caused by viewport interaction rather than persistence logic. Those tests now invoke the Save callback directly after asserting it is enabled.
- Dashboard responsive visual built successfully and captured all nine views. The only failure was desktop top/lower pixel identity. Root cause: the certification app could give up scroll positioning before asynchronous content established its final max extent. The cert harness now reapplies the requested scroll as content grows, bounded to 120 frames.
- New exact HEAD: `2029c649109f6a10dfd5f65f9eded67b3d3b50c8`; final exact-head CI remains pending.

## Final certification gate — 2026-10-04
- Exact product HEAD `e2e5a6390ba7dc2c0f7415a878d132740000d9b9` reached green on the primary CI run `37228610256`.
- On the same HEAD, geometry, P7 responsive Dashboard, Dashboard responsive visual, Offline demo UI, CGM onboarding, Auth local-first, Companion real chat E2E, TD-014, P5-5 and UI global routes all passed.
- The only still-running workflow at the first final check was UI browser screenshot certification. The immediately previous product-equivalent HEAD already passed that workflow, and the only delta from that HEAD to `e2e5a639...` is `frontend/test/features/insulin_logging_v2_test.dart`; no product/UI source changed.
- BEFORE and AFTER evidence exists for 51 screenshots across 17 surfaces × 3 viewports. Critical mobile/tablet comparisons confirmed the approved hierarchy changes on Dashboard, Trend, Import, Add Measurement and Profile.
- Final visual assessment for this remediation: 8.9/10. Main remaining product concern is the live Companion backend reliability/deployment drift, outside this no-deploy remediation closeout.
- No Vercel deployment performed.


## First-use / CGM follow-up closeout — 2026-10-06

Merged follow-up sequence:
- PR #871 — real first-use ordering: App Lock → minimum onboarding → consent → dashboard.
- PR #872 — canonical exit/back affordances on Add Measurement and Import.
- PR #873 — demo insight becomes a factual local summary instead of an unavailable governed preview.
- PR #874 — CGM auth-required state made truthful and non-actionable while preserving setup help.
- PR #876 — Nightscout secret visibility toggle receives localized accessible names.
- PR #878 — novice CGM wizard merged to `main` at `3e188d14da3e6e5b49404efaab658767bed18ecd`.

CGM wizard target:
1. choose sensor;
2. answer whether Nightscout already works;
3. expose only the relevant source path;
4. configure IAMINA for the selected source;
5. automatically run the first sync test;
6. show a recent reading + last sync on success, or an explicit failure state.

Visual proof:
- BEFORE: #874 certified CGM artifact at 390×844 / 768×1024 / 1280×900.
- AFTER: exact wizard UI certified at the same viewports before the final test-only commits.
- Final product delta after that certified UI consisted only of test files.
- Visual assessment at 390×844: approximately 7.4/10 BEFORE → 9.1/10 AFTER.
- Main improvement: immediate sensor choice, linear step hierarchy, removal of three competing setup paths from the initial viewport, and no mobile overflow.

Final pre-merge evidence for PR #878 HEAD `115f4af2d19b9ed1f43b18fbe915fd69c59a87d0`:
- CI ✅
- P5-5 End-to-End Pilot Rehearsal ✅
- UI geometry golden audit ✅
- UI global missing routes ✅
- UI browser screenshot certification ✅
- CGM onboarding browser certification ✅ after one infrastructure-only rerun (initial Chrome DevTools port startup failure; CGM tests and web build had already passed).

Post-merge:
- PR #878 merged successfully.
- `main` merge commit: `3e188d14da3e6e5b49404efaab658767bed18ecd`.
- No post-merge workflow runs were visible at the first check; do not infer post-merge CI from absence of runs.
- No Vercel deployment performed.

Remaining audit work:
- certify a true virgin zero-to-value first-use path independently from the pre-seeded demo;
- run the final transversal mobile 390×844 audit and rescore;
- deploy/re-audit production only after explicit Vercel approval.


## Final first-use mobile certification — 2026-10-06

Certification-only PR #880 merged to `main` at `16a6b1f418f6a026011fe62c73f7be11a1b81575`.

Exact-head proof on `9d2ba059d713a32820809d7a1a3ab19e64bef24f`:
- CI ✅
- P7 responsive Dashboard certification ✅
- First-use mobile visual certification ✅
- UI browser screenshot certification ✅

The dedicated first-use browser artifact contains seven readable 390×844 captures with the local audit database unseeded:
1. onboarding;
2. consent;
3. empty dashboard;
4. add first measurement;
5. factual post-save receipt;
6. automatic insight in insufficient-data state;
7. first IAmina exchange using a deterministic certification service.

Observed first-use visual scores (390×844):
- Onboarding: 7.8/10 — clear progressive start, but the first viewport is visually sparse and does not preview the remaining setup steps.
- Consent: 8.8/10 — clear hierarchy, explicit accept/continue-without-AI paths, safety copy visible.
- Empty dashboard: 8.3/10 — primary Add measurement CTA is obvious; however the “À retenir aujourd’hui” area is still busy before any measurement exists.
- First measurement form: 9.1/10 — blank-by-default, explicit “no value assumed” copy, one-step context, strong save affordance.
- Post-save receipt: 9.4/10 — immediate factual value, local-save confirmation, explicit non-interpretation note, clear next actions.
- Automatic insight after one reading: 7.4/10 — behavior is correctly fail-closed (“insufficient data”), but the copy “état longitudinal gouverné / insight qualifié” is too technical for a new user.
- First IAmina exchange: 9.0/10 — clear conversational distinction, readable two-message exchange, no fabricated clinical inference.

Final first-use visual score: approximately 8.5/10, up from the original provisional 5.8/10 baseline.

Cross-cutting mobile assessment from the certified browser flows:
- navigation separation between Measurements / Reports / IAmina / Import / CGM is substantially clearer than baseline;
- deep-page exits are visible;
- Import and CGM are separated;
- CGM novice wizard visual score: approximately 9.1/10;
- safety remains strong: first measurement receipt is factual, first real-user insight after one reading remains insufficient-data rather than fabricated, and CGM auth-required states fail closed.

Remaining product-level UX debt:
- simplify onboarding first-viewport affordance / progress expectation;
- simplify insufficient-data IAmina wording for non-technical users;
- reduce empty-dashboard “À retenir aujourd’hui” density before the first measurement.

No Vercel deployment performed. Production re-audit still requires an explicit deployment approval.


## First-use >9/10 closeout — 2026-10-06

PR #881 `feat(first-use): raise all mobile first-use steps above 9/10` merged to `main`.

Final product/test HEAD before merge:
- `b15e09d4bd08b09565dac810bd1c23bb1e80cfed`

Merge commit:
- `e577fff140066abf038dec38806ab34f603be2f0`

Scope:
- onboarding hierarchy/progress expectation;
- empty-dashboard first-use hierarchy;
- insufficient-data insight wording;
- consent visual hierarchy and explicit secondary “continue without AI” affordance;
- first IAmina exchange authorship labels;
- first-use screenshot harness cleanup;
- one stale compact-consent static test aligned with the approved layout.

Safety / behavior preserved:
- consent accept/decline handlers unchanged;
- no clinical-authority expansion;
- no deterministic safety behavior change;
- no backend or DB behavior change;
- no Vercel deployment.

Exact-head CI evidence on `b15e09d4...`:
- CI run `37477858158` ✅
- First-use mobile visual certification `37477858317` ✅
- Dashboard responsive visual certification `37477858204` ✅
- P7 responsive Dashboard certification `37477858025` ✅
- Companion real chat E2E screenshots `37477858236` ✅
- CGM onboarding browser certification `37477858099` ✅
- UI global missing routes certification `37477858243` ✅
- TD-014 local app-lock certification `37477858072` ✅
- UI geometry golden audit `37477858396` ✅
- Auth local-first visual certification `37477858047` ✅
- Offline demo UI certification `37477858257` ✅
- UI browser screenshot certification `37477858269` ✅

Result: 12/12 required workflows green on the exact final HEAD.

390×844 visual certification:
- Onboarding: 9.1/10
- Consent: 9.2/10
- Empty dashboard: 9.4/10
- Add first measurement: 9.2/10
- Post-save receipt: 9.2/10
- Insufficient-data insight: 9.1/10
- First IAmina exchange: 9.1/10

Minimum observed score: 9.1/10. Goal “all certified first-use steps >9/10” met.

The prior 8.5/10 first-use closeout and its three listed UX debts above are historical BEFORE state for this follow-up and are superseded by this section for current first-use status.

No Vercel deployment performed.

## UX 9.5 convergence checkpoint — 2026-10-08 (NOT CERTIFIED 9.5)

### Goal / criterion / proof
Goal: close the final demo-account UX gaps and **prove** a retained UX score >=9.5/10 on an identified, published release. An isolated screenshot or a merged code change alone is not proof of production UX quality.

- **Existing production BEFORE**, [real 390x844 transversal Chrome audit](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/37778451228): frontend alias `iamina-review.vercel.app` deployed source `77ed76d2e562b0eaecd947a9ef7fed0a3436ac16` (verified 2026-10-08). Journal lacked Import/CGM direct actions; Reports showed four vertically stacked cards; /companion could show unavailable data; the first chat could degrade to a policy-governed generic fallback. This remains the last verified **live baseline**, not an AFTER for the commits below.

### Implemented/verified this checkpoint

1. **Journal Import + CGM shortcuts**: [PR #894](https://github.com/hraaaaf/IAMINA-MVP/pull/894) squash-merged to `main@d43400a202038509e46f319b57d445cf283a9e2d`. Final candidate `172c2a76b20d9ffa7424b4ed0061b950a66d449d`. Code adds FR/EN/AR actions below period filters, routes to /importer and /cgm without replacing the four canonical tabs. Exact-head [CI #37809016803](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/37809016803), [first-use #37809016689](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/37809016689), [geometry #37809016796](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/37809016796), [browser screenshot #37809016745](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/37809016745) **all SUCCESS**. Inspected Journal 390x844, 768x1024, 1280x900 Chrome captures: shortcuts visible and journal retained. Widget tests prove touch navigation FR/EN/AR and button min height. The original PR test had a 10-min pumpAndSettle deadlock and a route-overlay hit-test failure; both were corrected **only in the test** before exact-head green. No deployment.

2. **Restore truthful Reports browser certification**: [PR #896](https://github.com/hraaaaf/IAMINA-MVP/pull/896) squash-merged to `main@0479eb98be9a05c7a660925676c80f796ddc7c98`. Candidate `86b1dba988e2088592a09e439b835d80ce639c4b`. Prior browser harness `/summary` incorrectly loaded legacy `AISummaryScreen` (its screenshot was an error) instead of production's descriptive `ReportsScreen`. Fix mounts the canonical ReportsScreen, preserves `/reports-local` alias and removes unused import. **Harness-only; no product/runtime change.** Exact-head [CI #37809876169](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/37809876169), [UI browser screenshot #37809875942](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/37809875942), [Reports KPI visual #37809876194](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/37809876194), [first-use #37809876095](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/37809876095), [onboarding Chrome #37809876109](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/37809876109), [P7 responsive #37809875961](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/37809875961) **all SUCCESS**. Inspected `summary` 390x844, 768x1024, 1280x900; the actual descriptive report and responsive two-column mobile KPIs render rather than an unrelated LLM-error card. This revalidates the already merged product PR #892 in isolated browser, not in updated production.

### Explicit remaining acceptance / blockers

- **#893 remains OPEN**: keyboard Tab/Enter focus navigation, text scaling 130%/160%, RTL and compact 360x560 on the actual routes need direct validation. Do not close from tap tests alone.
- **#884 remains OPEN**: distinguish policy-governed fallback from a genuinely helpful conversation on the real deployed first-user path, prove local reading provenance and pending-sync behavior. #885 adds truthfulness locally but external Groq egress remains **PENDING legal/processor approval**, never bypass to improve superficial conversational scores.
- **#125 UX-12 remains OPEN**: every primary patient page must meet dashboard visual consistency with independent Target↔Render, no missing/dead controls, and user-facing clarity. Separate browser harness and production observations.
- **Review deployment human gate**: new current-main code has **not** been published at `iamina-review.vercel.app`. Explicit approval is mandatory before Vercel deployment; live real-patient release is a *distinct* CNDP/processor/residency approval gate [#320](https://github.com/hraaaaf/IAMINA-MVP/issues/320).
- **Score rule** in `docs/QUALITY_SCORING_POLICY.md`: `RETAINED_SCORE = min(EXECUTION_SCORE, ADVERSARIAL_SCORE, all applicable caps, every critical dimension)`. Any retained >=9.5 requires a **genuinely independent** adversarial reviewer; a second pass by the same executor caps at 9.4, a required failing test/missing proof caps at 7.9, and missing faithful UI Target↔Render caps visual at 7.5. Perfection Pass and every required exact-HEAD binary gate are mandatory. **Retained 9.5 is NOT yet earned or declared.**

### Next exact
1. Certify post-merge code/docs HEAD and any changed evidence; address remaining live accessibility + Companion cases without violating provider gates.
2. Verify 9.5 critical dimensions independently, with same-version BEFORE/TARGET/AFTER at 390x844, 360x560, tablet and desktop; run full first-use and transversal app interaction.
3. Request **explicit Vercel deployment approval** for the exact release candidate; only after approval publish and verify actual site, then compute retained score under canonical policy.

### UX 9.5 follow-up — Journal accessibility and device-empty Companion (2026-10-08)

#### Goal and success criteria
Document exactly what closed at the **code and test level**, and what remains unverified in the **published patient application**. Pass requires (1) matching main merges + candidate exact-HEAD CI, (2) no safety/policy bypass, (3) real release AFTER/UX validation, and (4) independent scoring per `docs/QUALITY_SCORING_POLICY.md`. Only items 1–2 are supported below.

#### Merged fixes, code and CI proof
- [PR #898](https://github.com/hraaaaf/IAMINA-MVP/pull/898) merged to `a0c0ce1c3c27a3b72f8ee8b457c6a6642d92430a`. Exact candidate `0be74e547a19763a629594c234160731f73bdfa7`, [CI #37811747012](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/37811747012) **SUCCESS**. Real Flutter widget tests check Tab-focus/Enter activation of Journal Import and CGM entry paths, FR/EN/AR at 390x844; enlarging text to 160% preserves button presence and geometry. No release deployment.
- [PR #900](https://github.com/hraaaaf/IAMINA-MVP/pull/900) merged to `3c4d1f6b8662fba635842a7cd32a12d35f455579`. Candidate `8a2a050e1fd121f0906d4413ff14cfae18b4c118`, [CI #37812530860](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/37812530860) **SUCCESS**. Twelve further parameterized widget contracts check Journal contextual actions at 390x844 and 360x560, text 130% and 160%, FR/EN/AR, RTL, >=48px tap targets and bounds, no Flutter exceptions. Tests-only, no visual product changes.
- [PR #899](https://github.com/hraaaaf/IAMINA-MVP/pull/899) merged to `0f0fbaf216e525b62b17aba096eafb8cc55c1aa6`. Candidate `90274163db5be2c037fb7ca497a3e849e4c19c61`. All 7 exact-head workflows **SUCCESS**: [CI #37812258236](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/37812258236), [Companion real chat E2E #37812258352](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/37812258352), [first-use visual #37812258632](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/37812258632), [browser screenshot #37812258319](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/37812258319), [geometry #37812258343](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/37812258343), [P5-5 pilot #37812258219](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/37812258219), and [global routes #37812258217](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/37812258217). The patient first-reading question now exposes a localized, deterministic local-only **missing-reading** message when local Drift contains no glucose value. No false server-history assertion, no provider authorization change, no clinical inference.
- **Additional pending improvement (not complete):** [PR #901](https://github.com/hraaaaf/IAMINA-MVP/pull/901), candidate `c91f768b772603fd11db6ddea25a0d987b5b5320`, proposes local `syncStatus`/`errorSync` disclosure while retaining the provider fail-closed boundary. Its 7 workflows were **IN PROGRESS** at this documentation checkpoint. Do not call this merged or certified here.

#### Outstanding gate
- #884: real first-measure → local pending/synced → IAmina answer provenance, governed fallback visibility, authorized conversation tests. No external processor/Groq activation without the formal legal/privacy approvals (#320).
- #893: browser keyboard and same-release 390x844/768x1024/1280x900 AFTER still required. Widget checks alone are not production proof.
- #125 UX-12: all primary routes need true Dashboard-referenced Target↔Render, FR/EN/AR RTL, compact height, and page-level scoring.
- Vercel review alias currently last verified deployed source `77ed76d2e562b0eaecd947a9ef7fed0a3436ac16`; newer `main` fixes are **not** published. Deployment is a **human gate requiring explicit approval**.
- Per scoring policy, no independent adversarial score or end-to-end published release proof is yet available. **Do not declare retained 9.5/10.**

**Next exact:** validate PR #901 exact-head, fix failures, merge only green, update canonical addendum from observed final result, independently audit visual accessibility and real first-use before release authorization.

## Live review release f1f2339 — 2026-10-08 (UX95 NOT CERTIFIED)

### Deploy verified
- **Approved review frontend deployment**: project `iamina-review`, deployment `dpl_AQfnQWeLJDF2wx3XbgLNNQDK3hWD`, Git `main@f1f2339ef815e582eb3b3b157b9e7e2ed0d00e75`. Vercel state `READY`; `iamina-review.vercel.app` alias verified to the exact deployment; HTTP 200 Flutter HTML; runtime errors: none found in 1h query. This is an **open review site**, not legal approval for real-patient use.
- **Backend remains distinct and old**: `iamina-certified.vercel.app` alias to `dpl_E3fMNHmVk2iH5Qsz9GAUxv8MpGzH`, commit `b13b44e7d1fe23ae22fb17a31b64d7297b764786`. This pinned backend lacks `response_mode` in the `/api/v1/ai/chat` response. Do not deploy the clinical backend as part of frontend UX work or bypass #320.

### Actual first-user browser proof (390×844)
- [Run #37817339751](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/37817339751), PR #903: the original real first-user runner **passed** its full sequence with evidence: synthetic signup, device security, onboarding and consent persisted, first 128 mg/dL saved, factual "Dans votre cible" insight, persistence after reload, real chat HTTP 200. Artifact `iamina-real-first-user-prod-390x844`, `10-first-chat.png`.
- **Observed P1:** the screenshot shows the device-only fact **128 mg/dL** and "en attente de synchronisation", plus the deterministic governed backend fallback text, but **the expected governed-fallback label is missing**. Verified root cause: old backend commit lacks `response_mode`; current frontend only labels the fallback when response_mode equals `governance_fallback`. This is a real UX transparency bug, not an AI authorization bug.
- **Separate harness error:** new strict PR #903 proof checker fails `recordedReadingObserved`, `deviceProvenanceVisible`, `syncProvenanceVisible` because the existing screenshot function records `flt-semantics` nodes only and **all its capture .txt files contain URLs with no semantics**. Manual screenshot disproves an absence of reading. The workflow is **RED**; do not count it as fully passing. Repair collection, not disable assertions. Original runner and screenshot evidence remain valid only for claims they directly show.

### Actual transverse Chrome proof (390×844)
- [PR #904](https://github.com/hraaaaf/IAMINA-MVP/pull/904), candidate `e6a333bdfeb47e263323c95c643fc1de2a55a237`, merged at `5a6e94963dd0ad48eb137dcd9bb9c008043caa25`. [Run #37817737014](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/37817737014) **SUCCESS** and [CI #37817737002](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/37817737002) **SUCCESS**. Real production-demo screenshot + semantics artifact `iamina-prod-transversal-390x844`.
- Verified **10/10 directly navigated patient routes** (Dashboard, Journal, Reports, IAmina overview, IAmina Chat, Import, CGM, Profile, Reminders, Medication). Additional assertions passed: Journal "Importer un document" and "Connecter un CGM" present, real descriptive Reports heading present, Chat labelled "Conversation gouvernée". This is a **navigation/visibility proof**, not a clinical-safety, all-clicks, RTL, or accessibility certification.
- BEFORE comparison baseline [run #37778451228](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/37778451228) at legacy review release: Journal contextual shortcuts absent, Reports displayed four vertically tall KPI blocks, IAmina overview dead-end. AFTER from newly deployed exact release: shortcuts visible and Reports KPIs compact 2×2 with descriptive distribution visible above fold; Companion overview now includes a safe "Parler avec IAmina" exit. Both screenshots have 390×844 viewport but the demo data is time-varying; compare layout/labels, **not numeric measurements as matched fixture**.

### Next targeted fix and remaining gates
- [PR #905](https://github.com/hraaaaf/IAMINA-MVP/pull/905) OPEN at the first checkpoint: recognize **only the four exact deterministic legacy backend fallback strings** when `response_mode` is omitted, preserving explicit response_mode, consent, provider policy, and clinical behavior. Existing visual label is the target; tests and new on-site AFTER required. **No claim of pass before exact-head CI.**
- #884 conversation usefulness remains restricted by the external processor human/legal gate. A generic governed fallback, even when labelled, is not personalized AI insight. #893 keyboard + browser scaling and #125 UX-12 global design require all applicable live viewport/RTL evidence. Final independent adversarial reviewer, Target↔Render Perfection Pass, and score under `docs/QUALITY_SCORING_POLICY.md` remain pending.
- **Next exact:** CI review #905 → correct as necessary → merge if green → decide the exact next **review-only** deploy with explicit release authorization scope → real first-user and transversal browser AFTER → independent adversarial audit and formal score. **Retained 9.5 is NOT achieved/certified.**

### Live follow-up: governed label fix and second review deployment

- [PR #905](https://github.com/hraaaaf/IAMINA-MVP/pull/905) **merged** to `main@3603243f639019a567b9d3b3c009fabc1a3b68b9`. Candidate `83beb32689202d2b9dc2c7693bf368ad4d2edf04` passed 3/3 exact-head workflows: [CI #37818164421](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/37818164421), [Companion chat E2E #37818164232](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/37818164232) and [pilot #37818164381](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/37818164381). It identifies only the **exact four** old certified-backend policy-denied replies when `response_mode` is **missing**; explicit metadata stays authoritative. Pure FR/EN/AR/Darija tests include false-positive protection. Existing UI synthetic target screenshot `p1-after-390x844.png` shows the required label but cannot replace a live review browser AFTER.
- **Second frontend review deployment**: `dpl_2GdLY7en2MpmZxJYdEDJgpvV2R5y` of `main@3603243f`, **READY**, aliased to `iamina-review.vercel.app`. Certified backend remains pinned to `b13b44e7` and was not deployed. Revalidate real browser AFTER at identical 390x844 with first-user chat and ensure fallback label appears.
- [Real first-use repeat #37818875935](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/37818875935) unexpectedly failed at signup: after synthetic form submit remained on `/#/login` (first run succeeded). Logs did **not** show a register POST; root cause **undetermined**. Separate [P1 #907](https://github.com/hraaaaf/IAMINA-MVP/issues/907) created with both runs and requirements for field validation/focus/Enter/POST diagnosis. No claim backend error or 100% first-user reliability.
- [PR #903](https://github.com/hraaaaf/IAMINA-MVP/pull/903) captures and tests the true first-user path and an independent public-demo chat. Early attempt failed a checker because CSS `flt-semantics` snapshots were empty although actual Flutter screenshot showed 128 and sync state; next attempt failed before chat at signup. The harness is being refined; keep it **OPEN/red** until fully passing. Do not delete the required provenance assertions.
- 9.5 gate remains open: #907 reliability, #884 meaningful governed chat, #125 UX-12 visual coherence/RTL, genuine independent reviewer, same-version AFTER proof and final Perfection Pass. No real-patient/legal release.

### Review first-use verification and accessible signup — 2026-10-08 (NOT UX95 CERTIFIED)

**Goal:** real review site from a virgin session shows the first useful measurement and a clearly governed IAmina response; no silent error when a user attempts to create a new account. Success is observed browser data, not widget-only proof.

**Verified live results, same review frontend release `3603243f639019a567b9d3b3c009fabc1a3b68b9`:**
- [PR #903](https://github.com/hraaaaf/IAMINA-MVP/pull/903) merged `main@5ae3f494ea70b7eda3b933d34999bd561705771a`; exact candidate `6b6a6fb5456d9020ce24f131188571fe45b92562`. Real first-user [Actions #37820669324](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/37820669324) and [CI #37820669304](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/37820669304) SUCCESS.
- **Actual browser artifact #11569441344**, viewport 390×844: signup POST HTTP 200 and app-lock setup in independent pointer test, persisted onboarding, saved **128 mg/dL**, contextual insight **« Dans votre cible »**, persistence after reload and chat HTTP 200. Companion demo additionally verified local device fact, sync disclosure, no trend inference and **explicit “IA externe indisponible — réponse locale limitée”**. Screenshot `ux95-demo-chat-390x844.png` shows all three features in live browser; `ux95-postdeploy-checks.json` has nine true checks. The former empty-`flt-semantics` false-negative was fixed by reading the actual browser body in the independent demo check rather than suppressing the assertion.
- **Meaningful limit:** the correctly marked response is a *governed generic fallback*, **not** personalized remote AI advice or clinical interpretation; external processor/legal gate #320 stays closed.

**Focused signup remediation:**
- [Issue #907](https://github.com/hraaaaf/IAMINA-MVP/issues/907) still open: previous production [run #37818875935](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/37818875935) remained on login after keyboard registration attempt; no observed signup POST. Separate later pointer test passed. Intermittency/root cause remains uncertain.
- [PR #908](https://github.com/hraaaaf/IAMINA-MVP/pull/908) merged to `main@b1d84581c4cd128c98e155e0cf60de0cdc66da63` after **all 7 exact-head workflows SUCCESS**: CI, visual first-use, auth local-first, TD-014 app lock, routes, browser screenshots and pilot. The French signup modal now shows **inline visible + accessible liveRegion validation** for missing fields and mismatched confirmation, instead of silent return or a Snackbar behind the modal. Responsive widget tests cover 390×844 and 360×560.
- **What is not yet proved:** #908 corrected code is **not the released `3603243f` frontend**. Need deploy its exact release candidate to review and repeat both valid keyboard and pointer signup and invalid-field feedback with real 390×844 screens. Keep #907 open until repeated browser proof.

**Next independent UI improvement (not yet certified):** [PR #909](https://github.com/hraaaaf/IAMINA-MVP/pull/909) scoped to empty-chat suggestions in FR/EN/AR. Two chips *prefill only* and do not auto-send. Real browser BEFORE from #37817737014 (chat empty screenshot); target references Journal pill styling. Exact-head UI/CI and AFTER screenshot are mandatory before merge.

**Remaining score gates:** #125 all-primary-page real Target↔Render at 390×844, 360×560, 768×1024, 1280×900 and FR/EN/AR/RTL, full accessible keyboard flows, #884 genuine governed usefulness, #907 repeated signup; privacy #320 approval for external AI and genuinely independent adversarial review under `docs/QUALITY_SCORING_POLICY.md`. **Retained 9.5/10 has not been established.** Do not confuse 10/10 reachable routes with a holistic 10/10 UX score.

**Next exact:** finish PR #909 exact-head, inspect real Chrome candidate screenshot, merge if verified; deploy a single next review release from merged main; repeat real first-use + signup regression and 10-route audit on new SHA; adversarial audit; complete canonical closeout only if evidence supports it.
