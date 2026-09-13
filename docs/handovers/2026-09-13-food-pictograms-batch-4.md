# IAMINA — Food pictograms Batch 4

Status: READY TO MERGE once final docs exact-head recertification is green

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

### Product/test exact-head proof

Exact head: `77cf113193f80bb43080131c049819dd62d86680`

- CI #34770717394 — SUCCESS
- UI geometry golden audit #34770717314 — SUCCESS
- P5-5 End-to-End Pilot Rehearsal #34770717308 — SUCCESS
- P7 responsive Dashboard certification #34770717413 — SUCCESS
- UI browser screenshot certification #34770717323 — SUCCESS

Chrome artifact:
- ID `10321952223`
- name `iamina-ui-browser-cert-multi-viewport`
- digest `sha256:f1d391fa05312853440ec8c8585c7a7d1845617e8c6480d28292b242c5f312ed`

### AFTER inspection

- 390×844: clean one-column picker; native `Tajine`, `Tajine agneau aux pruneaux`, retained `Tajine kefta` and `Tajine poulet citron confit`; no observed collision, overflow or clipped label.
- 768×1024: same four results in a clean one-column layout; photo CTA and consent note visible; no observed collision or overflow.
- 1280×900: clean two-column result grid with full-width photo CTA below; no observed collision or overflow.
- The horizontal category rail keeps its pre-existing scroll/edge clipping behavior; Batch 4 did not introduce a new layout regression there.

Manual visual score: **9.3/10**.

Basis: stable responsive structure at all three target viewports, coherent native pictogram language, immediate small-size recognition and no observed layout regression. Remaining visual debt is limited to the pre-existing horizontal category-rail edge clipping/scroll behavior.

## Validation gate

Product/test head satisfies the functional and visual proof gate above. This documentation closeout commit must itself be exact-head recertified before merge; no merge is claimed until that proof is green.

No Vercel deployment is part of this lot.
