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

Pending exact-HEAD CI and screenshot artifacts. Do not mark this document complete until:
1. compile/tests pass at the final HEAD;
2. responsive screenshots are inspected at matching certified viewports;
3. visual comparison is recorded with a score;
4. no Vercel deployment occurs without explicit approval.
