# IAMINA — Food pictograms Batch 11

Status: FINAL CERTIFICATION — aligned to merged Batch 10; exact-head gates required before merge

## Goal

Extend native FoodPicker pictogram coverage from 240 to 264 concepts without changing nutrition logic, catalog structure, search behavior or runtime render priority.

Success = exact manifest-derived 24-item Batch 11, native union exactly 264, all eleven batches pairwise disjoint, every ID bound to the catalog, first post-Batch-11 long-tail fallback preserved, semantics preserved, exact-head CI/geometry/P5-5/Chrome green after Batch 10 integration, and AFTER evidence inspected at 390×844 / 768×1024 / 1280×900.

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

Manual AFTER inspection on product head `605bb94e3936bd718740a38b8ae9cc94daf571bc`:
- 390×844: sauce-family results render cleanly in one column; CTA and consent copy remain visible; no observed collision, overflow or clipped label.
- 768×1024: same result family remains clean in one column; no observed collision or overflow.
- 1280×900: clean two-column result grid; no observed collision or overflow.
- Pre-existing horizontal category rail edge clipping remains scroll behavior, not a Batch-11 regression.

Visual score: 9.3/10.

## Verified integration and proof

- Batch 10 merged to `main` as `7e858710776a12d84a3db4ba8e9ef966ce80c010`.
- Batch 11 was rebuilt content-identically on that exact `main`; integration head before this documentation closeout was `dee1e1571df9b1a64bbec568f7c174915fa22ede`.
- Compare against merged Batch 10: behind 0; only six Batch-11 implementation/docs files plus six inherited fallback-test updates.
- Product visual proof retained on `605bb94e3936bd718740a38b8ae9cc94daf571bc`:
  - UI geometry run `34819733134` — SUCCESS
  - UI browser screenshot certification run `34819733141` — SUCCESS
  - Chrome artifact `10338450490`, digest `sha256:ca0731d55447fd393ed96b3a08a0e1a675af1cb31e2387825d0e873e7b9425de`.
- Local artifact ZIP SHA-256 independently matched the GitHub digest.
- AFTER files were inspected at 390×844, 768×1024 and 1280×900.
- Batch-11 contract remains: exact 24 IDs, native union 264, pairwise disjoint batches, catalog binding, localized native semantics, and first post-Batch-11 fallback preserved.

Final exact-head CI/geometry/P5-5/Chrome run IDs and exact Chrome artifact are recorded in PR #616 metadata after certification. P7 is N/A, not green.

No Vercel deployment is part of this lot.
