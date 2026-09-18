# FoodPicker B23 — Yemen depth

Goal: append three independently selectable Yemeni concepts to certified B22 (368) without altering prior entries/order.

Accepted: `yemeni_saltah`, `yemeni_fahsa`, `yemeni_bint_al_sahn` → target 371.

Evidence:
- Saltah: Embassy of the Republic of Yemen in Warsaw identifies Saltah as a traditional northern Yemeni lunchtime staple built around hulba: https://embassy-of-yemen.pl/en/home/visit-yemen/tourism-in-yemen/must-try/ . Humanities LibreTexts' Yemeni Republic reference independently describes Yemeni Saltah/Fahsa food context: https://human.libretexts.org/Bookshelves/Languages/Arabic/Arabic_Level_One/09%3A_At_Home__fi_Albayet/9.10%3A_Yemeni_Republic .
- Fahsa: Humanities LibreTexts identifies Fahsa as a popular Yemeni stew, thicker than Saltah, made with slow-cooked shredded lamb or beef and served with Yemeni flatbread. Fifteen.net independently describes Fahsa as a traditional Yemeni lamb stew finished with hulbah: https://www.fifteen.net/dishes/yemeni/ .
- Bint al-sahn: Humanities LibreTexts identifies Bint Al-Sahn/Sabaya as a traditional Yemeni layered dough dessert with clarified butter and honey. Sumy State University educational material independently lists Bint Al-Sahn as a popular Yemeni dessert eaten with honey: https://essuir.sumdu.edu.ua/server/api/core/bitstreams/34e31cb3-3baf-429f-991b-ca9e782847fb/content .

Labels:
- Saltah yéménite / Yemeni saltah / سلتة يمنية
- Fahsa yéménite / Yemeni fahsa / فحسة يمنية
- Bint al-sahn yéménite / Yemeni bint al-sahn / بنت الصحن اليمنية

Categories: saltah=other; fahsa=other; bint-al-sahn=sweetDessert. Current region enum has no Yemen value, so B23 uses `universal` rather than misclassifying Yemeni foods as Gulf.

Duplicate gate: repository-wide search for saltah/salta, fahsa/fahsah and bint al-sahn/sabayah returned no existing catalog representation before implementation.

BEFORE: certified B22, 368 concepts. Goal: expose Bint al-sahn yéménite with native pictogram and neutral category association at 390×844, 768×1024, 1280×900, with no overflow/clipping/collision and readable labels.
AFTER: exact-head browser artifact inspected at all three required viewports; native pictogram present, label readable, no visible overflow/clipping/collision.

Certified PR HEAD: `11cc48de7001266dcaaf99e9ef36f9b1e4bab586`.
PR #676 merged by explicit human approval as squash commit `a668e22041a421adbc8b96a49adac5aee886021a`.
Exact-head artifact: `10527330467`; verified SHA256: `2f8f1f82d2558b55241a566b583116d0211a68be1c6641ac0f81339c9058b9aa`.

Post-merge closeout on `main@a668e22041a421adbc8b96a49adac5aee886021a`:
- CI `35316363627` — SUCCESS
- P5-5 `35316363639` — SUCCESS
- UI geometry `35316363643` — SUCCESS
- UI browser screenshot certification `35316363613` — SUCCESS
- CGM onboarding browser certification `35316363810` — SUCCESS

Status: B23 CLOSED / VERIFIED. Catalog baseline for the next lot: 371. No Vercel deployment performed by the food pipeline.
