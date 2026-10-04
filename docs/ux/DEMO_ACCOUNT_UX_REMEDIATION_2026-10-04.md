# IAMINA — Demo Account UX Remediation — 2026-10-04

## Status

IN PROGRESS — PR #867. No Vercel deployment.

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
