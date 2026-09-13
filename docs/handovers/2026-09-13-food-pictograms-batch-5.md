# IAMINA — Food pictograms Batch 5

Status: ACTIVE

## Goal

Extend native FoodPicker pictogram coverage from 96 to 120 concepts, stacked on Batch 4, without changing nutrition logic, catalog structure, search behavior or runtime render priority.

Success = exact manifest-derived 24-item batch 5, native union exactly 120, pairwise disjoint batches, every ID bound to the catalog, long-tail emoji fallback preserved, semantics preserved, exact-head CI/geometry/E2E/responsive/Chrome green after Batch 4 is integrated, and AFTER evidence inspected at 390×844 / 768×1024 / 1280×900.

## Source of truth

`frontend/tool/food_pictogram_manifest.dart` and `frontend/lib/core/data/meal_food_catalog.dart` on the Batch-4 base derived from `main@eb588496fc380f1ae0bbabd69ba4d28067a933b1`.

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

## Validation gate

Before merge:
- Batch 4 must be integrated into `main` and Batch 5 resynced onto that exact base;
- product tests for exact 24 + union 120 + catalog binding + fallback + semantics;
- visual contract test for five fixed disjoint 24-item batches;
- exact-head CI, geometry, P5-5, P7 responsive and Chrome SUCCESS;
- AFTER screenshots inspected at all three viewports;
- explicit visual score recorded.

No Vercel deployment is part of this lot.
