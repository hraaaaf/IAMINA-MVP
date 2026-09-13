# IAMINA — Food pictograms Batch 6

Status: ACTIVE

## Goal

Extend native FoodPicker pictogram coverage from 120 to 144 concepts, stacked on Batch 5, without changing nutrition logic, catalog structure, search behavior or runtime render priority.

Success = exact manifest-derived 24-item Batch 6, native union exactly 144, all six batches pairwise disjoint, every ID bound to the catalog, long-tail emoji fallback preserved, semantics preserved, exact-head CI/geometry/P5-5/P7/Chrome green after Batch 5 integration, and AFTER evidence inspected at 390×844 / 768×1024 / 1280×900.

## Source of truth

`frontend/tool/food_pictogram_manifest.dart` + `frontend/lib/core/data/meal_food_catalog.dart` on Batch-5 head `7c034f17f8a3cbfdef3dfb1feedc16a6b18d696b`.

Ordering contract: first 48 launch IDs, then remaining catalog sorted by `MealFoodCategory.index`, then French label using Dart `String.compareTo`, split into 24-item batches.

Batch 5 ends at `shakshuka`. Batch 6 therefore consumes the final three non-priority Gulf concepts, all remaining non-priority meat/poultry concepts, then the first nine remaining fish/seafood concepts.

## Exact Batch 6

`shawarma_beef`, `shuwa`, `tabbouleh`, `lamb`, `chicken_breast`, `minced_beef`, `lamb_chops`, `turkey`, `liver`, `kefta`, `merguez`, `roast_chicken`, `sausage`, `beef_steak`, `veal`, `sea_bass`, `squid`, `crab`, `shrimp`, `sea_bream`, `prawns`, `mackerel`, `hake`, `mussels`.

## UI/UX certification

BEFORE: certified Batch-5 FoodPicker surface, same production surface and viewports 390×844 / 768×1024 / 1280×900.

Goal: expose new beef-family Batch-6 pictograms while retaining the already-native Batch-1 beef baseline.

Reference: established IAMINA native pictogram language: compact 44–48 px recognition, soft contact shadow, restrained teal accent, no text/logo, no external assets, offline-safe.

AFTER fixture: search query `bœuf`.

Comparison scope: same surface/viewports/layout. Displayed data intentionally changes to expose Batch-6 artwork, so this is not a pixel-for-pixel content comparison.

## Validation gate

Before merge:
- Batch 5 integrated into `main`, then Batch 6 resynced onto exact base;
- exact 24 + native union 144 + catalog binding + fallback + semantics tests;
- visual contract for six fixed disjoint 24-item batches;
- exact-head CI, geometry, P5-5, P7 responsive and Chrome SUCCESS;
- AFTER screenshots inspected at all three viewports;
- explicit visual score recorded.

No Vercel deployment is part of this lot.
