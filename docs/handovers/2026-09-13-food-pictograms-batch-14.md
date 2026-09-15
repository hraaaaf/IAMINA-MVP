# IAMINA — Food pictograms Batch 14

Status: PREPARED — awaiting Batch-13 merge and exact-main reconstruction

## Goal

Finish native FoodPicker pictogram coverage from 312 to the full 322-concept catalog without changing nutrition logic, catalog structure, search behavior or runtime render priority.

Success = exact manifest-derived final 10-item Batch 14, native union exactly equal to all 322 catalog IDs, all fourteen batches pairwise disjoint, semantics preserved, exact-head CI/geometry/P5-5/Chrome green after Batch 13 integration, and AFTER evidence inspected at 390×844 / 768×1024 / 1280×900.

P7 responsive Dashboard certification is N/A for this FoodPicker-only lot because that workflow is path-filtered to Dashboard files.

## Source of truth

`frontend/tool/food_pictogram_manifest.dart` + `frontend/lib/core/data/meal_food_catalog.dart`.

Ordering contract: first 48 launch IDs, then remaining catalog sorted by `MealFoodCategory.index`, then French label using Dart `String.compareTo`, split into 24-item batches. Batch 14 is intentionally partial because it exhausts the catalog.

Batch 13 ends at `fried_chicken`. Batch 14 contains the two remaining snack/fast-food concepts, all three meal-salad concepts, and all five soup concepts.

## Exact Batch 14

`sandwich`, `tacos_wrap`, `chicken_caesar_salad`, `tuna_salad`, `greek_salad`, `chorba`, `lentil_soup`, `vegetable_soup`, `chicken_soup`, `tomato_soup`.

## Final mathematical contract

The final Batch-14 test must prove on the exact merge head:
- Batch 14 length = 10;
- Batch 14 is disjoint from Batches 1→13;
- union Batches 1→14 length = 322;
- that union equals `mealFoodCatalog.map((item) => item.id).toSet()` exactly.

Only after those checks pass may the chantier be described as 322/322 native.

## Final fallback regression contract

After Batch 14 there is intentionally no real catalog item outside the native union. Historical fallback regression tests must therefore stop using a real catalog sentinel such as `sandwich`.

Nine fallback checks require the same synthetic outside-catalog probe on the final lot:
- Batch 6 through Batch 13 fallback tests: 8 checks;
- generic deterministic asset-path/emoji-fallback test: 1 check.

The probe is a synthetic `MealFoodItem` whose ID is deliberately absent from `mealFoodCatalog`. This preserves fallback regression coverage while proving that every one of the 322 real catalog foods is native. The generic test also verifies the deterministic path `assets/food/pictograms/v1/<probe-id>.webp`.

## UI/UX certification

BEFORE: certified Batch-13 FoodPicker surface, same production surface and viewports 390×844 / 768×1024 / 1280×900.

Goal: expose the final soup family with native artwork while preserving the established IAMINA compact visual language.

Reference: established IAMINA native pictogram language: compact 44–48 px recognition, soft contact shadow, restrained teal accent, no text/logo, no external assets, offline-safe.

AFTER fixture: search query `soupe`.

Retained product proof exists for the same Batch-14 rendering. Final merge still requires exact-head reconstruction/certification after Batch 13 merges.

## Validation gate

Before merge:
- Batch 13 integrated into `main`, then Batch 14 reconstructed on exact current main;
- final 10 + native union exactly equal to the complete catalog ID set;
- pairwise-disjoint batch contract;
- all nine synthetic outside-catalog fallback probes green;
- localized semantics preserved;
- exact-head CI, geometry, P5-5 and Chrome SUCCESS;
- P7 recorded N/A, not green;
- AFTER screenshots inspected at all three viewports;
- explicit visual score recorded.

No Vercel deployment is part of this lot.
