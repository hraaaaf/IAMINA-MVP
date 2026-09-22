# FoodPicker B33 — Palestine core

## Goal
Add a small, culturally verified Palestine core batch after certified B32, preserving the 398-item prefix and existing order.

## Catalog
- before: 398
- target: 401
- `palestinian_musakhan` — Musakhan palestinien / Palestinian musakhan / مسخن فلسطيني
- `palestinian_qidreh` — Qidreh d’Hébron / Hebron qidreh / قدرة خليلية
- `jerusalem_kaak` — Ka’ak de Jérusalem / Jerusalem ka’ak / كعك القدس

## Provenance evidence
### Musakhan
- Travel Palestine, official tourism site cuisine archive: https://travelpalestine.wordpress.com/cuisine/ — describes Musakhan as a common main dish of the northern West Bank, with taboon bread, onions, sumac and roast chicken.
- Palestinian Heritage Trail: https://paltrails.ps/palestinian-cuisine — independently identifies Musakhan as a festive Palestinian dish and northern-region specialty associated with olive harvest.

### Qidreh
- Travel Palestine cuisine index: https://www.travelpalestine.ps/en/Category/2/Cuisine — identifies Qidreh as Hebron’s traditional dish, rice with lamb/chicken, garlic, broth and chickpeas.
- Arab News regional Ramadan feature: https://www.arabnews.com/middle-east/during-ramadan-traditional-regional-dishes-shine-in-palestine-2057861 — independently identifies Qidreh as a traditional Palestinian dish from Hebron and describes its rice/meat/chickpea preparation.

### Ka’ak Al-Quds
- UNESCO Intangible Cultural Heritage 2026 nomination video: https://ich.unesco.org/en/video/83700 — records the State of Palestine nomination “Ka’ak Al-Quds, Jerusalem sesame bread”. Nomination status is recorded as nomination, not inscription.
- Travel Palestine bread reference: https://www.travelpalestine.ps/en/Article/8/Bread — identifies Qa'ek as sesame-coated bread particularly renowned in Jerusalem.

## Duplicate / ambiguity gate
Default-branch code search for `musakhan qidreh kaak quds Jerusalem sesame bread` returned no existing concept. Maqluba was researched but rejected for this lot because its provenance is broadly Levantine / multi-country and therefore less clean for a provenance-focused Palestine batch.

## Category decision
- Musakhan → `MealFoodCategory.meatPoultry`: independently selectable chicken-centered main dish.
- Qidreh → `MealFoodCategory.breadGrain`: rice-based main dish.
- Ka’ak Al-Quds → `MealFoodCategory.breadGrain`: sesame bread.

## UI proof contract
BEFORE: B32 `Kisra soudanaise`.
Goal: expose a native Palestinian core pictogram without geometry/category regression.
AFTER fixture: `Musakhan palestinien`.
Required viewports: 390x844, 768x1024, 1280x900.

## Required gates
CI; P5-5 End-to-End Pilot Rehearsal; UI geometry golden audit; UI browser screenshot certification; exact-head artifact SHA256 + screenshot inspection.

## Merge / deployment
Never auto-merge. Human approval required after certified principal screenshot. No Vercel deployment.
