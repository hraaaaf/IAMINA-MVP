# FoodPicker B26 — Libya depth

## Goal
Append a small evidence-backed Libya batch after certified B25 without disturbing the 377-item prefix.

## Baseline / target
- baseline: 377 concepts
- target: 380 concepts
- branch: `feat/foodpicker-b26-libya-depth`

## Accepted concepts
1. `libyan_bazin` — FR: Bazin libyen — EN: Libyan bazin — AR: البازين الليبي — `breadGrain`
2. `libyan_mbakbaka` — FR: Mbakbaka libyenne — EN: Libyan mbakbaka — AR: المبكبكة الليبية — `other` (pasta/stew; no dedicated pasta category exists)
3. `libyan_shorba` — FR: Chorba libyenne — EN: Libyan shorba — AR: الشوربة الليبية — `soup`

The current region enum has no Libya/Maghreb member, so B26 deliberately uses `universal` rather than misclassifying Libyan foods as Morocco or Gulf. No enum/schema expansion is mixed into this append lot.

## Provenance evidence
### Bazin
- Libya Observer, reporting Ministry of Culture + UNESCO heritage work: https://libyaobserver.ly/culture/libya-moves-preserve-cultural-heritage-unesco-support — identifies Bazeen among iconic Libyan dishes being prepared for heritage recognition.
- Associated Press, Tajoura Ramadan tradition: https://apnews.com/article/301b21e2152bdf0523357b2c0405be8c — documents bazin as a cherished traditional Libyan dish made from barley flour and served communally for iftar.

### Mbakbaka
- Libya Observer / Ministry heritage report: https://libyaobserver.ly/culture/libya-moves-preserve-cultural-heritage-unesco-support — explicitly lists Mbakbaka among iconic Libyan dishes in the Ministry's UNESCO-supported preservation work.
- Corinthia Tripoli Ramadan 2025 menu: https://www.corinthia.com/globalassets/a_new-folders-organisation-project/properties/tripoli/la-valette-ramadan-iftar---sample-menu-individual-bookings.pdf — identifies Traditional Pasta Imbakbaka in Tripoli; corroborates the dish name and local culinary use.
- TasteAtlas: https://www.tasteatlas.com/mbakbaka — supporting reference classifying Mbakbaka as a Libyan pasta stew.

### Shorba
- Corinthia Tripoli Ramadan 2025 menu: https://www.corinthia.com/globalassets/a_new-folders-organisation-project/properties/tripoli/la-valette-ramadan-iftar---sample-menu-individual-bookings.pdf — explicitly lists Traditional Libyan Shorba.
- Almenassa Libya Ramadan culture report: https://almenassa.ly/en/2026/03/03/ramadan-in-libya-a-unified-table-bridging-arab-amazigh-tuareg-and-tebu-cultures/ — documents soup as a core Ramadan table element across Libyan communities.

## Rejected / deferred
- Couscous: rejected as a new Libya-specific concept because the catalog already represents couscous and a country-prefixed duplicate would weaken concept identity.
- Asida: deferred because it is pan-regional and provenance is not specific enough for a Libya-prefixed concept under the strict ambiguity rule.
- Fatat: deferred because the name is shared across multiple MENA preparations and the available evidence does not justify a clean Libya-specific concept.

## UI proof contract
BEFORE: B25 fixture `Jareesh saoudien` at 390x844, 768x1024, 1280x900.
Goal: expose a distinctly Libyan B26 native pictogram while preserving FoodPicker geometry/category clarity.
AFTER fixture: `Bazin libyen` at the same three viewports.

## Required gates
- CI
- P5-5 End-to-End Pilot Rehearsal
- UI geometry golden audit
- UI browser screenshot certification
- exact-head artifact SHA256 verification and manual inspection of all three FoodPicker captures

## Merge / deployment
Never auto-merge. Human approval required after visual proof. No Vercel deployment.
