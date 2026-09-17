# FoodPicker B21 — Tunisia depth

Goal: append three independently selectable Tunisian concepts to certified B20 (362) without altering prior entries/order.

Accepted: `tunisian_brik`, `tunisian_lablabi`, `tunisian_kafteji` → target 365.

Evidence:
- Brik: Discover Tunisia (official Tunisian tourism portal) identifies the famous crispy golden egg brik as a Tunisian medina snack: https://www.discovertunisia.com/en/sophistication-and-tradition . Lonely Planet independently describes brik à l'oeuf as a classic on Tunisian restaurant menus: https://www.lonelyplanet.com/articles/7-typical-tunisian-dishes-you-must-try .
- Lablabi: Discover Tunisia identifies lablabi as a spicy chickpea soup found in Tunisian medina food culture: https://www.discovertunisia.com/en/discover/around-tunis . Lonely Planet independently describes lablabi as a hearty dish served across Tunisia: https://www.lonelyplanet.com/articles/7-typical-tunisian-dishes-you-must-try .
- Kafteji: Discover Tunisia identifies kaftaji/kafteji as fried and chopped summer vegetables with egg in Tunisian medina cuisine: https://www.discovertunisia.com/en/sophistication-and-tradition . TasteAtlas independently identifies Kafteji as a traditional Tunisian fried-vegetable dish and popular street food: https://www.tasteatlas.com/best-rated-dishes-in-tunisia .

Labels:
- Brik tunisienne / Tunisian brik / بريك تونسي
- Lablabi tunisien / Tunisian lablabi / لبلابي تونسي
- Kafteji tunisien / Tunisian kafteji / كفتاجي تونسي

Categories: brik=snackFastFood; lablabi=soup; kafteji=snackFastFood. The current region enum has no Tunisia/Maghreb value, so B21 uses `universal` rather than misclassifying Tunisian foods as Morocco or Gulf.

Duplicate gate: repository-wide searches for `brik`, `lablabi`, and `kafteji` returned no existing catalog representation before implementation.

BEFORE: certified B20, 362 concepts. Goal: expose Lablabi tunisien with native pictogram and neutral category association at 390×844, 768×1024, 1280×900, with no overflow/clipping/collision and readable labels.
AFTER: pending exact-head browser certification and artifact inspection.

Required exact-head gates: CI, P5-5 End-to-End Pilot Rehearsal, UI geometry golden audit, UI browser screenshot certification. Artifact ZIP SHA256 must match GitHub digest before screenshot acceptance.

Human merge required. No Vercel.
