# FoodPicker B32 — Sudan core

## Goal
Add a small, culturally verified Sudan core batch after certified B31, preserving the 395-item prefix and existing order.

## Catalog
- before: 395
- target: 398
- `sudanese_kisra` — Kisra soudanaise / Sudanese kisra / كسرة سودانية
- `sudanese_aseeda` — Aseeda soudanaise / Sudanese aseeda / عصيدة سودانية
- `sudanese_gurraasa` — Gurraasa soudanaise / Sudanese gurraasa / قراصة سودانية

## Provenance evidence
All three are independently supported by two official Sudanese diplomatic sources:
- Embassy of Sudan, Washington — Culture/Food: https://sudanembassy.org/us-sudan-relations/ — identifies Kisra as the Sudanese staple, Aseeda as wheat/corn porridge eaten with stews, and Gourrassa as a northern Sudan wheat main dish.
- Embassy of the Republic of Sudan, The Hague — Sudanese Cuisine: https://www.sudanembassy.nl/sudanese-cuisine/ — independently describes Kissra, Asseeda and Gourrassa with the same Sudanese culinary roles.
Supporting culinary reference:
- Visit Sudan cuisine/explore: https://visitsudan.org/en/cuisine and https://visitsudan.org/en/explore — describes Kisra, Aseeda and Gurraasa and their preparation/context.

## Duplicate gate
Default-branch code search for `kisra aseeda gurraasa gourrassa` returned no existing concept. Egyptian ful was deliberately not duplicated.

## Category decision
All three are flour/cereal staples and use `MealFoodCategory.breadGrain`: kisra is fermented sorghum flatbread; aseeda is a thick wheat/sorghum porridge; gurraasa is a thick wheat flatbread.

## UI proof contract
BEFORE: B31 `Kochari égyptien`.
Goal: expose a native Sudanese staple pictogram without geometry/category regression.
AFTER fixture: `Kisra soudanaise`.
Required viewports: 390x844, 768x1024, 1280x900.

## Required gates
CI; P5-5 End-to-End Pilot Rehearsal; UI geometry golden audit; UI browser screenshot certification; exact-head artifact SHA256 + screenshot inspection.

## Merge / deployment
Never auto-merge. Human approval required after certified principal screenshot. No Vercel deployment.
