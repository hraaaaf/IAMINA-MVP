# FoodPicker B25 — Saudi depth

## Status
CLOSED / MERGED / POST-MERGE VERIFIED.

## Goal
Append a small, evidence-backed Saudi batch after certified B24 without disturbing the 374-item prefix.

## Baseline / target
- baseline: 374 concepts
- target: 377 concepts
- branch: `feat/foodpicker-b25-saudi-depth`
- PR: #686
- candidate HEAD: `0da2252cd78cbc04a96912898d9525db46232faa`
- merge/main result: `5da6ddf3a90d21ae5b2bb6949eab16b6b7d5130b`

## Accepted concepts
1. `saudi_jareesh` — FR: Jareesh saoudien — EN: Saudi jareesh — AR: الجريش السعودي
2. `saudi_saleeg` — FR: Saleeg saoudien — EN: Saudi saleeg — AR: السليق السعودي
3. `saudi_marqooq` — FR: Marqooq saoudien — EN: Saudi marqooq — AR: المرقوق السعودي

All three are `gulfDish` / `gulf` and use native B25 painters.

## Provenance evidence
### Jareesh
- Saudipedia, Jareesh: https://saudipedia.com/en/jareesh
- Arab News / SPA reporting: https://www.arabnews.com/saudi-arabia/culinary-caravan-is-a-chance-to-savor-saudi-arabias-food-heritage-2494696

### Saleeg
- Saudipedia, List of Regional Dishes: https://saudipedia.com/en/list-of-regional-dishes-in-the-kingdom
- Saudipedia, Five Saudi Rice Dishes: https://saudipedia.com/en/list-of-five-saudi-dishes-made-with-rice

### Marqooq
- Saudipedia, Traditional Food in Riyadh Province: https://saudipedia.com/en/traditional-food-in-riyadh-province
- Arab News / SPA reporting: https://www.arabnews.com/saudi-arabia/culinary-caravan-is-a-chance-to-savor-saudi-arabias-food-heritage-2494696

## UI proof
BEFORE: B24 fixture `Amlou marocain`.
AFTER: B25 fixture `Jareesh saoudien` at 390x844, 768x1024, 1280x900.
Exact-head browser artifact: `10543858023`.
SHA256: `b6d2b65586849bc30daee8654c4fb7da88e393d0541fa9380ae8b72f8117a28f`.
Manual inspection: no clipping, overflow or collision observed; native Jareesh pictogram and Gulf category state were correct.

## Exact-head gates
- CI `35337760051`: SUCCESS
- P5-5 `35337760130`: SUCCESS
- UI geometry `35337760036`: SUCCESS
- UI browser screenshot certification `35337760120`: SUCCESS
- CGM onboarding browser certification `35337760103`: SUCCESS

## Post-merge closeout
`main` reached merge result `5da6ddf3a90d21ae5b2bb6949eab16b6b7d5130b`. Push workflows on that exact SHA: browser `35353533012` SUCCESS; P5-5 `35353533041` SUCCESS; geometry `35353532917` SUCCESS; CGM browser `35353533042` SUCCESS. CI `35353533011` attempt 1 was cancelled during Flutter tests without a functional failure; attempt 2 completed SUCCESS on the same exact main SHA.

B25 is therefore closed and the next FoodPicker cycle may start from the then-current `main` subject to the canonical pipeline candidate/source gates.

## Deployment
No Vercel deployment was performed or authorized.
