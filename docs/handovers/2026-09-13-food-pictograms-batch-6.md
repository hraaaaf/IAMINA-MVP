# IAMINA — Food pictograms Batch 6

Status: FINAL CERTIFICATION — product proof retained; doc-only closeout head must recertify before merge

## Goal

Extend native FoodPicker pictogram coverage from 120 to 144 concepts without changing nutrition logic, catalog structure, search behavior or runtime render priority.

Success = exact manifest-derived 24-item Batch 6, native union exactly 144, all six batches pairwise disjoint, every ID bound to the catalog, long-tail emoji fallback preserved, semantics preserved, exact-head CI/geometry/P5-5/P7/Chrome green after Batch 5 integration, and AFTER evidence inspected at 390×844 / 768×1024 / 1280×900.

## Source of truth

`frontend/tool/food_pictogram_manifest.dart` + `frontend/lib/core/data/meal_food_catalog.dart`.

Ordering contract: first 48 launch IDs, then remaining catalog sorted by `MealFoodCategory.index`, then French label using Dart `String.compareTo`, split into 24-item batches.

Batch 5 ends at `shakshuka`. Batch 6 consumes the final three non-priority Gulf concepts, all remaining non-priority meat/poultry concepts, then the first nine remaining fish/seafood concepts.

## Exact Batch 6

`shawarma_beef`, `shuwa`, `tabbouleh`, `lamb`, `chicken_breast`, `minced_beef`, `lamb_chops`, `turkey`, `liver`, `kefta`, `merguez`, `roast_chicken`, `sausage`, `beef_steak`, `veal`, `sea_bass`, `squid`, `crab`, `shrimp`, `sea_bream`, `prawns`, `mackerel`, `hake`, `mussels`.

## UI/UX certification

BEFORE: certified Batch-5 FoodPicker surface, same production surface and viewports 390×844 / 768×1024 / 1280×900.

Goal: expose new beef-family Batch-6 pictograms while retaining the already-native Batch-1 beef baseline.

Reference: established IAMINA native pictogram language: compact 44–48 px recognition, soft contact shadow, restrained teal accent, no text/logo, no external assets, offline-safe.

AFTER fixture: search query `bœuf`.

Manual AFTER inspection on exact product head `89d0375a5309ff2cc27d745c403f4db5a93b4f53`:
- 390×844: four beef results render cleanly in one column (`Bœuf`, `Bœuf haché`, `Shawarma bœuf`, `Steak de bœuf`); CTA and consent copy remain visible; no observed collision, overflow or clipped label.
- 768×1024: same four results render cleanly in one column; no observed collision or overflow.
- 1280×900: clean two-column result grid and full-width photo CTA; no observed collision or overflow.
- Pre-existing horizontal category rail edge clipping remains scroll behavior, not a Batch-6 regression.

Visual score: 9.3/10.

## Verified integration and proof

- Batch 5 merged to `main` as `9e7b80feb9743e2a4db297f38b78c06fbfcd83a5`.
- Batch 6 was reconstructed/retargeted onto that exact main base before certification.
- Exact product head `89d0375a5309ff2cc27d745c403f4db5a93b4f53` has the complete five-gate set green:
  - UI geometry run `34823062314` — SUCCESS
  - P5-5 End-to-End Pilot Rehearsal run `34823062390` — SUCCESS
  - P7 responsive Dashboard certification run `34823062371` — SUCCESS
  - CI run `34823062317` — SUCCESS
  - UI browser screenshot certification run `34823062408` — SUCCESS
- Chrome artifact `10338634459`, digest `sha256:af0bd5aca6fc5388f804083beb32459a2e16571a22061fe74a020acd07f9daea`.
- Local artifact ZIP SHA-256 independently matches the GitHub digest.
- AFTER files inspected at their exact native dimensions: 390×844, 768×1024, 1280×900.
- PR #606 reviews: 0; unresolved review threads: 0.

This documentation-only closeout commit changes no product code. It must still receive the same exact-head five-gate set before PR #606 merges; final run IDs can be retained in the PR metadata without another source commit.

No Vercel deployment is part of this lot.
