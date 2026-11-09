# IAMINA D13 — Web guarded glucose save after D22 (03-11-2026)

**Decision:** D13 — Block Back/Discard while an actual glucose INSERT is in flight.

**Goal:** save one and only one user-entered measurement while preventing exits through the inline back button, page header, system PopScope and native browser-history Back during an asynchronous Drift INSERT.

**Base:** `main@c2fc32bbd31a24fe17542e6abda96d937905737b`, D22 `TECHNICALLY_ACCEPTED / SCOPED_CLOSED / MERGED`. D22 medical/scientific G1–G7 are deferred to D32 and not imported here.

**Change:** scoped D13 navigation guard in AddLogSheet, AddLogScreen and GoRouter; existing D22 glucose half-dial and unit preference, values, clinical logic and storage schema are preserved. No backend, database schema or Vercel settings touched.

**Evidence plan:** (1) Flutter widget tests with delayed real Drift INSERT, failure/abandon and exactly one persisted row; (2) real Chromium FR/AR at 390×844, 768×1024 and 1280×900 for inline Back + browser-history Back during pending INSERT, receipt, reload and exact persisted value 126 mg/dL; (3) CI analysis and independent review on exact candidate HEAD. Browser runner checks the current D22 dial rather than obsolete `input.flt-text-editing` CSS host. Never infer successful save solely from form HTML.

**Status at creation:** CANDIDATE / NO-GO; CI and AFTER visual evidence not yet inspected on this SHA, independent review pending. No patient go-live, deployment or merge authorization. Historical PR #1215 remains draft for provenance; its FUE run #41418493386 failed 6/6 with `D13_INPUT_NOT_OBSERVABLE` after D22 changed the widget DOM.

**Next:** inspect SHA-specific runs; diagnose any failing steps without concealing failed scenarios; validate UI BEFORE/AFTER and a11y at required viewports; independent review and release certifier; merge only if Vercel auto-deploy gate is explicitly safe and owner-authorized. D12 follows D13.
