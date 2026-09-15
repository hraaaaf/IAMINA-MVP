# IAMINA — Gulf Core Foods B15

Status: FINAL CERTIFICATION — cultural audit complete; exact-head gates required before merge

## Goal

Extend the certified 322-item meal catalog with 24 reviewed GCC foods while preserving the existing V3 catalog and B1-B14 pictogram assignments.

Success = 346/346 catalog items resolve to native pictograms, the first 322 IDs remain byte-stable through the V3 baseline module, search/serialization accept new foods, and exact-head CI + browser + P5-5 + geometry gates pass.

## Base / non-regression boundary

- Source baseline: current `main` after B14 certification and subsequent unrelated docs-only merges.
- `meal_food_catalog_v3.dart` is the unchanged certified 322-item catalog blob.
- `meal_food_catalog.dart` is the compatibility facade and appends Gulf Core only.
- Manifest ordering explicitly appends B15 after the 322-item baseline so B1-B14 cannot be reshuffled.
- No backend, DB, patient data, documents, API schema or deployment changes.

## B15 IDs — 24

`matazeez`, `areeka`, `masoub`, `haneeth`, `maghsh`, `samak_mkashan`, `mahshoosh`, `marsah`, `gahwa_gishr`, `tasabea`, `mashgotha`, `miva_bread`, `qabooli`, `mishkak`, `omani_halwa`, `lamb_khuzi`, `bahraini_halwa`, `malgoum`, `louba_bahraini`, `bahraini_tikka`, `tashreeb`, `murabiyan`, `mutabbaq_zubaidi`, `dakkous`.

## Cultural validation

The candidate list was checked against independent, serious regional sources before final certification:

- Saudi Arabia: Visit Saudi documents Jazan specialties including Maghsh, Samak Mkashan, Mahshoosh, Marsah and Gahwa Gishr; its Aseer material documents Haneeth, Areeka, Tasabea, Mashgotha and Miva bread. The Saudi Culinary Arts Commission also identifies Matazeez, Areeka, Mashghotha and multiple Jazan dishes in its national gastronomy material.
  - https://www.visitsaudi.com/en/jazan/stories/jazan-taste
  - https://www.visitsaudi.com/en/aseer/stories/traditional-dishes-and-flavors-of-abha
  - https://culinary.moc.gov.sa/-/media/Project/Ministries/Commission/culinaryarts/Culinary-Arts-Books/CAC-Gastronomy-Tourism-Book.pdf
- Oman: the Ministry of Heritage and Tourism portal identifies Mishkak, Qabooli and Omani halwa as authentic Omani food/hospitality traditions.
  - https://experienceoman.om/things-to-do-categories/heritage-and-culture-activities
- UAE: the official UAE government portal and Experience Abu Dhabi identify Khuzi/Ghuzi as traditional Emirati cuisine.
  - https://u.ae/en/information-and-services/visiting-and-exploring-the-uae/what-to-do-in-the-uae/dining-
  - https://visitabudhabi.ae/en/plan-your-trip/article-hub/emirati-food-to-try/
- Bahrain: Bahrain Tourism documents Bahraini halwa and louba, and its street-food guide documents tikka and malgoum as local staples.
  - https://www.bahrain.com/en/try-these-places-for-a-taste-of-authentic-bahraini-breakfast
  - https://www.bahrain.com/en/bahrain-street-food-guide
- Kuwait: Kuwait Times/KUNA material documents tashreeb, murabiyan and mutabbak zbaidi as traditional Kuwaiti dishes. Daqoos/dakkous is independently documented as a Gulf tomato-garlic sauce strongly associated with Kuwait and neighbouring Gulf cuisines.
  - https://kuwaittimes.com/traditional-kuwaiti-food-items-still-present-in-ramadan-meals/amp/
  - https://www.tasteatlas.com/daqoos

Scope note: several Saudi entries are regional Aseer/Jazan/Najd foods. They are included under the app's `gulf` region as GCC/Saudi coverage, not as a claim that every item originates on the Persian/Arabian Gulf coast.

## CI defect resolved before final certification

The first PR-head run reached 419 passed / 1 failed / 1 skipped. The only failure was the historical `meal_capture_panel_test.dart` expecting catalog version `3.0.0-morocco-gcc` after B15 intentionally advanced it to `3.1.0-morocco-gcc-core`. The test expectation was updated; no production catalog behavior was changed by that fix.

## Visual certification

BEFORE: certified B14 FoodPicker, 322 native concepts.

Goal: 24 new GCC concepts are visually distinct, readable, native, and do not alter existing layout or responsive geometry.

AFTER query fixture: `halwa`.

Required viewports: 390×844, 768×1024, 1280×900.

Required exact-head gates:
1. CI
2. UI browser screenshot certification
3. P5-5 End-to-End Pilot Rehearsal
4. UI geometry golden audit (Ahem text)

P7: N/A for catalog/pictogram-only scope.

No Vercel deployment is part of this lot.
