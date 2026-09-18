# FoodPicker B25 — Saudi depth

## Goal
Append a small, evidence-backed Saudi batch after certified B24 without disturbing the 374-item prefix.

## Baseline / target
- baseline: 374 concepts
- target: 377 concepts
- branch: `feat/foodpicker-b25-saudi-depth`

## Accepted concepts
1. `saudi_jareesh` — FR: Jareesh saoudien — EN: Saudi jareesh — AR: الجريش السعودي
2. `saudi_saleeg` — FR: Saleeg saoudien — EN: Saudi saleeg — AR: السليق السعودي
3. `saudi_marqooq` — FR: Marqooq saoudien — EN: Saudi marqooq — AR: المرقوق السعودي

All three are `gulfDish` / `gulf` and use native B25 painters.

## Provenance evidence
### Jareesh
- Saudipedia, Jareesh: https://saudipedia.com/en/jareesh — identifies Jareesh as a major traditional Saudi dish and records its 2023 adoption by the Culinary Arts Commission as the Kingdom's national dish; cites SPA and the Culinary Arts Commission.
- Arab News / SPA reporting, Culinary caravan: https://www.arabnews.com/saudi-arabia/culinary-caravan-is-a-chance-to-savor-saudi-arabias-food-heritage-2494696 — reports the Culinary Arts Commission's National and Regional Dishes Narratives initiative and Jareesh as a national culinary treasure.

### Saleeg
- Saudipedia, List of Regional Dishes: https://saudipedia.com/en/list-of-regional-dishes-in-the-kingdom — records Saleeg as the Culinary Arts Commission-selected regional dish of Makkah Province; source: SPA.
- Saudipedia, Five Saudi Rice Dishes: https://saudipedia.com/en/list-of-five-saudi-dishes-made-with-rice — documents Saleeg preparation in Saudi cuisine; sources include SPA and Ministry of Culture.

### Marqooq
- Saudipedia, Traditional Food in Riyadh Province: https://saudipedia.com/en/traditional-food-in-riyadh-province — records Marqooq as Riyadh Province's designated regional dish; sources include SPA and Culinary Arts Commission.
- Arab News / SPA reporting, Culinary caravan: https://www.arabnews.com/saudi-arabia/culinary-caravan-is-a-chance-to-savor-saudi-arabias-food-heritage-2494696 — independently reports Marqooq as the official Riyadh regional selection.

## Rejected / deferred
No ambiguous-origin candidate was promoted merely to increase batch size. Existing Gulf-core IDs and obvious synonyms were excluded before implementation.

## UI proof contract
BEFORE: B24 fixture `Amlou marocain` at 390x844, 768x1024, 1280x900.
Goal: expose the first B25 native pictogram without geometry regression.
AFTER fixture: `Jareesh saoudien` at the same three viewports.

## Required gates
- CI
- P5-5 End-to-End Pilot Rehearsal
- UI geometry golden audit
- UI browser screenshot certification
- exact-head artifact SHA256 verification and manual inspection of all three FoodPicker captures

## Merge / deployment
No automatic merge under the canonical pipeline contract. Human approval is required after visual proof. No Vercel deployment.
