# IAMINA — Food pictograms Batch 7

Status: FINAL CERTIFICATION — product proof retained; doc-only closeout head must recertify before merge

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

BEFORE: certified Batch-6 FoodPicker surface, same production surface and viewports 390×844 / 768×1024 / 1280×900.

Goal: expose several newly-native milk concepts while retaining the Batch-1 `milk` baseline in the same search result family.

Reference: established IAMINA native pictogram language: compact 44–48 px recognition, soft contact shadow, restrained teal accent, no text/logo, no external assets, offline-safe.

AFTER fixture: search query `lait`.

Manual AFTER inspection on product head `0eafc27ad92632f7444663d465330931bd843c95`:
- 390×844: `Lait`, `Lait de chamelle`, `Lait demi-écrémé`, `Lait entier`, `Lait écrémé` render cleanly with retained matching results; no observed collision or horizontal overflow in result rows.
- 768×1024: same result family remains clean in one column; photo CTA and consent text visible; no observed collision or overflow.
- 1280×900: clean two-column result grid; full-width CTA below; no observed collision or overflow.
- Pre-existing category rail edge clipping remains horizontal scroll behavior and is not introduced by Batch 7.

Visual score: 9.3/10.

## Verified integration and proof

- Batch 6 merged to `main` as `d2c70122a0521c1280dcab2936bbb1d6d1c104d5`.
- Batch 7 was resynced onto that exact main and retargeted to `main`.
- Main-based product head before this documentation closeout: `bad533adaf0358e70e8d4bf9b661062203416854`; compare against `main` shows exactly the six Batch-7 files and 0 commits behind.
- Product code at `bad533adaf0358e70e8d4bf9b661062203416854` is byte-equivalent to the visually inspected `0eafc27ad92632f7444663d465330931bd843c95`; the only intervening file change is the inherited Batch-6 handover synchronization.
- Product visual proof on `0eafc27ad92632f7444663d465330931bd843c95`:
  - UI geometry run `34823315478` — SUCCESS
  - UI browser screenshot certification run `34823315476` — SUCCESS
  - Chrome artifact `10339521146`, digest `sha256:e7624dc8ee5891ca571e0c62e3222003eaf451636db8b1b6efe383f7c5f62433`.
- Local artifact ZIP SHA-256 independently matches the GitHub digest.
- AFTER files inspected at their exact native dimensions: 390×844, 768×1024, 1280×900.
- Batch-7 tests assert the exact 24 IDs, pairwise disjoint union of 168, catalog binding, localized native semantics, and `greek_yogurt` emoji fallback.
- PR #607 reviews: 0; unresolved review threads: 0 at product-proof checkpoint.

This documentation-only closeout commit changes no product code. It must receive the complete exact-head five-gate set — CI, geometry, P5-5, P7 responsive and Chrome — before PR #607 merges. Final run IDs can be retained in PR metadata without another source commit.

No Vercel deployment is part of this lot.
