# Dashboard P7 — Responsive convergence closeout

Date: 2026-08-17

## Goal

Converge Dashboard to one governed patient product across mobile, tablet and desktop. Viewport width may change density and composition only; it must not swap product authority or clinical semantics.

## Certified product state

- `/dashboard` resolves to `DashboardCompanionEntryScreen` across viewports.
- The previous `<700px` route-level product fork is removed.
- The same Today / Trend / Adaptive KPI / Smart Insight / Next Action authorities are preserved across sizes.
- Mobile remains single-column; wider layouts use bounded responsive composition.
- Trend keeps recorded points factual and adds only visual trajectory segments between sufficiently close successive recordings. Large temporal gaps remain disconnected; no continuity is invented.
- The latest recorded trend point is visually emphasized and the configured target band is visually reduced in dominance.
- No new clinical formula, threshold, ranking, proactive authority, diagnosis, prescription, dose change or autonomous treatment action was introduced.

## Exact-head evidence

Certified PR head: `0775b9fd67bd301e9aeec30fba7c81fadddbbd49`.

Required pull-request gates on that exact head:

- CI #2751 — success
- Django migration drift #2563 — success
- UI screenshot audit #312 — success
- P7 responsive Dashboard certification #7 — success
- UI browser screenshot certification #289 — success

Real Chrome evidence was produced at 390×844, 768×1024 and 1280×900, including the Dashboard and Trend surfaces. Native responsive evidence covered 699×900, 701×900, 1440×1000 and Arabic/RTL 900×900.

The Flutter golden audit uses the Ahem test font and is therefore a structural/layout regression proof, not a visual-design review artifact. Visual design review is based on real Chrome captures.

## Merge

PR #306 merged to `main` as `446c27636853265d9b37186df16dda9feae1243e`.

Historical stacked P7 PR #284 was closed without merge and superseded by the clean reconstruction from certified P6.

## Post-closeout visual coherence correction

A subsequent real Chrome review exposed a duplicate desktop identity in the left navigation rail: a fictive ECG mark plus a duplicate `IAmina / Compagnon Diabète` block coexisted with the canonical Dashboard identity.

Correction PR #310 removed `_EcgMarkPainter` and `_BrandHeader` from the desktop shell and updated the anti-regression contract so the navigation shell must not render a second brand identity. Navigation, routing, clinical semantics and responsive authority were unchanged.

Certified correction head: `87a8a02ecf83ff358984c71cd4982bbcbdda47bd`.

Exact-head correction gates:

- CI #2763 — success
- Django migration drift #2575 — success
- UI screenshot audit #314 — success
- UI browser screenshot certification #291 — success

Real Chrome 1280×900 evidence confirms that the left rail now begins with the Add Entry CTA and only the canonical IAMINA identity remains visible on the Dashboard.

PR #310 merged to `main` as `78622f869e19e24f12675ff7ecd8793616ac252b`.

## Result

P7 responsive convergence, including the post-closeout single-brand correction, is closed at the engineering/UI certification level. This workstream is separate from the 32/41 MENA critical-path numerator and does not change that numerator.

No Vercel deployment was performed.
