# IAMINA — Food pictograms Batch 4

Status: ACTIVE

## Goal

Extend native FoodPicker pictogram coverage from 72 to 96 concepts without changing nutrition logic, catalog structure, search behavior or runtime render priority.

Success = exact manifest-derived 24-item batch 4, native union exactly 96, pairwise disjoint batches, every ID bound to the catalog, long-tail emoji fallback preserved, semantics preserved, exact-head CI/geometry/E2E/responsive/Chrome green, and AFTER evidence inspected at 390×844 / 768×1024 / 1280×900.

## Source of truth

`frontend/tool/food_pictogram_manifest.dart` on `main@eb588496fc380f1ae0bbabd69ba4d28067a933b1`.

Ordering contract: first 48 launch IDs, then remaining catalog sorted by `MealFoodCategory.index`, then French label using Dart `String.compareTo`, split into 24-item batches.

## Exact Batch 4

`rice`, `basmati_rice`, `brown_rice`, `semolina`, `vermicelli`, `bissara`, `briouat_cheese`, `briouat_meat`, `couscous_tfaya`, `hssoua`, `khlii`, `maakouda`, `mrouzia`, `mechoui`, `pastilla_chicken`, `pastilla_seafood`, `seffa`, `sellou`, `sfenj`, `tajine`, `lamb_prune_tagine`, `tanjia`, `zammita`, `aseeda`.

## UI/UX certification

BEFORE: Batch 3 merged state, same production FoodPicker surface and viewports 390×844 / 768×1024 / 1280×900.

Goal: expose multiple Batch-4 Moroccan pictograms while retaining already-certified Batch-2 tajines in the same result set.

Reference: established IAMINA native pictogram language: compact 44–48 px recognition, soft contact shadow, restrained teal accent, no text/logo, no external assets, offline-safe.

AFTER fixture: search query `tajine`.

Comparison scope: same surface/viewports/layout. Displayed data intentionally changes to expose Batch-4 artwork, so this is not a pixel-for-pixel content comparison.

## Validation gate

Before merge:
- product tests for exact 24 + union 96 + catalog binding + fallback + semantics;
- visual contract test for four fixed disjoint 24-item batches;
- exact-head CI, geometry, P5-5, P7 responsive and Chrome SUCCESS;
- AFTER screenshots inspected at all three viewports;
- explicit visual score recorded.

No Vercel deployment is part of this lot.
