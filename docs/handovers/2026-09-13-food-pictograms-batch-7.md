# IAMINA — Food pictograms Batch 7

Status: PRE-CERTIFIED VISUAL — pending Batch 6 merge + exact-main final gate

## Goal

Extend native FoodPicker pictogram coverage from 144 to 168 concepts without changing nutrition logic, catalog structure, search behavior or runtime render priority.

Success = exact manifest-derived 24-item Batch 7, native union exactly 168, all seven batches pairwise disjoint, every ID bound to the catalog, first post-Batch-7 long-tail fallback preserved, semantics preserved, exact-head CI/geometry/P5-5/P7/Chrome green after Batch 6 integration, and AFTER evidence inspected at 390×844 / 768×1024 / 1280×900.

## Source of truth

`frontend/tool/food_pictogram_manifest.dart` + `frontend/lib/core/data/meal_food_catalog.dart`.

Ordering contract: first 48 launch IDs, then remaining catalog sorted by `MealFoodCategory.index`, then French label using Dart `String.compareTo`, split into 24-item batches.

Batch 6 ends at `mussels`. Batch 7 continues with the final three remaining fish/seafood concepts, all non-priority egg concepts, then the first 18 non-priority dairy concepts. `greek_yogurt` is the first item outside Batch 7 and remains the fallback sentinel.

## Exact Batch 7

`fish`, `octopus`, `tuna`, `omelette`, `fried_egg`, `boiled_egg`, `butter`, `cream`, `feta`, `cheese`, `processed_cheese`, `fresh_cheese`, `cream_cheese`, `halloumi`, `laban`, `labneh`, `camel_milk`, `semi_skimmed_milk`, `whole_milk`, `skimmed_milk`, `mozzarella`, `qishta`, `raib`, `yogurt`.

## UI/UX certification

BEFORE: Batch-6 FoodPicker surface, same production surface and viewports 390×844 / 768×1024 / 1280×900.

Goal: expose several newly-native milk concepts while retaining the Batch-1 `milk` baseline in the same search result family.

Reference: established IAMINA native pictogram language: compact 44–48 px recognition, soft contact shadow, restrained teal accent, no text/logo, no external assets, offline-safe.

AFTER fixture: search query `lait`.

Early stacked AFTER inspection on head `2bd7ee584bf510a40a5eb4f6ea2f65a1b2e69c91`:
- 390×844: `Lait`, `Lait de chamelle`, `Lait demi-écrémé`, `Lait entier`, `Lait écrémé` render cleanly with retained non-Batch-7 matching results; no observed collision or horizontal overflow in result rows.
- 768×1024: same result family remains clean in one column; photo CTA and consent text visible; no observed collision or overflow.
- 1280×900: clean two-column result grid; full-width CTA below; no observed collision or overflow.
- Pre-existing category rail edge clipping remains horizontal scroll behavior and is not introduced by Batch 7.

Early visual score: 9.3/10. Final score must be reconfirmed on the exact main-based head after Batch 6 merges.

## Early stacked proof

- UI geometry #582 / run `34819599062` — SUCCESS
- Chrome #585 / run `34819599132` — SUCCESS
- Chrome artifact `10337524242`, digest `sha256:bc75d517d24b147fded751d4186bddbd9eae76b99e0f25d8205c30828e82e1a2`.
- Local artifact SHA-256 independently matches the GitHub digest.

## Final validation gate

Before merge:
- Batch 6 integrated into `main`, then Batch 7 resynced onto exact current main;
- exact 24 + native union 168 + catalog binding + fallback + semantics tests;
- visual contract for seven fixed disjoint 24-item batches;
- exact-head CI, geometry, P5-5, P7 responsive and Chrome SUCCESS;
- final AFTER screenshots inspected at all three viewports;
- final visual score recorded.

No Vercel deployment is part of this lot.
