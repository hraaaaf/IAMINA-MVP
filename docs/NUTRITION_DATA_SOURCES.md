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

IAMINA deliberately stores a carbohydrate interval of **14.2–15.7 g/100 g** rather than a single generic apple value because the curated Foundation Food entries differ by cultivar.

Curated FDC references: `1105664`, `1105547`, `1105781`, `1105430`, `1105897`.

No natural-piece weight is claimed from this seed because the audited Foundation entries did not publish a compatible portion weight.

### Banana — raw

Source: USDA FoodData Central Foundation Foods, April 2026 release.

IAMINA stores **20.1–23.0 g carbohydrate/100 g** across the audited overripe and ripe/slightly-ripe Foundation Food entries. A published peeled-banana portion is represented as **110–115 g**, preserving the source variation rather than manufacturing one exact weight.

Curated FDC references: `790774`, `790991`.

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
