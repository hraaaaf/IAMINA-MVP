# FoodPicker B22 — Algeria depth

Goal: append three independently selectable Algerian concepts to certified B21 (365) without altering prior entries/order.

Accepted: `algerian_rechta`, `algerian_chakhchoukha`, `algerian_mhadjeb` → target 368.

Evidence:
- Rechta: Lonely Planet describes reshta/rechta as a traditional Algerian festive dish of noodle-thin pasta with white broth, chickpeas, vegetables and chicken/meat: https://www.lonelyplanet.com/articles/what-to-eat-and-drink-in-algeria . Its Algiers guide independently lists rechta among traditional Algerian staples: https://www.lonelyplanet.com/articles/best-things-to-do-in-algiers .
- Chakhchoukha: Lonely Planet identifies Algerian chakhchoukha as torn flatbread soaked with chickpea, meat and vegetable sauce and locates it especially in eastern Algeria: https://www.lonelyplanet.com/articles/what-to-eat-and-drink-in-algeria . Its Algiers guide independently lists chakhchoukha among traditional Algerian dishes: https://www.lonelyplanet.com/articles/best-things-to-do-in-algiers .
- Mhadjeb: Lonely Planet identifies m’hadjeb as Algerian street food, thin layered flatbread stuffed with onion, garlic and tomato sauce: https://www.lonelyplanet.com/articles/what-to-eat-and-drink-in-algeria . Its Algiers guide independently calls mhadjeb an Algiers street-food staple: https://www.lonelyplanet.com/articles/best-things-to-do-in-algiers .

Labels:
- Rechta algérienne / Algerian rechta / رشتة جزائرية
- Chakhchoukha algérienne / Algerian chakhchoukha / شخشوخة جزائرية
- Mhadjeb algérien / Algerian mhadjeb / محاجب جزائرية

Categories: rechta=other; chakhchoukha=other; mhadjeb=snackFastFood. Current region enum has no Algeria/Maghreb value, so B22 uses `universal` rather than misclassifying Algerian foods as Morocco or Gulf.

Duplicate gate: repository-wide search for rechta/reshta, chakhchoukha and mhadjeb/mhajeb returned no existing catalog representation before implementation.

BEFORE: certified B21, 365 concepts. Goal: expose Chakhchoukha algérienne with native pictogram and neutral category association at 390×844, 768×1024, 1280×900, with no overflow/clipping/collision and readable labels.
AFTER: pending exact-head browser certification and artifact inspection.

Required exact-head gates: CI, P5-5 End-to-End Pilot Rehearsal, UI geometry golden audit, UI browser screenshot certification. Artifact ZIP SHA256 must match GitHub digest before screenshot acceptance.

Human merge required. No Vercel.
