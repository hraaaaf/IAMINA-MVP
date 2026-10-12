# IAMINA V1-01 / CAL-11 — Apple numeric UI parity: scope and remaining proof

**Date:** 2026-10-12. **Status:** engineering oracle candidate; screenshots **NOT VERIFIED**. No patient authorization, no clinical/nutrition reviewer approval, no merge, no Vercel deployment.

## Goal / success / evidence
Confirm the USDA-derived apple lower bound moves from 14.2 to 14.1 g per 100 g across the actual NutritionPortionEditor, without a hidden unit, dose, treatment or unsupported personal precision claim. Use identical 100 g selection, locales FR/EN/AR and viewports 390×844, 768×1024, 1280×900.

## Source-backed BEFORE / AFTER code evidence
- **BEFORE** [#943 `f7ebe654cd69a03acf6a3694ff0633e8a5b5042e`](https://github.com/hraaaaf/IAMINA-MVP/commit/f7ebe654cd69a03acf6a3694ff0633e8a5b5042e): apple carbohydrate `14.2–15.7 g/100g`; five old FDC identifiers from a previous source mapping.
- **AFTER code parent** [#945 `34dd3fbfab7c8b125f2097546ce18d1bbc3d5f58`](https://github.com/hraaaaf/IAMINA-MVP/commit/34dd3fbfab7c8b125f2097546ce18d1bbc3d5f58): `14.1–15.7 g/100g`; five matching IDs from pinned official USDA Foundation April 2026 archive. The interval for 100 g is **14.1–15.7 g of carbohydrates**, not insulin dose. No source-backed unit weight for a generic whole apple is claimed.
- Product rendering: `nutrition_portion_editor.dart` multiplies the per-100g range by user-entered grams and formats to one decimal, shows `g` and source publisher; `formatLocalizedCarbRange` isolates the numeric range in Arabic RTL. Expected UI output for 100 g: FR `≈ 14.1–15.7 g de glucides`; EN `≈ 14.1–15.7 g carbohydrates`; AR `≈ 14.1–15.7 غ كربوهيدرات` (with Unicode numeric isolation markers).
- New automated widget oracle `frontend/test/l10n/nutrition_bidi_contract_test.dart` checks actual rendering string, USDA publisher, RTL order and no widget exception across all 3 locales × 3 viewports. **Only mark it PASS after exact-new-HEAD CI shows it executed successfully.**

## Limits, blockers, human gates
- No machine/browser was reachable for actual BEFORE/AFTER visual screenshots in this session: remote desktop offline; local GitHub DNS inaccessible. **BLOCKED_DEVICE_BROWSER** for screenshots. Widget tests are automated text/layout evidence, **not** screenshot inspection and do not justify a visual score.
- The live UI/UX screenshot matrix must still be obtained and personally inspected, same state/viewports/locale; independently evaluate text scaling and clinical comprehensibility.
- USDA primary-source CI and quantitative correctness do not approve the cultivar-to-generic-apple mapping for an individual patient, nor dose/treatment advice. Nutrition reviewer remains mandatory.
- **CAL-09/10** clinical-day policy and **CAL-12** Unicode/RTL typed clinical PDF/consent scope remain unresolved human gates. PDF stays OFF. No merge, no Vercel, no patient usage.
