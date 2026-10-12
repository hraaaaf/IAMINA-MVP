# IAMINA V1-01 / CAL-11 — Apple numeric UI parity: scope and remaining proof

**Date:** 2026-10-12. **Status:** real-Chromium UI parity 9/9 visually reviewed on HEAD `357aa1e…`; startup/semantics JavaScript warning under separate investigation. Not yet clinical/product certification. No patient authorization, no clinical/nutrition reviewer approval, no merge, no Vercel deployment.

## Goal / success / evidence
Confirm the USDA-derived apple lower bound moves from 14.2 to 14.1 g per 100 g across the actual NutritionPortionEditor, without a hidden unit, dose, treatment or unsupported personal precision claim. Use identical 100 g selection, locales FR/EN/AR and viewports 390×844, 768×1024, 1280×900.

## Source-backed BEFORE / AFTER code evidence
- **BEFORE** [#943 `f7ebe654cd69a03acf6a3694ff0633e8a5b5042e`](https://github.com/hraaaaf/IAMINA-MVP/commit/f7ebe654cd69a03acf6a3694ff0633e8a5b5042e): apple carbohydrate `14.2–15.7 g/100g`; five old FDC identifiers from a previous source mapping.
- **AFTER code parent** [#945 `34dd3fbfab7c8b125f2097546ce18d1bbc3d5f58`](https://github.com/hraaaaf/IAMINA-MVP/commit/34dd3fbfab7c8b125f2097546ce18d1bbc3d5f58): `14.1–15.7 g/100g`; five matching IDs from pinned official USDA Foundation April 2026 archive. The interval for 100 g is **14.1–15.7 g of carbohydrates**, not insulin dose. No source-backed unit weight for a generic whole apple is claimed.
- Product rendering: `nutrition_portion_editor.dart` multiplies the per-100g range by user-entered grams and formats to one decimal, shows `g` and source publisher; `formatLocalizedCarbRange` isolates the numeric range in Arabic RTL. Expected UI output for 100 g: FR `≈ 14.1–15.7 g de glucides`; EN `≈ 14.1–15.7 g carbohydrates`; AR `≈ 14.1–15.7 غ كربوهيدرات` (with Unicode numeric isolation markers).
- New automated widget oracle `frontend/test/l10n/nutrition_bidi_contract_test.dart` checks actual rendering string, USDA publisher, RTL order and no widget exception across all 3 locales × 3 viewports. **Only mark it PASS after exact-new-HEAD CI shows it executed successfully.**

## Limits, blockers, human gates
- Remote desktop remained offline, but isolated real-Chromium GitHub Actions resolved the original **BLOCKED_DEVICE_BROWSER** screenshot blocker. **18 PNG were independently inspected** from the exact-HEAD GitHub artifact. The isolated widget fixture is not the complete production navigation flow.
- Widget tests remain separate from real browser evidence, and neither provides clinical or nutrition approval.
- USDA primary-source CI and quantitative correctness do not approve the cultivar-to-generic-apple mapping for an individual patient, nor dose/treatment advice. Nutrition reviewer remains mandatory.
- **CAL-09/10** clinical-day policy and **CAL-12** Unicode/RTL typed clinical PDF/consent scope remain unresolved human gates. PDF stays OFF. No merge, no Vercel, no patient usage.

## Actual BEFORE / AFTER real-Chrome evidence — inspected 2026-10-12

- Certified source code and run: [PR #945 commit `357aa1eef009e7b85d1e822a1fbea2def606b18c`](https://github.com/hraaaaf/IAMINA-MVP/commit/357aa1eef009e7b85d1e822a1fbea2def606b18c), [GitHub Actions browser run #38303516146](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38303516146) **SUCCESS**, [artifact `cal11-apple-100g-before-after-18-png`](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38303516146/artifacts/11771359007). Artifact expires **2026-11-02**, retain/re-run for later review.
- Actual product widget `NutritionPortionEditor` was unchanged versus #943, exact same grams=100 locale and viewport. Measured FR/EN/AR × (390×844, 768×1024, 1280×900) × BEFORE/AFTER = **18 real Chrome PNGs**, verified PNG dimensions and SHA-256 against signed job observations JSON.
- FR screenshot displayed `≈ 14.2–15.7 g de glucides` BEFORE vs `≈ 14.1–15.7 g de glucides` AFTER. EN and Arabic similarly preserve translated strings, source publisher, RTL alignment and range order.
- **Independent pixel-difference measurement:** for all **9/9** paired before/after comparisons the bounding box of all changed pixels is precisely **7×11 px**, localized to the single lower-bound digit (`2`→`1`); no shifted or clipped layout found in the 18 inspected images. This is a **9/9 visual numeric-parity score for the isolated widget**, **not** a 10/10 clinical UI/UX certification.
- **Open browser error:** all 18 test observations log `Cannot read properties of undefined (reading 'update')` as a **nonfatal pageerror**, including baseline BEFORE and corrected AFTER. Being present in both versions demonstrates no new differential in this pair, but does **not** establish its root cause or justify a full no-runtime-error claim. Next QA commit captures precise stack and phase; classify whether fixture's Flutter web semantics activation or wider runtime. **The browser proof remains qualified pending that diagnostic.**
- Separate [Flutter exact-HEAD CI #38303516137](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38303516137) was still in progress when this protocol amendment was prepared. Do not transfer success status from the previous HEAD to a later SHA.

**Next exact:** diagnose captured browser pageerrors without altering patient code; re-check full CI of the new exact HEAD; then independent human nutrition validation, CAL-09/10 day boundary and CAL-12 consent/privacy (PDF OFF). No merge or deployment without approval.
