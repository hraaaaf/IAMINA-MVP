# IAMINA — Food pictograms Batch 7

Status: ACTIVE

## Goal

Extend native FoodPicker pictogram coverage from 144 to 168 concepts, stacked on Batch 6, without changing nutrition logic, catalog structure, search behavior or runtime render priority.

Success = exact manifest-derived 24-item Batch 7, native union exactly 168, all seven batches pairwise disjoint, every ID bound to the catalog, first post-Batch-7 long-tail fallback preserved, semantics preserved, exact-head CI/geometry/P5-5/P7/Chrome green after Batch 6 integration, and AFTER evidence inspected at 390×844 / 768×1024 / 1280×900.

## Source of truth

`frontend/tool/food_pictogram_manifest.dart` + `frontend/lib/core/data/meal_food_catalog.dart` inherited from Batch-6 branch rooted at Batch-5 head `7c034f17f8a3cbfdef3dfb1feedc16a6b18d696b`.

Ordering contract: first 48 launch IDs, then remaining catalog sorted by `MealFoodCategory.index`, then French label using Dart `String.compareTo`, split into 24-item batches.

Batch 6 ends at `mussels`. Batch 7 continues with the final three remaining fish/seafood concepts, all non-priority egg concepts, then the first 18 non-priority dairy concepts. `greek_yogurt` is the first item outside Batch 7 and remains the fallback sentinel.

## Exact Batch 7

`fish`, `octopus`, `tuna`, `omelette`, `fried_egg`, `boiled_egg`, `butter`, `cream`, `feta`, `cheese`, `processed_cheese`, `fresh_cheese`, `cream_cheese`, `halloumi`, `laban`, `labneh`, `camel_milk`, `semi_skimmed_milk`, `whole_milk`, `skimmed_milk`, `mozzarella`, `qishta`, `raib`, `yogurt`.

## UI/UX certification

BEFORE: certified Batch-6 FoodPicker surface, same production surface and viewports 390×844 / 768×1024 / 1280×900.

Goal: expose several newly-native milk concepts while retaining the Batch-1 `milk` baseline in the same search result family.

Reference: established IAMINA native pictogram language: compact 44–48 px recognition, soft contact shadow, restrained teal accent, no text/logo, no external assets, offline-safe.

AFTER fixture: search query `lait`.

Comparison scope: same surface/viewports/layout. Displayed data intentionally changes to expose Batch-7 artwork, so this is not a pixel-for-pixel content comparison.

## Validation gate

Before merge:
- Batch 6 integrated into `main`, then Batch 7 resynced onto exact base;
- exact 24 + native union 168 + catalog binding + fallback + semantics tests;
- visual contract for seven fixed disjoint 24-item batches;
- exact-head CI, geometry, P5-5, P7 responsive and Chrome SUCCESS;
- AFTER screenshots inspected at all three viewports;
- explicit visual score recorded.

No Vercel deployment is part of this lot.
