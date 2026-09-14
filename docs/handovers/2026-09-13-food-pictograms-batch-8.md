# IAMINA — Food pictograms Batch 8

Status: FINAL CERTIFICATION — exact-main rebuild completed; exact-head gates required before merge

## Goal

Extend native FoodPicker pictogram coverage from 168 to 192 concepts without changing nutrition logic, catalog structure, search behavior or runtime render priority.

Success = exact manifest-derived 24-item Batch 8, native union exactly 192, all eight batches pairwise disjoint, every ID bound to the catalog, first post-Batch-8 long-tail fallback preserved, semantics preserved, applicable exact-head CI/geometry/P5-5/Chrome green after Batch 7 integration, and AFTER evidence inspected at 390×844 / 768×1024 / 1280×900.

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

- Batch 7 merged to `main` as `e8b2bc5b827b58a8a866cade8fde3c6963896261`.
- The 21 commits that reached `main` around the Batch-7 merge were compared against the Batch-7 head; they touch backend auth-abuse / `docs/TECHDEBT.md` only and do not touch FoodPicker files.
- Batch 8 was rebuilt from the exact tree of `main@e8b2bc5b827b58a8a866cade8fde3c6963896261` by applying only its six canonical Batch-8 files.
- Rebuilt product head before this documentation closeout: `b13ea8f336f7796fa5ae3b2787bfe570d51b5b15`.
- Compare against exact main: 1 commit ahead, 0 behind, exactly six Batch-8 files.
- Product visual proof retained from `991b26c1d51ea54dcb861cf24e6ce9febc4a2c0b`:
  - UI geometry run `34823395910` — SUCCESS
  - UI browser screenshot certification run `34823395929` — SUCCESS
  - Chrome artifact `10339199771`, digest `sha256:dfb7dfdd8db07482a40169e6c44691eb5897a6579010c86ff9852b26b229a9a2`.
- Local artifact ZIP SHA-256 independently matched the GitHub digest.
- AFTER files were inspected at their exact native dimensions: 390×844, 768×1024, 1280×900.
- Batch-8 contract remains: exact 24 IDs, native union 192, pairwise disjoint batches, catalog binding, localized native semantics, and `lettuce` fallback preserved.
- P7 responsive Dashboard certification is not applicable to this FoodPicker-only diff: `.github/workflows/p7-responsive-cert.yml` is path-filtered to Dashboard files.

This documentation-only closeout commit changes no product code. The resulting exact HEAD must receive all applicable gates — CI, geometry, P5-5 and Chrome — before PR #613 merges. Final run IDs can be retained in PR metadata without another source commit.

No Vercel deployment is part of this lot.
