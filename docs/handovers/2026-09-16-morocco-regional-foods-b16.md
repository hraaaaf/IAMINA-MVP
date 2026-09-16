# FoodPicker B16 — Morocco regional depth

Status: IMPLEMENTED / CERTIFICATION PENDING / HUMAN MERGE REQUIRED

## Goal

Extend the certified 346-item FoodPicker catalog with three independently useful Moroccan regional concepts while preserving the V3 322-item baseline and Gulf Core B15 ordering.

Expected catalog delta: 346 → 349.

## Accepted concepts

### `medfouna_rissani` — Medfouna de Rissani / Rissani medfouna / مدفونة الريصاني

- Category: `moroccanDish`
- Region: Morocco / Drâa-Tafilalet / Rissani
- Evidence 1: Visit Drâa-Tafilalet, regional tourism authority, describes Medfouna as stuffed bread originating in Rissani and details the meat, egg, almond, onion and spice filling: https://visitdraatafilalet.com/activities/7-dishes-you-should-try-in-errachidia/
- Evidence 2: Communes & Villes du Maroc describes Medfouna as an ancestral culinary marker of Rissani/Tafilalet and details its two-layer stuffed-bread form: https://www.communesmaroc.com/ar/commune/er-rissani/articles/view/2025/03/er-rissani-histoire-millenaire-diversite-culinaire
- Supporting regional source: https://visitdraatafilalet.com/en/destinations/rissanis-souk/

### `tafernout_bread` — Pain Tafernout / Tafernout bread / خبز تفرنوت

- Category: `breadGrain`
- Region: Morocco / South and Souss-associated Amazigh food culture
- Evidence 1: Visit Drâa-Tafilalet explicitly lists Pain de Tafernout as bread found throughout Morocco's southern region and describes traditional oven/hot-sand cooking: https://visitdraatafilalet.com/activities/7-dishes-you-should-try-in-errachidia/
- Evidence 2: TasteAtlas identifies Tafernout as an Amazigh flatbread from Morocco, especially Souss, High Atlas and southern areas, and describes the earthen-oven association: https://www.tasteatlas.com/tafernout
- Supporting regional gastronomy guide: https://visitdraatafilalet.com/wp-content/uploads/2022/02/Guide-Gastro-Esp_CompressPdf.pdf

### `berkoukes` — Berkoukes / Berkoukes / بركوكس

- Category: `moroccanDish`
- Region: Morocco, with explicit Maghreb-wide provenance retained in the evidence rather than falsely claiming exclusivity
- Evidence 1: Wikipedia's reference-backed overview identifies Berkoukes as a traditional North African/Maghreb dish popular in Algeria, Tunisia and parts of Morocco, with academic/book references including Fatéma Hal's work on the Moroccan table: https://en.wikipedia.org/wiki/Berkoukes_(dish)
- Evidence 2: Afrik describes Berkoukes as a North African/Amazigh traditional dish prepared principally in Algeria, Tunisia and Morocco: https://www.afrik.com/berkoukes
- Scope note: IAMINA labels this as a Moroccan-region selectable concept, not as a uniquely Moroccan invention.

## Deduplication

The certified 322-item baseline was inspected for the accepted names. `mrouzia`, `seffa`, `rfissa`, `bissara`, `maakouda`, `khlii`, and `amlou` already exist and were rejected as duplicates despite strong source evidence. No `medfouna`, `tafernout`, or `berkoukes` concept was found in the baseline or Gulf Core B15 extension.

## Append / non-regression design

- `meal_food_catalog_v3.dart` remains untouched.
- Gulf Core B15 remains untouched and stays immediately after the 322-item baseline.
- B16 is isolated in `meal_food_morocco_regional_b16.dart` and appended after B15.
- Pictogram manifest stable append list keeps all B15 IDs before all B16 IDs.
- No backend, DB schema, patient data, auth, CGM, medication, documents or unrelated UI changes.

## Native pictograms

B16 adds native code-painted FoodPicker artwork for all three IDs:

- Medfouna: round stuffed bread with visible cut/filling cue.
- Tafernout: rustic round bread with stone-baked surface cue.
- Berkoukes: red stew/soup with visibly large semolina grains.

Generic fallback is not accepted as final B16 representation.

## Tests / certification contract

Added/updated contracts must prove:

- 322 baseline unchanged;
- 24 B15 items unchanged and ordered before B16;
- exact 346 → 349 delta;
- unique IDs;
- FR/EN/AR labels;
- searchability;
- category and Morocco-region assignment;
- native B16 pictogram routing;
- union of B1–B16 native pictogram IDs equals all 349 catalog IDs;
- visual fixture query `medfouna`.

Required exact-head gates before merge: CI, P5-5 End-to-End Pilot Rehearsal, UI geometry golden audit, UI browser screenshot certification. Browser artifact SHA256 must be checked and 390×844, 768×1024 and 1280×900 screenshots inspected.

## Merge / deployment

Never auto-merge. Owner approval is required after exact-head evidence and principal screenshot are presented.

No Vercel deployment.
