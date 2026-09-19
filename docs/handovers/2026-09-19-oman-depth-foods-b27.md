# FoodPicker B27 — Oman depth II

## Goal
Append a small evidence-backed Oman batch after certified B26 without disturbing the 380-item prefix.

## Baseline / target
- baseline: 380 concepts
- target: 383 concepts
- branch: `feat/foodpicker-b27-oman-depth-2`

## Accepted concepts
1. `omani_halwa` — FR: Halwa omani — EN: Omani halwa — AR: الحلوى العُمانية — `sweetDessert`
2. `omani_mishkak` — FR: Mishkak omani — EN: Omani mishkak — AR: مشكاك عُماني — `meatPoultry`
3. `omani_qabooli` — FR: Qabooli omani — EN: Omani qabooli — AR: قبولي عُماني — `gulfDish`

## Provenance evidence
### Omani halwa
- Oman Ministry of Heritage and Tourism / Experience Oman, About Oman: https://experienceoman.om/about-oman — identifies Omani halwa as a uniquely Omani heritage product and hospitality food.
- Oman Ministry of Heritage and Tourism / Wanderlust Oman guide: https://experienceoman.om/wp-content/uploads/2025/05/Oman-Gide-Wanderlust.pdf — documents halwa as a formal Omani welcome tradition and describes its local preparation.
- Times of Oman / Food Safety and Quality Centre reporting: https://timesofoman.com/article/126933-omani-halwa-all-set-to-become-famous-in-the-world — reports Oman-specific standards and the inherited Omani halwa craft.

### Omani mishkak
- Oman Ministry of Heritage and Tourism / Experience Oman heritage-cuisine page: https://experienceoman.om/things-to-do-categories/heritage-and-culture-activities — lists grilled Mishkak Kebabs among Omani cuisine.
- Oman Observer: https://www.omanobserver.om/article/88609/LATEST%20NEWS/mishkak-omanis-favourite-snack — describes Mishkak as a popular traditional dish across Oman and documents preparation/use.
- Times of Oman Eid traditions: https://cdn-2.timesofoman.com/article/77043-preparation-for-eid-al-fitr-begins — identifies Omani mishkak as a popular Eid food.

### Omani qabooli
- Oman Ministry of Heritage and Tourism / Experience Oman heritage-cuisine page: https://experienceoman.om/things-to-do-categories/heritage-and-culture-activities — explicitly recommends Qabooli as an authentic Omani experience and describes rice, nuts, raisins and meat.
- Times of Oman Eid traditions: https://cdn-2.timesofoman.com/article/77043-preparation-for-eid-al-fitr-begins — lists Al Qaboli among popular Omani Eid dishes.
- Condé Nast Traveler: https://www.cntraveler.com/story/the-colorful-and-complex-world-of-omani-cuisine — documents qabooli rice in the context of Oman's distinctive culinary history.

## Rejected / deferred
- Majboos: not added; already broadly represented in Gulf vocabulary and insufficiently distinct as a new Oman-specific concept.
- Harees: not added; pan-Gulf concept already represented and country-prefixing would weaken concept identity.
- Thareed: deferred for the same cross-Gulf duplicate risk.

## UI proof contract
BEFORE: B26 fixture `Bazin libyen` at 390x844, 768x1024, 1280x900.
Goal: expose a clearly Omani B27 native pictogram while preserving FoodPicker geometry and category clarity.
AFTER fixture: `Halwa omani` at the same three viewports.

## Required gates
- CI
- P5-5 End-to-End Pilot Rehearsal
- UI geometry golden audit
- UI browser screenshot certification
- exact-head artifact SHA256 verification and manual inspection of all three FoodPicker captures

## Merge / deployment
Never auto-merge. Human approval required after visual proof. No Vercel deployment.
