# FoodPicker B34 — Bahrain core

## Goal
Add three culturally verified Bahrain concepts after certified B33 while preserving the 401-item prefix and ordering.

## Catalog
- before: 401
- target: 404
- `bahraini_muhammar` — Muhammar bahreïni / Bahraini muhammar / محمر بحريني
- `bahraini_mumawwash` — Mumawwash bahreïni / Bahraini mumawwash / مموش بحريني
- `bahraini_kebab` — Kebab bahreïni / Bahraini kebab / كباب بحريني

## Evidence
### Muhammar
- Gulf News: https://gulfnews.com/food/cooking-cuisines/muhammar-or-bahraini-sweet-rice-1.1609665316753 — Bahraini sweet rice with date syrup/spices.
- FACT Bahrain: https://fact-magazine.com/traditional-flavours-of-bahrain/ — distinctive sweet rice with dates/sugar, rose water/cardamom, served with fish.

### Mumawwash
- FACT Bahrain: https://fact-magazine.com/traditional-flavours-of-bahrain/ — rice with green lentils, spices and dried shrimp.
- Petit Futé Bahrain gastronomy: https://www.petitfute.co.uk/p65-bahrein/gastronomie/ — Bahrain specialty of rice, lentils and shrimp.

### Bahraini kebab
- Bahrain Authority for Culture and Antiquities: https://culture.gov.bh/en/mediacenter/news_center/2023/March2023/Name%2C21415%2Cen.html — official cultural-authority material identifies tikka/kebab-style popular dishes and Bahraini ingredients within traditional Bahraini cuisine heritage.
- Alalwan et al. figure/reference summary: https://www.researchgate.net/figure/Some-of-the-popular-traditional-savory-dishes-consumed-in-Bahrain-A-Harees-a_fig3_320406665 — Bahraini kebab described as a deep-fried chickpea-flour/vegetable food popular during Ramadan.
- Supporting Bahrain reference: https://almatar.com/blog/traditional-food-in-bahrain-a-taste-of-culture/ — Bahraini kebab is a fried chickpea/vegetable patty served as a snack/appetizer.

## Rejections / remediation
- Balaleet rejected: already represented in the certified catalog.
- Agaily/Gers Ogaily rejected: shared Gulf/Kuwaiti provenance is materially ambiguous for a Bahrain-specific lot.
- Mahyawa rejected: provenance is shared with southern Iran and several GCC states.
- `bahraini_halwa` rejected during CI remediation: the candidate collided with an already represented catalog ID/concept, producing 403 unique IDs for a 404-row catalog and duplicate pictogram routing. It was replaced rather than weakening the uniqueness contract.
- CI run `35808313054` on HEAD `e17c508465df36bb9880eebef49f9e9d973b09a5` exposed the duplicate plus stale B33 exact-total regression; both now have dedicated remediation.

## UI proof
BEFORE: `Musakhan palestinien`.
Goal: expose Bahrain B34 artwork with correct Gulf association and no geometry regression.
AFTER fixture: `Muhammar bahreïni`.
Viewports: 390x844, 768x1024, 1280x900.

## Gates
CI; P5-5 End-to-End Pilot Rehearsal; UI geometry golden audit; UI browser screenshot certification; exact-head artifact SHA256 + screenshot inspection. Any commit invalidates older green evidence and requires exact-head recertification.

## Merge / deployment
Never auto-merge. Human approval required after principal certified screenshot. No Vercel deployment.
