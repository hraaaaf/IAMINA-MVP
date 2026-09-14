# IAMINA — Food pictograms Batch 8

Status: FINAL CERTIFICATION — product proof retained; exact-head gates required before merge

## Goal

Extend native FoodPicker pictogram coverage from 168 to 192 concepts without changing nutrition logic, catalog structure, search behavior or runtime render priority.

Success = exact manifest-derived 24-item Batch 8, native union exactly 192, all eight batches pairwise disjoint, every ID bound to the catalog, first post-Batch-8 long-tail fallback preserved, semantics preserved, exact-head CI/geometry/P5-5/P7/Chrome green after Batch 7 integration, and AFTER evidence inspected at 390×844 / 768×1024 / 1280×900.

## Source of truth

`frontend/tool/food_pictogram_manifest.dart` + `frontend/lib/core/data/meal_food_catalog.dart`.

Ordering contract: first 48 launch IDs, then remaining catalog sorted by `MealFoodCategory.index`, then French label using Dart `String.compareTo`, split into 24-item batches.

Batch 7 ends at `yogurt`. Batch 8 continues with the final non-priority dairy concept, the six remaining non-priority legume concepts, then the first 17 remaining vegetable concepts. `lettuce` is the first item outside Batch 8 and remains the fallback sentinel.

## Exact Batch 8

`greek_yogurt`, `fava_beans`, `white_beans`, `red_beans`, `green_peas`, `split_peas`, `soybeans`, `garlic`, `artichoke`, `eggplant`, `beetroot`, `broccoli`, `carrot`, `mushroom`, `cabbage`, `cauliflower`, `preserved_lemon`, `cucumber`, `coriander`, `pumpkin`, `zucchini`, `celery`, `okra`, `green_beans`.

## UI/UX certification

BEFORE: certified Batch-7 FoodPicker surface, same production surface and viewports 390×844 / 768×1024 / 1280×900.

Goal: expose multiple newly-native bean concepts in one search while preserving the same compact IAMINA visual language.

Reference: established IAMINA native pictogram language: compact 44–48 px recognition, soft contact shadow, restrained teal accent, no text/logo, no external assets, offline-safe.

AFTER fixture: search query `haricot`.

Manual AFTER inspection on product head `991b26c1d51ea54dcb861cf24e6ce9febc4a2c0b`:
- 390×844: `Haricots blancs`, `Haricots rouges` and `Haricots verts` render cleanly in one column; CTA and consent remain visible; no observed collision or overflow.
- 768×1024: same three results remain clean in one column; no observed collision or overflow.
- 1280×900: clean two-column result grid with the final result on the next row; no observed collision or overflow.
- Pre-existing horizontal category rail edge clipping remains scroll behavior and is not introduced by Batch 8.

Visual score: 9.3/10.

## Verified integration and proof

- Batch 8 was aligned onto final Batch-7 head `1d71e85f1a2bfc7e67965122906b1244aedf6d01` through merge commit `accff376d015a30fe485ed694261ef28ed5f632b`.
- The merge is content-neutral for Batch 8: its tree is unchanged from visually inspected product head `991b26c1d51ea54dcb861cf24e6ce9febc4a2c0b`; only ancestry was synchronized.
- Product visual proof on `991b26c1d51ea54dcb861cf24e6ce9febc4a2c0b`:
  - UI geometry run `34823395910` — SUCCESS
  - UI browser screenshot certification run `34823395929` — SUCCESS
  - Chrome artifact `10339199771`, digest `sha256:dfb7dfdd8db07482a40169e6c44691eb5897a6579010c86ff9852b26b229a9a2`.
- Local artifact ZIP SHA-256 independently matches the GitHub digest.
- AFTER files inspected at their exact native dimensions: 390×844, 768×1024, 1280×900.
- Batch-8 contract remains: exact 24 IDs, native union 192, pairwise disjoint batches, catalog binding, localized native semantics, and the first post-Batch-8 fallback preserved.

This documentation-only closeout commit changes no product code. Batch 8 must still be retargeted to exact `main` after Batch 7 merges and the same exact HEAD must receive CI, geometry, P5-5, P7 responsive and Chrome SUCCESS before PR #613 merges. Final run IDs can be retained in PR metadata without another source commit.

No Vercel deployment is part of this lot.
