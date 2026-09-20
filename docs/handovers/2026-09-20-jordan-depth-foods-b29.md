# FoodPicker B29 — Jordan depth I

## Goal
Append a small evidence-backed Jordan batch after certified B28 without disturbing the 386-item prefix.

## Baseline / target
- baseline: 386 concepts
- target: 389 concepts
- branch: `feat/foodpicker-b29-jordan-depth-1`

## Accepted concepts
1. `jordanian_mansaf` — FR: Mansaf jordanien — EN: Jordanian mansaf — AR: منسف أردني — `meatPoultry`
2. `jordanian_rashouf` — FR: Rashouf jordanien — EN: Jordanian rashouf — AR: رشوف أردني — `soup`
3. `jordanian_makmoura` — FR: Makmoura jordanienne — EN: Jordanian makmoura — AR: مكمورة أردنية — `meatPoultry`

## Provenance evidence
### Mansaf
- UNESCO ICH: https://ich.unesco.org/en/RL/al-mansaf-in-jordan-a-festive-banquet-and-its-social-and-cultural-meanings-01849 — Jordan nomination, inscribed 2022; festive lamb/goat, yogurt, rice/bulgur and bread dish.
- Visit Jordan: https://international.visitjordan.com/unesco/ — identifies Mansaf as a classic Jordanian Bedouin dish.
- National Geographic: https://www.nationalgeographic.com/travel/article/fast-facts-62 — independently identifies Mansaf as Jordan's traditional dish.

### Rashouf
- Visit Jordan: https://edutravel.visitjordan.com/en/page/79/Food-and-Drinks — identifies Rushoof as a Jordanian Bedouin dish of legumes and yogurt.
- Jordan Heritage Restaurant menu: https://www.jordanheritage.jo/wp-content/uploads/2025/01/JH-Petra-Main-Menu_compressed.pdf — identifies Rashouf across Jordanian regions and describes jameed, lentils, pulses and grains.
- Tasting Table: https://www.tastingtable.com/695680/must-try-jordanian-food-mansaf/ — independently documents Jordanian rashouf with jameed, lentils and wheat.

### Makmoura
- Jordan Times: https://jordantimes.com/news/local/makmoora-taste-irbid-loved-across-region — documents Makmoora as an iconic northern Jordan/Irbid layered chicken-onion pastry.
- Jordan Times: https://jordantimes.com/news/features/beyond-mansaf-four-traditional-jordanian-dishes-you-probably-did-not-know — independently documents Makmura as a traditional Jordanian dish rooted in Irbid.
- Jordan News: https://www.jordannews.jo/Section-101/Good-Food/The-joys-of-olives-9587 — describes Makmoorah as the pride of north Jordan.

## Anti-duplicate review
Current default branch was searched for mansaf, rashouf/rushoof and makmoura/makmoora; no matching concept was found. Shared Levantine staples already represented in the catalog were not duplicated.

## UI proof contract
BEFORE: B28 fixture `Pastilla marocaine` at 390x844, 768x1024, 1280x900.
Goal: expose a clearly Jordanian B29 native pictogram while preserving FoodPicker geometry and baseline order.
AFTER fixture: `Mansaf jordanien` at the same three viewports.

## Required gates
- CI
- P5-5 End-to-End Pilot Rehearsal
- UI geometry golden audit
- UI browser screenshot certification
- exact-head artifact SHA256 verification and manual inspection of all three FoodPicker captures

## Merge / deployment
Never auto-merge. Human approval required after visual proof. No Vercel deployment.
