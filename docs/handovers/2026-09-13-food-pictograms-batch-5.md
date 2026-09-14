# IAMINA — Food pictograms Batch 5

Status: CERTIFIED — pending merge

## Goal

Extend native FoodPicker pictogram coverage from 96 to 120 concepts without changing nutrition logic, catalog structure, search behavior or runtime render priority.

Success = exact manifest-derived 24-item Batch 5, native union exactly 120, pairwise disjoint batches, every ID bound to the catalog, long-tail emoji fallback preserved, semantics preserved, exact-head CI/geometry/P5-5/P7/Chrome green on the current main-based branch, and AFTER evidence inspected at 390×844 / 768×1024 / 1280×900.

## Source of truth

`frontend/tool/food_pictogram_manifest.dart` and `frontend/lib/core/data/meal_food_catalog.dart`.

Ordering contract: first 48 launch IDs, then remaining catalog sorted by `MealFoodCategory.index`, then French label using Dart `String.compareTo`, split into 24-item batches.

## Exact Batch 5

`fish_biryani`, `chicken_biryani`, `lamb_biryani`, `falafel`, `fattoush`, `foul_medames`, `kabsa_lamb`, `khabeesa`, `machboos_fish`, `majboos_shrimp`, `machboos_lamb`, `madrooba`, `manakish_cheese`, `manakish_zaatar`, `mandi_lamb`, `margoog`, `moutabal`, `mutabbaq`, `muhammar_rice`, `saleeg`, `saloona`, `samboosa_cheese`, `samboosa_meat`, `shakshuka`.

## UI/UX certification

BEFORE: certified Batch-4 FoodPicker, same production surface and viewports 390×844 / 768×1024 / 1280×900.

Goal: expose newly-native Machboos variants with the already-native Batch-2 chicken Machboos as retained baseline.

Reference: established IAMINA native pictogram language: compact 44–48 px recognition, soft contact shadow, restrained teal accent, no text/logo, no external assets, offline-safe.

AFTER fixture: search query `machboos`.

Manual AFTER inspection on exact product/doc head `1663bc2eadeea1e8689378ab742a7b29a0bbf6c3`:
- 390×844: four Machboos results render cleanly in one column; CTA and consent copy visible; no observed collision, overflow or clipped label.
- 768×1024: same four results render cleanly in one column; no observed collision or overflow.
- 1280×900: clean two-column result grid and full-width photo CTA; no observed collision or overflow.
- Pre-existing horizontal category rail edge clipping remains scroll behavior, not a Batch-5 regression.

Visual score: 9.3/10.

## Verified integration and proof

- Batch 4 merged to `main` as `e68b516277a138e4e2f9d757ef59759f062e0a02`.
- Batch 5 was reconstructed/retargeted onto that exact main base before certification.
- Exact head `1663bc2eadeea1e8689378ab742a7b29a0bbf6c3`:
  - CI #4205 / run `34786382365` — SUCCESS
  - UI geometry #558 / run `34786382362` — SUCCESS
  - P5-5 #118 / run `34786382389` — SUCCESS
  - P7 responsive #172 / run `34786382426` — SUCCESS
  - Chrome #561 / run `34786382368` — SUCCESS
- Chrome artifact `10327026855`, digest `sha256:dd35dbe5db6eb9b0637cda4e33f2d92e59b09b2e62205f0cfe869bf1a72db1a3`.

This closeout documentation commit must itself receive the same exact-head 5-gate certification before merge.

No Vercel deployment is part of this lot.
