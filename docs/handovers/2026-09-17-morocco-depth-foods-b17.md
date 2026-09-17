# FoodPicker B17 — Morocco depth

Goal: append four independently selectable Moroccan concepts to certified B16 (349) without altering prior entries/order.

Accepted after duplicate remediation: `tanjia_marrakchia`, `boulfaf`, `lben_moroccan`, `raib_moroccan` → target 353.

Rejected during certification: `chebakia`. Exact-head CI proved that `chebakia` was already represented in the certified catalog, producing 353 rows but only 352 unique IDs and a duplicate pictogram path. It was removed from B17 rather than weakening the uniqueness contract.

Evidence:
- Tanjia: Moroccan National Tourist Office, https://www.visitmorocco.com/fr/informations-pratiques/d%C3%A9guster — emblematic Marrakech dish, lamb/veal slow-cooked in terracotta; TasteAtlas, https://www.tasteatlas.com/tanjia — Marrakech Moroccan specialty and clay-urn preparation.
- Boulfaf: Choumicha, https://choumicha.ma/recette/929-brochettes-de-foie-a-la-crepine-de-mouton-boulfaf.html — Moroccan festive grilled liver brochettes wrapped in sheep caul fat, categorized under Saveurs du Maroc / Aid Al Adha; TasteAtlas, https://www.tasteatlas.com/boulfaf — traditional Moroccan grilled lamb-liver dish associated with Eid al-Adha. Supporting reference: Taste of Maroc, https://tasteofmaroc.com/caul-fat-wrapped-liver-brochettes-boulfaf/ — Moroccan liver brochettes distinguished by caul-fat wrapping and strong Eid association.
- Lben: Moroccan National Tourist Office, https://www.visitmorocco.com/en/travel-info/food-drinks — fermented milk served across Morocco, notably with couscous; Jibal, https://www.jibal.ma/en/products/jibal-lben-fermented-milk/ — traditional Moroccan fermented dairy beverage.
- Raib: Moroccan National Tourist Office, same food/drinks page — traditional Moroccan yoghurt; COPAG, https://copag.ma/fr/produits-laitiers-et-derives/raib-jaouda — fermented-milk raib; Jibal, https://www.jibal.ma/en/products/jibal-raib-2/ — Moroccan traditional dairy specialty.

Labels: Tanjia marrakchia / Marrakesh tanjia / طنجية مراكشية; Boulfaf / Boulfaf / بولفاف; Lben marocain / Moroccan lben / اللبن المغربي; Raïb marocain / Moroccan raib / الرايب المغربي.

Categories: tanjia=moroccanDish; boulfaf=meatPoultry; lben/raib=dairy.

Certification history:
- HEAD `895b470663bc937d0226fb1b976fb2c1bfb8e65a`: P5-5, Geometry and Browser passed; CI failed 455 passed / 5 failed. Root cause was duplicate `chebakia` plus stale B16 catalog-version expectation.
- Remediation replaces `chebakia` with independently verified `boulfaf`, adds its native painter/manifest route, adds a regression test forbidding B17 from reintroducing duplicate `chebakia`, and aligns the catalog-version test with `3.3.0-morocco-depth-b17`.
- Any green evidence from `895b4706…` is stale after remediation; all required gates must run again on the new exact HEAD.

Human merge required. No Vercel.
