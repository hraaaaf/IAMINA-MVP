# IAMINA — Food pictograms Batch 13

Status: FINAL CERTIFICATION — rebuilt on merged Batch 12; exact-head gates required before merge

## Goal

Extend native FoodPicker pictogram coverage from 288 to 312 concepts without changing nutrition logic, catalog structure, search behavior or runtime render priority.

Success = exact manifest-derived 24-item Batch 13, native union exactly 312, all thirteen batches pairwise disjoint, every ID bound to the catalog, first post-Batch-13 fallback preserved, semantics preserved, exact-head CI/geometry/P5-5/Chrome green, and AFTER evidence inspected at 390×844 / 768×1024 / 1280×900.

P7 responsive Dashboard certification is N/A for this FoodPicker-only lot because that workflow is path-filtered to Dashboard files.

## Source of truth

`frontend/tool/food_pictogram_manifest.dart` + `frontend/lib/core/data/meal_food_catalog.dart`.

Ordering contract: first 48 launch IDs, then remaining catalog sorted by `MealFoodCategory.index`, then French label using Dart `String.compareTo`, split into 24-item batches.

Batch 12 ends at `ice_cream`. Batch 13 contains the sixteen remaining non-priority dessert concepts, then the first eight remaining snack/fast-food concepts. `sandwich` is the first item outside Batch 13 and remains the fallback sentinel.

## Exact Batch 13

`cake`, `bastilla_milk`, `khanfaroosh`, `kunafa`, `maamoul`, `mhalbiya`, `mhancha`, `honey`, `molasses`, `umm_ali`, `qatayef`, `sago_dessert`, `date_syrup`, `stevia`, `sugar`, `brown_sugar`, `bocadillo`, `chips`, `fries`, `hot_dog`, `nuggets`, `panini`, `popcorn`, `fried_chicken`.

## Integration maintenance

Batch 13 makes `cake` native. Eight inherited fallback checks use `sandwich` instead:
- Batch 6 fallback test;
- Batch 7 fallback test;
- Batch 8 fallback test;
- Batch 9 fallback test;
- Batch 10 fallback test;
- Batch 11 fallback test;
- Batch 12 fallback test;
- generic deterministic asset-path/emoji-fallback test.

## Current-main integration

- Batch 12 merged through PR #617 as `0ba77c5802cbab4008fb4ed43485dc3aa8351353`.
- Batch 13 was reconstructed from that exact `main` tree with only the 14 intended FoodPicker implementation/docs/fallback-test paths.
- Companion chat drift found in the old prepared tree was explicitly excluded from the rebuilt tree.
- Compare against merged Batch 12: ahead 1, behind 0, exactly 14 expected paths.
- Runtime priority unchanged: certified asset > native painter > emoji fallback.

## UI/UX certification

BEFORE: certified Batch-12 FoodPicker surface, same production surface and viewports 390×844 / 768×1024 / 1280×900.

Goal: expose the newly-native fried-chicken concept on the same FoodPicker surface.

Reference: established IAMINA native pictogram language: compact 44–48 px recognition, soft contact shadow, restrained teal accent, no text/logo, no external assets, offline-safe.

AFTER fixture: search query `poulet frit`.

Retained product proof exists for the same Batch-13 rendering. Final merge still requires exact-head proof on the final branch head.

## Validation gate

Before merge:
- exact 24 + native union 312 + catalog binding + fallback + semantics tests;
- visual contract for thirteen fixed disjoint 24-item batches;
- exact-head CI, geometry, P5-5 and Chrome SUCCESS;
- P7 recorded N/A, not green;
- AFTER screenshots inspected at all three viewports;
- explicit visual score recorded;
- PR review/thread/mergeability rechecked.

No Vercel deployment is part of this lot.
