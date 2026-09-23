# FoodPicker B34 — Bahrain core

## Goal
Add three culturally verified Bahrain concepts after certified B33 while preserving the 401-item prefix and ordering.

## Catalog
- before: 401
- target: 404
- `bahraini_muhammar` — Muhammar bahreïni / Bahraini muhammar / محمر بحريني
- `bahraini_mumawwash` — Mumawwash bahreïni / Bahraini mumawwash / مموش بحريني
- `bahraini_halwa` — Halwa bahreïnie / Bahraini halwa / حلوى بحرينية

## Evidence
### Muhammar
- Gulf News: https://gulfnews.com/food/cooking-cuisines/muhammar-or-bahraini-sweet-rice-1.1609665316753 — Bahraini sweet rice with date syrup/spices.
- FACT Bahrain: https://fact-magazine.com/traditional-flavours-of-bahrain/ — distinctive sweet rice with dates/sugar, rose water/cardamom, served with fish.

### Mumawwash
- FACT Bahrain: https://fact-magazine.com/traditional-flavours-of-bahrain/ — rice with green lentils, spices and dried shrimp.
- Petit Futé Bahrain gastronomy: https://www.petitfute.co.uk/p65-bahrein/gastronomie/ — Bahrain specialty of rice, lentils and shrimp.

### Bahraini halwa
- Bahrain Authority for Culture and Antiquities: https://culture.gov.bh/en/events/AnnualFestivalsandEvents/HeritageFestival/HeritageFestival2017/Food/ — famous traditional Bahraini/GCC sweet; ingredients and 200+ year Shuwaiter tradition.
- Al-Monitor/AFP: https://www.al-monitor.com/originals/2022/04/bahraini-artisans-toil-preserve-sugar-coated-tradition — independent reporting on Bahrain's traditional halwa confectionery heritage.

## Rejections
- Balaleet rejected: already represented in the certified catalog.
- Agaily/Gers Ogaily rejected: shared Gulf/Kuwaiti provenance is materially ambiguous for a Bahrain-specific lot.
- Mahyawa rejected: provenance is shared with southern Iran and several GCC states.

## UI proof
BEFORE: `Musakhan palestinien`.
Goal: expose Bahrain B34 artwork with correct Gulf association and no geometry regression.
AFTER fixture: `Muhammar bahreïni`.
Viewports: 390x844, 768x1024, 1280x900.

## Gates
CI; P5-5 End-to-End Pilot Rehearsal; UI geometry golden audit; UI browser screenshot certification; exact-head artifact SHA256 + screenshot inspection.

## Merge / deployment
Never auto-merge. Human approval required after principal certified screenshot. No Vercel deployment.
