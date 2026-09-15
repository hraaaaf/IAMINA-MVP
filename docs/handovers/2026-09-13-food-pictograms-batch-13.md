# IAMINA — Food pictograms Batch 13

Status: PREPARED — awaiting Batch-12 merge and exact-main reconstruction

## Goal

Extend native FoodPicker pictogram coverage from 288 to 312 concepts without changing nutrition logic, catalog structure, search behavior or runtime render priority.

Success = exact manifest-derived 24-item Batch 13, native union exactly 312, all thirteen batches pairwise disjoint, every ID bound to the catalog, first post-Batch-13 fallback preserved, semantics preserved, exact-head CI/geometry/P5-5/Chrome green after Batch 12 integration, and AFTER evidence inspected at 390×844 / 768×1024 / 1280×900.

P7 responsive Dashboard certification is N/A for this FoodPicker-only lot because that workflow is path-filtered to Dashboard files.

## Source of truth

`frontend/tool/food_pictogram_manifest.dart` + `frontend/lib/core/data/meal_food_catalog.dart`.

Ordering contract: first 48 launch IDs, then remaining catalog sorted by `MealFoodCategory.index`, then French label using Dart `String.compareTo`, split into 24-item batches.

Batch 12 ends at `ice_cream`. Batch 13 contains the sixteen remaining non-priority dessert concepts, then the first eight remaining snack/fast-food concepts. `sandwich` is the first item outside Batch 13 and remains the fallback sentinel.

## Exact Batch 13

`cake`, `bastilla_milk`, `khanfaroosh`, `kunafa`, `maamoul`, `mhalbiya`, `mhancha`, `honey`, `molasses`, `umm_ali`, `qatayef`, `sago_dessert`, `date_syrup`, `stevia`, `sugar`, `brown_sugar`, `bocadillo`, `chips`, `fries`, `hot_dog`, `nuggets`, `panini`, `popcorn`, `fried_chicken`.

## Prepared integration maintenance

Batch 13 makes `cake` native. After Batch 12 merges, eight inherited fallback checks must therefore use `sandwich` instead:
- Batch 6 fallback test;
- Batch 7 fallback test;
- Batch 8 fallback test;
- Batch 9 fallback test;
- Batch 10 fallback test;
- Batch 11 fallback test;
- Batch 12 fallback test;
- generic deterministic asset-path/emoji-fallback test.

## UI/UX certification

BEFORE: certified Batch-12 FoodPicker surface, same production surface and viewports 390×844 / 768×1024 / 1280×900.

Goal: expose the newly-native fried-chicken concept on the same FoodPicker surface.

Reference: established IAMINA native pictogram language: compact 44–48 px recognition, soft contact shadow, restrained teal accent, no text/logo, no external assets, offline-safe.

AFTER fixture: search query `poulet frit`.

Retained product proof exists for the same Batch-13 rendering. Final merge still requires exact-head reconstruction/certification after Batch 12 merges.

## Validation gate

Before merge:
- Batch 12 integrated into `main`, then Batch 13 reconstructed on exact current main;
- exact 24 + native union 312 + catalog binding + fallback + semantics tests;
- visual contract for thirteen fixed disjoint 24-item batches;
- exact-head CI, geometry, P5-5 and Chrome SUCCESS;
- P7 recorded N/A, not green;
- AFTER screenshots inspected at all three viewports;
- explicit visual score recorded.

No Vercel deployment is part of this lot.
