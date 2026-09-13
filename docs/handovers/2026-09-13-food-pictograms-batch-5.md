# IAMINA — Food pictograms Batch 5

Status: ACTIVE — exact-main recertification

## Goal

Extend native FoodPicker pictogram coverage from 96 to 120 concepts without changing nutrition logic, catalog structure, search behavior or runtime render priority.

Success = exact manifest-derived 24-item Batch 5, native union exactly 120, pairwise disjoint batches, every ID bound to the catalog, long-tail emoji fallback preserved, semantics preserved, exact-head CI/geometry/P5-5/P7/Chrome green on the current main-based branch, and AFTER evidence inspected at 390×844 / 768×1024 / 1280×900.

## Source of truth

`frontend/tool/food_pictogram_manifest.dart` and `frontend/lib/core/data/meal_food_catalog.dart`.

Ordering contract: first 48 launch IDs, then remaining catalog sorted by `MealFoodCategory.index`, then French label using Dart `String.compareTo`, split into 24-item batches.

Batch 4 consumes `aseeda` as its final Gulf item. Batch 5 therefore continues from the next exact sorted Gulf concept.

## Exact Batch 5

`fish_biryani`, `chicken_biryani`, `lamb_biryani`, `falafel`, `fattoush`, `foul_medames`, `kabsa_lamb`, `khabeesa`, `machboos_fish`, `majboos_shrimp`, `machboos_lamb`, `madrooba`, `manakish_cheese`, `manakish_zaatar`, `mandi_lamb`, `margoog`, `moutabal`, `mutabbaq`, `muhammar_rice`, `saleeg`, `saloona`, `samboosa_cheese`, `samboosa_meat`, `shakshuka`.

## UI/UX certification

BEFORE: certified Batch-4 surface, same production FoodPicker and viewports 390×844 / 768×1024 / 1280×900.

Goal: expose several newly-native Machboos variants with the already-native Batch-2 chicken Machboos as a retained baseline.

Reference: established IAMINA native pictogram language: compact 44–48 px recognition, soft contact shadow, restrained teal accent, no text/logo, no external assets, offline-safe.

AFTER fixture: search query `machboos`.

Comparison scope: same surface/viewports/layout. Displayed data intentionally changes to expose Batch-5 artwork, so this is not a pixel-for-pixel content comparison.

## Verified integration state

- Batch 4 merged to `main` as `e68b516277a138e4e2f9d757ef59759f062e0a02`.
- Batch 5 was reconstructed/retargeted onto that exact main base before this certification refresh.
- The previous exact Batch-5 head had Geometry, P7 responsive and Chrome green; this documentation commit intentionally triggers a fresh exact-head certification so CI and P5-5 are also proven on the current head before merge.

## Validation gate

Before merge:
- product tests for exact 24 + union 120 + catalog binding + fallback + semantics;
- visual contract test for five fixed disjoint 24-item batches;
- exact-head CI, geometry, P5-5, P7 responsive and Chrome SUCCESS;
- AFTER screenshots inspected at all three viewports;
- explicit visual score recorded.

No Vercel deployment is part of this lot.
