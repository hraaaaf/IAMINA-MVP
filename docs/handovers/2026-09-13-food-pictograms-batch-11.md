# IAMINA — Food pictograms Batch 11

Status: FINAL CERTIFICATION — aligned to current main; exact-head gates required before merge

## Goal

Extend native FoodPicker pictogram coverage from 240 to 264 concepts without changing nutrition logic, catalog structure, search behavior or runtime render priority.

Success = exact manifest-derived 24-item Batch 11, native union exactly 264, all eleven batches pairwise disjoint, every ID bound to the catalog, first post-Batch-11 long-tail fallback preserved, semantics preserved, exact-head CI/geometry/P5-5/Chrome green after current-main integration, and AFTER evidence inspected at 390×844 / 768×1024 / 1280×900.

P7 responsive Dashboard certification is N/A for this FoodPicker-only lot because that workflow is path-filtered to Dashboard files.

## Source of truth

`frontend/tool/food_pictogram_manifest.dart` + `frontend/lib/core/data/meal_food_catalog.dart`.

Ordering contract: first 48 launch IDs, then remaining catalog sorted by `MealFoodCategory.index`, then French label using Dart `String.compareTo`, split into 24-item batches.

Batch 10 ends at `chia_seeds`. Batch 11 continues with the eight remaining nut/seed concepts, all twelve remaining non-priority fat/sauce concepts, then the first four remaining drink concepts. `coconut_water` is the first item outside Batch 11 and remains the fallback sentinel.

## Exact Batch 11

`flax_seeds`, `sunflower_seeds`, `hazelnuts`, `walnuts`, `cashews`, `pistachios`, `almond_butter`, `sesame`, `chermoula`, `harissa`, `argan_oil`, `sunflower_oil`, `ketchup`, `mayonnaise`, `olives`, `barbecue_sauce`, `hot_sauce`, `soy_sauce`, `garlic_sauce`, `tahini`, `ayran`, `energy_drink`, `coffee`, `water`.

## UI/UX certification

BEFORE: certified Batch-10 FoodPicker surface, same production surface and viewports 390×844 / 768×1024 / 1280×900.

Goal: expose several newly-native sauce concepts in one search while retaining the established IAMINA compact artwork language.

Reference: established IAMINA native pictogram language: compact 44–48 px recognition, soft contact shadow, restrained teal accent, no text/logo, no external assets, offline-safe.

AFTER fixture: search query `sauce`.

Observed retained product proof:
- 390×844: sauce-family results render cleanly in one column; CTA and consent copy remain visible; no observed collision, overflow or clipped label.
- 768×1024: same result family remains clean in one column; no observed collision or overflow.
- 1280×900: clean two-column result grid; no observed collision or overflow.
- Pre-existing horizontal category rail edge clipping remains scroll behavior, not a Batch-11 regression.

Visual score retained pending final exact-head artifact: 9.3/10.

## Verified integration and proof

- Batch 10 merged to `main` as `7e858710776a12d84a3db4ba8e9ef966ce80c010`.
- Batch 11 exact-head `10d205f88b0ac46c890ce0577f30945fa899c175` was fully certified before `main` advanced:
  - CI `34905567932` — SUCCESS
  - UI geometry `34905568031` — SUCCESS
  - P5-5 `34905567789` — SUCCESS
  - UI browser screenshot certification `34905567737` — SUCCESS
  - Chrome artifact `10372554693`, digest `sha256:c7a06dcab8a9f98516bb3a9c4d294300f3094e2e22d8b60c22def2940d3230cd`.
- The exact artifact ZIP digest matched locally and the `sauce` surface was inspected at 390×844, 768×1024 and 1280×900.
- `main` then advanced to `4f873001910d7b065860aff87bf5b1d9f2cbd99b` through PR #628, which changes backend AI/circuit-breaker files only and does not touch FoodPicker/frontend/docs paths.
- Batch 11 was therefore rebuilt on that current main while preserving the backend changes from #628.
- Current-main compare is behind 0 and contains only the twelve expected Batch-11 implementation/docs/fallback-test paths.
- Batch-11 contract remains: exact 24 IDs, native union 264, pairwise-disjoint batches, catalog binding, localized native semantics, and first post-Batch-11 fallback preserved.

Final current-main exact-head CI/geometry/P5-5/Chrome run IDs and exact Chrome artifact are recorded in PR #616 metadata after certification. P7 is N/A, not green.

No Vercel deployment is part of this lot.
