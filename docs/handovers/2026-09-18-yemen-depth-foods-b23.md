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
AFTER: pending exact-head browser certification and artifact inspection.

Required exact-head gates: CI, P5-5 End-to-End Pilot Rehearsal, UI geometry golden audit, UI browser screenshot certification. Artifact ZIP SHA256 must match GitHub digest before screenshot acceptance.

Human merge required. No Vercel.
