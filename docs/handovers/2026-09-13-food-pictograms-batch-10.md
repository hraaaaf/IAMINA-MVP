# IAMINA — Food pictograms Batch 10

Status: FINAL CERTIFICATION — product proof retained; exact-head gates required before merge

## Goal

Extend native FoodPicker pictogram coverage from 216 to 240 concepts without changing nutrition logic, catalog structure, search behavior or runtime render priority.

Success = exact manifest-derived 24-item Batch 10, native union exactly 240, all ten batches pairwise disjoint, every ID bound to the catalog, first post-Batch-10 long-tail fallback preserved, semantics preserved, exact-head CI/geometry/P5-5/P7/Chrome green after Batch 9 integration, and AFTER evidence inspected at 390×844 / 768×1024 / 1280×900.

## Source of truth

`frontend/tool/food_pictogram_manifest.dart` + `frontend/lib/core/data/meal_food_catalog.dart`.

Ordering contract: first 48 launch IDs, then remaining catalog sorted by `MealFoodCategory.index`, then French label using Dart `String.compareTo`, split into 24-item batches.

Batch 9 ends at `raspberry`. Batch 10 continues with the remaining twenty non-priority fruit concepts, then the first four nut/seed concepts. `flax_seeds` is the first item outside Batch 10 and remains the fallback sentinel.

## Exact Batch 10

`guava`, `pomegranate`, `kiwi`, `mandarin`, `mango`, `melon`, `blueberry`, `nectarine`, `coconut`, `orange_cinnamon`, `grapefruit`, `papaya`, `watermelon`, `pear`, `plum`, `prunes`, `peach`, `grapes`, `raisins`, `fruit_salad`, `almonds`, `peanut_butter`, `peanuts`, `chia_seeds`.

## UI/UX certification

BEFORE: certified Batch-9 FoodPicker surface, same production surface and viewports 390×844 / 768×1024 / 1280×900.

Goal: expose newly-native grape and raisin artwork in the same search family.

Reference: established IAMINA native pictogram language: compact 44–48 px recognition, soft contact shadow, restrained teal accent, no text/logo, no external assets, offline-safe.

AFTER fixture: search query `raisin`.

Manual AFTER inspection on product head `5431002e33bb13ccd8942f2c76c331a0185a3648`:
- 390×844: `Raisin` and `Raisins secs` render cleanly in one column; CTA and consent copy remain visible; no observed collision, overflow or clipped label.
- 768×1024: same result pair remains clean in one column; no observed collision or overflow.
- 1280×900: clean two-column result grid; no observed collision or overflow.
- Pre-existing horizontal category rail edge clipping remains scroll behavior, not a Batch-10 regression.

Visual score: 9.3/10.

## Verified integration and proof

- Batch 10 was aligned onto final Batch-9 head `37891821c59fb16f72c8458b98471c535839627e` through merge commit `7e24107b180a20bd545714ff10ee4e6e4e4d8b1f`.
- The merge is content-neutral for Batch 10: its tree is unchanged from visually inspected product head `5431002e33bb13ccd8942f2c76c331a0185a3648`; only ancestry was synchronized.
- Product visual proof on `5431002e33bb13ccd8942f2c76c331a0185a3648`:
  - UI geometry run `34823673720` — SUCCESS
  - UI browser screenshot certification run `34823673739` — SUCCESS
  - Chrome artifact `10339900559`, digest `sha256:c0e897d8cfcdd8979c758d553188fcf0ed108c67c772f8f3870b56a4925d698f`.
- Local artifact ZIP SHA-256 independently matches the GitHub digest.
- AFTER files inspected at their exact native dimensions: 390×844, 768×1024, 1280×900.
- Batch-10 contract remains: exact 24 IDs, native union 240, pairwise disjoint batches, catalog binding, localized native semantics, and first post-Batch-10 fallback preserved.

This documentation-only closeout commit changes no product code. Batch 10 must still be retargeted to exact `main` after Batch 9 merges and the same exact HEAD must receive CI, geometry, P5-5, P7 responsive and Chrome SUCCESS before PR #615 merges. Final run IDs can be retained in PR metadata without another source commit.

No Vercel deployment is part of this lot.
