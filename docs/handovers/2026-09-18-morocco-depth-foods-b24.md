# FoodPicker B24 — Morocco depth

Goal: append three independently selectable Moroccan concepts to certified B23 (371) without altering prior entries/order.

Accepted: `moroccan_amlou`, `moroccan_khlii`, `moroccan_taktouka` → target 374.

Evidence:
- Amlou: Moroccan National Tourist Office identifies Amlou as a southern/Agadir specialty made from argan oil, honey and almonds: https://www.visitmorocco.com/en/discover-morocco/gastronomy . Slow Food Foundation independently documents traditional Amlou as an almond, honey and argan-oil food from Morocco, especially Souss-Massa: https://www.fondazioneslowfood.com/en/ark-of-taste-slow-food/amlou/ . Morocco's Terroir du Maroc platform also lists Amlou from Souss-Massa with the same core ingredients: https://terroirdumaroc.gov.ma/en_ma/eacft1000-amlou-1000g-cooperative-tighanimine.html .
- Khlii: Moroccan National Tourist Office identifies Khlii as spicy dried meat rooted in Fez: https://www.visitmorocco.com/en/discover-morocco/gastronomy . A peer-reviewed review of African animal foods identifies khlii/khlia as a typical Moroccan cured meat obtained from salted-dried meat: https://www.tandfonline.com/doi/abs/10.1080/1828051X.2017.1348915 . Morocco's Terroir du Maroc platform independently describes khlii as 100% Moroccan preserved meat: https://terroirdumaroc.gov.ma/fr_ma/catalog/product/view/id/1935/s/khlii-camelin-500-gr-cooperative-jaid/ .
- Taktouka: Moroccan National Tourist Office's food guide identifies Tektouta/Taktouka as a Moroccan pepper-and-tomato starter: https://www.visitmorocco.com/en/travel-info/food-drinks . The Mediterranean Dish independently identifies Taktouka as a traditional Moroccan roasted-pepper and tomato salad: https://www.themediterraneandish.com/taktouka-moroccan-tomato-and-roasted-bell-pepper-salad/ .

Rejected this cycle: `mrouzia`. Although the Moroccan National Tourist Office lists Mrouzia among emblematic dishes of the Kingdom, historical/reference material also describes it more broadly as Maghribi with older attestations outside modern Morocco. Under the pipeline's provenance-ambiguity rule it is not certified in B24.

Labels:
- Amlou marocain / Moroccan amlou / أملو مغربي
- Khlii marocain / Moroccan khlii / الخليع المغربي
- Taktouka marocaine / Moroccan taktouka / تكتوكة مغربية

Categories: amlou=fatSauce; khlii=meatPoultry; taktouka=saladMeal. Region: Morocco for all three.

Duplicate gate: repository-wide searches for amlou/amlu, khlii/khlea/khlia and taktouka/tektouta returned no existing catalog representation before implementation.

BEFORE: certified B23, 371 concepts. Goal: expose Amlou marocain with native pictogram at 390×844, 768×1024, 1280×900, with Morocco association, no overflow/clipping/collision and readable labels.
AFTER: pending exact-head browser certification and artifact inspection.

Required exact-head gates: CI, P5-5 End-to-End Pilot Rehearsal, UI geometry golden audit, UI browser screenshot certification. Artifact ZIP SHA256 must match GitHub digest before screenshot acceptance.

Human merge required. No Vercel.
