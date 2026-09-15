# IAMINA — Food pictograms Batch 12

Status: FINAL CERTIFICATION — rebuilt on merged Batch 11; exact-head gates required before merge

## Goal

Extend native FoodPicker pictogram coverage from 264 to 288 concepts without changing nutrition logic, catalog structure, search behavior or runtime render priority.

Success = exact manifest-derived 24-item Batch 12, native union exactly 288, all twelve batches pairwise disjoint, every ID bound to the catalog, first post-Batch-12 fallback preserved, semantics preserved, exact-head CI/geometry/P5-5/Chrome green, and AFTER evidence inspected at 390×844 / 768×1024 / 1280×900.

P7 responsive Dashboard certification is N/A for this FoodPicker-only lot because that workflow is path-filtered to Dashboard files.

## Source of truth

`frontend/tool/food_pictogram_manifest.dart` + `frontend/lib/core/data/meal_food_catalog.dart`.

Ordering contract: first 48 launch IDs, then remaining catalog sorted by `MealFoodCategory.index`, then French label using Dart `String.compareTo`, split into 24-item batches.

Batch 11 ends at `water`. Batch 12 continues with the twelve remaining non-priority drink concepts, then the first twelve remaining dessert concepts. `cake` is the first item outside Batch 12 and remains the fallback sentinel after Batch 12.

## Exact Batch 12

`coconut_water`, `sparkling_water`, `juice`, `orange_juice`, `apple_juice`, `milkshake`, `protein_shake`, `smoothie`, `soft_drink`, `diet_soft_drink`, `black_tea`, `green_tea`, `baklava`, `basbousa`, `cookie`, `chebakia`, `chocolate`, `dark_chocolate`, `jam`, `gazelle_horns`, `croissant`, `atayef_moroccan`, `ghriyba`, `ice_cream`.

## Integration maintenance

Batch 12 makes `coconut_water` native. Seven inherited fallback checks are therefore migrated to `cake`:
- Batch 6 fallback test;
- Batch 7 fallback test;
- Batch 8 fallback test;
- Batch 9 fallback test;
- Batch 10 fallback test;
- Batch 11 fallback test;
- generic deterministic asset-path/emoji-fallback test.

## Current-main integration

- Batch 11 merged through PR #616 as `3c6e46e3adef55520211f3dbd383d65cabf4de0a`.
- Batch 12 rebuilt content-identically on that exact `main` tree.
- Integration commit before this documentation closeout: `8cde48dfe9c9b151561f54e9ca621feeea10169a`.
- Compare against merged Batch 11: ahead 1, behind 0, exactly 13 expected Batch-12 implementation/docs/fallback-test paths.
- Runtime priority unchanged: certified asset > native painter > emoji fallback.

## UI/UX certification

BEFORE: certified Batch-11 FoodPicker surface, same production surface and viewports 390×844 / 768×1024 / 1280×900.

Goal: expose newly-native chocolate concepts in the same search family while retaining the established IAMINA compact artwork language.

Reference: established IAMINA native pictogram language: compact 44–48 px recognition, soft contact shadow, restrained teal accent, no text/logo, no external assets, offline-safe.

AFTER fixture: search query `chocolat`.

Retained product-stack proof already exists for the same Batch-12 rendering at 390×844 / 768×1024 / 1280×900 with visual score 9.3/10. Final merge still requires exact-head proof on this final branch head.

## Validation gate

Before merge:
- exact 24 + native union 288 + catalog binding + fallback + semantics tests;
- visual contract for twelve fixed disjoint 24-item batches;
- exact-head CI, geometry, P5-5 and Chrome SUCCESS;
- P7 recorded N/A, not green;
- AFTER screenshots inspected at all three viewports;
- explicit visual score recorded;
- PR review/thread/mergeability rechecked.

No Vercel deployment is part of this lot.
