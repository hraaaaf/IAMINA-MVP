# IAMINA Nutrition Data Sources

## Purpose

Nutrition Data v2 may display a nutrition number only when the value is traceable to an explicit source, version and food reference. Unsupported foods and household portions remain loggable, but numeric nutrition fails closed instead of being guessed.

## Source order

1. Morocco-specific composition data when the food/preparation match is defensible.
2. ANSES Ciqual for compatible foods and preparations.
3. USDA FoodData Central Foundation Foods for compatible foods and preparations.

A source ranked earlier does not justify a loose mapping. Food identity, preparation state and edible portion must still match.

## Current curated numeric seed

### Apple — raw, with skin

Source: USDA FoodData Central Foundation Foods, April 2026 release.

IAMINA deliberately stores a carbohydrate interval of **14.1–15.7 g/100 g** rather than a single generic apple value because the curated Foundation Food entries differ by cultivar.

Curated FDC references: `1750339`, `1750340`, `1750341`, `1750342`, `1750343`.

No natural-piece weight is claimed from this seed because the audited Foundation entries did not publish a compatible portion weight.

### Banana — raw

Source: USDA FoodData Central Foundation Foods, April 2026 release.

IAMINA stores **20.1–23.0 g carbohydrate/100 g** across the audited overripe and ripe/slightly-ripe Foundation Food entries. A published peeled-banana portion is represented as **110–115 g**, preserving the source variation rather than manufacturing one exact weight.

Curated FDC references: `1105073`, `1105314`.

## CAL-11 USDA Foundation 2026-04 primary provenance

The Apple and Banana rows above were reconciled to the official USDA Foundation Foods `FoodData_Central_foundation_food_json_2026-04-30.zip`, SHA-256 `186e988ec542e913f51ef62b86a47758e8cdd0d1dc3889e7b055581f3c09c77a`. See [CAL-11 source-row audit](assessments/2026-10-12-v1-01-cal11-official-source-reconciliation.md). The seven historical identifiers were absent from this specific Foundation snapshot; this does not establish their status in every USDA dataset or release.

At **100 g edible apple**, the coded analytical carbohydrate estimate is **14.1–15.7 g**; this is a source-backed range, not a personalized meal amount, dose, treatment target or clinical recommendation. The patient may enter a different actual weight; unknown natural portions must not receive fabricated gram values.

## Explicit non-mappings

- Generic USDA bread is not mapped to Moroccan bread.
- Dry lentil composition is not mapped to an unspecified eaten/cooked lentil entry.
- Moroccan household portions such as msemen, harira bowls and couscous plates remain portion labels without numeric weight until an exact defensible source is curated.

## Patient-facing rules

- No invented glycemic index.
- No fabricated carbohydrate value from a qualitative food category.
- No hidden conversion from household portion to grams.
- Exact values are shown only when exactness is source-backed; otherwise IAMINA shows a range.
- Derived nutrition is recalculated from the versioned catalogue and is not persisted as immutable clinical truth.

## P1-JOURNAL-4 certification anchor

Exact-code visual recertification on product head `f909fac3cc57af81955fdee9bbaee4f87689734c` passed run `31320713710` across the FR/AR desktop, tablet, 390×844 and 360×560 matrix plus real-font Chromium captures. Artifact `9040098902` has digest `sha256:b1b1919c3d329ca13ac77064e0f187dab36ecf4b16ef02ff36be0d30239736ae`. The RTL numeric-range remediation was visually double-checked and the final UX score is **9.3/10**.
