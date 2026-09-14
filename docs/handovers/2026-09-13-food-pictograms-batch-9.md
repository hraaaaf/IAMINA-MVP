# IAMINA — Food pictograms Batch 9

Status: FINAL CERTIFICATION — exact-main rebuild complete; exact-head gates pending

## Goal

Extend native FoodPicker pictogram coverage from 192 to 216 concepts without changing nutrition logic, catalog structure, search behavior or runtime render priority.

Success = exact manifest-derived 24-item Batch 9, native union exactly 216, all nine batches pairwise disjoint, every ID bound to the catalog, first post-Batch-9 long-tail fallback preserved, semantics preserved, exact-head CI/geometry/P5-5/Chrome green, and AFTER evidence inspected at 390×844 / 768×1024 / 1280×900. P7 responsive is N/A for this FoodPicker-only diff because its workflow is Dashboard-path-filtered.

## Source of truth

`frontend/tool/food_pictogram_manifest.dart` + `frontend/lib/core/data/meal_food_catalog.dart`.

Ordering contract: first 48 launch IDs, then remaining catalog sorted by `MealFoodCategory.index`, then French label using Dart `String.compareTo`, split into 24-item batches.

Batch 8 ends at `green_beans`. Batch 9 continues with the remaining ten non-priority vegetable concepts, then the first fourteen remaining fruit concepts. `guava` is the first item outside Batch 9 and is the current fallback sentinel.

## Exact Batch 9

`lettuce`, `vegetables`, `mint`, `turnip`, `onion`, `sweet_potato`, `parsley`, `bell_pepper`, `salad`, `spinach`, `apricot`, `dried_apricots`, `pineapple`, `avocado`, `cherry`, `lemon`, `clementine`, `khalas_dates`, `medjool_dates`, `sukkari_dates`, `fig`, `dried_figs`, `strawberry`, `raspberry`.

## UI/UX certification

BEFORE: certified Batch-8 FoodPicker surface, same production surface and viewports 390×844 / 768×1024 / 1280×900.

Goal: expose multiple newly-native date varieties alongside retained earlier date artwork.

Reference: established IAMINA native pictogram language: compact 44–48 px recognition, soft contact shadow, restrained teal accent, no text/logo, no external assets, offline-safe.

AFTER fixture: search query `datte`.

Manual AFTER inspection on product head `3f5f070834ecbf1f98b2815ce84f355331560b53`:
- 390×844: date family clean in one column, including retained `Dattes` / `Dattes Ajwa` and newly-native `Dattes Khalas`, `Dattes Medjool`, `Dattes Sukkari`; `Sirop de dattes` remains visually distinct; no observed collision or overflow.
- 768×1024: same result family clean in one column; CTA and consent copy visible; no observed collision or overflow.
- 1280×900: clean two-column result grid; no observed collision or overflow.
- Pre-existing horizontal category rail edge clipping remains scroll behavior, not a Batch-9 regression.

Visual score: 9.3/10.

## Verified integration and proof

- Batch 8 merged in PR #613; subsequent PR #626 changed auth documentation only.
- Batch 9 was rebuilt directly on exact `main@f89b3efd215fee6a50bc2546092cc32eb8791e91`.
- Diff against that main is exactly nine files: six canonical Batch-9 files plus three inherited fallback-test updates.
- The three inherited sentinels moved from `lettuce` to `guava` because `lettuce` becomes native in Batch 9; no product logic changed in those test-only updates.
- Product visual proof retained from `3f5f070834ecbf1f98b2815ce84f355331560b53`:
  - UI geometry run `34823559110` — SUCCESS
  - UI browser screenshot certification run `34823559115` — SUCCESS
  - Chrome artifact `10340355026`, digest `sha256:7e8cff48ecf4ff29a53e862fa5c7bbbc6a03cbaabce6b36e9e2982deb3ddda9d`.
- Local artifact ZIP SHA-256 independently matched the GitHub digest.
- AFTER files inspected at exact native dimensions 390×844, 768×1024, 1280×900.
- Batch-9 contract: exact 24 IDs, native union 216, pairwise disjoint batches, catalog binding, localized native semantics, and post-Batch-9 fallback preserved.

This documentation closeout changes no product code. The exact HEAD created by this closeout must receive all applicable gates before PR #614 merges. Final run IDs may be retained in PR metadata without another source commit.

No Vercel deployment is part of this lot.
