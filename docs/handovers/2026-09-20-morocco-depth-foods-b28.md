# FoodPicker B28 — Morocco depth II

## Goal
Append a small evidence-backed Morocco batch after certified B27 without disturbing the 383-item prefix.

## Baseline / target
- baseline: 383 concepts
- target: 386 concepts
- branch: `feat/foodpicker-b28-morocco-depth-2`

## Accepted concepts
1. `moroccan_pastilla` — FR: Pastilla marocaine — EN: Moroccan pastilla — AR: بسطيلة مغربية — `other`
2. `marrakech_tanjia` — FR: Tanjia marrakchia — EN: Marrakech tanjia — AR: طنجية مراكشية — `meatPoultry`
3. `moroccan_mrouzia` — FR: Mrouzia marocaine — EN: Moroccan mrouzia — AR: مروزية مغربية — `meatPoultry`

## Provenance evidence
### Pastilla
- Moroccan National Tourist Office (ONMT), Gastronomy: https://visitmorocco.com/en/discover-morocco/gastronomy — identifies Pastilla among Morocco's emblematic dishes.
- Moroccan National Tourist Office, Fes guide: https://www.visitmorocco.com/sites/default/files/atoms/files/Fes%20ENG.pdf — documents pigeon-and-almond pastilla as a Fassi local delicacy and culinary tradition.
- Saveur: https://www.saveur.com/article/recipes/moroccan-pigeon-pie-bstilla/ — independently documents Moroccan b'stilla/pastilla, its poultry filling and festive use.

### Tanjia marrakchia
- Moroccan National Tourist Office, Food & Drink: https://visitmorocco.com/en/travel-info/food-drinks — identifies Tanjia as the staple dish of Marrakech and describes the terracotta-jar preparation.
- Moroccan National Tourist Office, Gastronomy: https://visitmorocco.com/fr/decouvrir-le-maroc/gastronomie — specifically lists tanjia among foods to taste at Marrakech's Jemaa el-Fna.
- Saveur: https://www.saveur.com/culture/tangia-marrakech/ — independently documents tangia/tanjia as a Marrakech-specific slow-cooked meat dish and its traditional hammam-furnace preparation.

### Mrouzia
- Moroccan National Tourist Office, Gastronomy: https://visitmorocco.com/en/discover-morocco/gastronomy — identifies Mrouzia among Morocco's emblematic dishes.
- Moroccan National Tourist Office, Fes guide: https://www.visitmorocco.com/sites/default/files/atoms/files/Fes%20ENG.pdf — documents Mrouzia as a high point of Fassi cuisine, traditionally prepared for Eid al-Adha with ras el hanout.
- Saveur, Ras el Hanout: https://www.saveur.com/article/Recipes/North-African-Spice-Mix/ — independently identifies Moroccan mrouzia as honey-braised lamb shanks using ras el hanout.

## Anti-duplicate review
- `rfissa` was explicitly rejected: it already exists in the certified catalog.
- generic tagine variants were not added: the catalog already contains broad tagine concepts and country-prefixing would weaken concept identity.
- accepted IDs and aliases were searched against the current default branch before implementation; no matching Pastilla, Tanjia or Mrouzia concept was found.

## UI proof contract
BEFORE: B27 fixture `Madrouba omanaise` at 390x844, 768x1024, 1280x900.
Goal: expose a clearly Moroccan B28 native pictogram while preserving FoodPicker geometry and category clarity.
AFTER fixture: `Pastilla marocaine` at the same three viewports.

## Required gates
- CI
- P5-5 End-to-End Pilot Rehearsal
- UI geometry golden audit
- UI browser screenshot certification
- exact-head artifact SHA256 verification and manual inspection of all three FoodPicker captures

## Merge / deployment
Never auto-merge. Human approval required after visual proof. No Vercel deployment.
