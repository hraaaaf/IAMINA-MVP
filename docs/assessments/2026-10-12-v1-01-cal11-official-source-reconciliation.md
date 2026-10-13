# IAMINA V1-01 / CAL-11 — Source USDA réconciliée sur snapshot officiel

**Date du contrôle :** 12 octobre 2026.
**Source primaire :** USDA FoodData Central, `FoodData_Central_foundation_food_json_2026-04-30.zip` (Foundation Foods, édition avril 2026), téléchargement GitHub Actions réussi, [run #38273801139](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38273801139), archive publique [artifact #11758012445](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38273801139/artifacts/11758012445).

- **Empreinte SHA-256 du ZIP officiel, vérifiée indépendamment depuis l'artefact :** `186e988ec542e913f51ef62b86a47758e8cdd0d1dc3889e7b055581f3c09c77a`.
- Enveloppe de preuve GitHub artefact ZIP SHA-256 : `dd3e9aaf96be394c382fc19b8669ac2cf5d107b28e007ad4a84a98f9eaa9051a` (empreinte différente de celle du ZIP USDA, **ne pas** les confondre).
- Contenu de l'archive primaire : tableau `FoundationFoods` avec 395 éléments incluant des placeholders JSON `null` ; 363 IDs non nuls uniques présents selon contrôle local. `foodNutrients[nutrient.id=1005]`, unité USDA `g` par 100 g, `foodPortions` pour les bananes.
- **7/7 anciens FDC IDs du catalogue #943 sont absents de ce snapshot Foundation**, [échec explicite du run officiel](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38273801139), ce qui n'établit pas qu'ils n'ont jamais existé dans une autre édition ou famille de données.

## Source primaire vérifiée — valeurs à porter dans le catalogue

| Famille | FDC ID présent dans le snapshot 2026-04 | Description USDA | Glucides, g / 100 g (nutriment 1005) | Portion `Banana`, `Peeled` |
|---|---:|---|---:|---:|
| Pomme | 1750339 | Apples, red delicious, with skin, raw | 14.8 | sans objet |
| Pomme | 1750340 | Apples, fuji, with skin, raw | 15.7 | sans objet |
| Pomme | 1750341 | Apples, gala, with skin, raw | 14.8 | sans objet |
| Pomme | 1750342 | Apples, granny smith, with skin, raw | 14.1 | sans objet |
| Pomme | 1750343 | Apples, honeycrisp, with skin, raw | 14.7 | sans objet |
| Banane | 1105073 | Bananas, overripe, raw | 20.1 | 110 g |
| Banane | 1105314 | Bananas, ripe and slightly ripe, raw | 23.0 | 115 g |

**Résultat de la curation du catalogue (sans extrapolation) :**
- Bornes pomme calculées **exactement depuis ces cinq lignes** : **14.1 à 15.7 g / 100 g** (ancienne borne 14.2 absente de ces cinq sources).
- Bornes banane calculées depuis ces deux lignes : **20.1 à 23.0 g / 100 g** (inchangées numériquement), mais **IDs corrigés**.
- Poids de banane pelée **110/115 g** vérifiés dans `foodPortions`, ligne `measureUnit.name='Banana'`, `modifier='Peeled'`, poids source `gramWeight`. Les poids sont des observations documentées, **pas** des recommandations patient ni la représentation certaine de n'importe quelle portion individuelle.
- Aucun résultat glycémique, indice glycémique ou dosage d'insuline ne découle de cette composition alimentaire.

## Validation automatique exigée

1. `backend/scripts/validate_v1_01_cal11_fdc.py` : fail-closed contre **tous** les ID absents/dupliqués, description hors famille, nutriment 1005 manquant/ambigu, unité autre que grammes et quantités hors bornes ; vérifie aussi la portion banane pelée correspondant à chaque source.
2. `frontend/lib/core/data/nutrition_catalog.dart` : remplacer seulement les IDs et la borne pomme ; conserver l'UI, les sélections locales et les autres aliments.
3. Tests backend synthétiques et Flutter pour figer la correspondance ; **le certificat primaire nécessite l'exécution de la vérification sur le ZIP officiel exact**, pas simplement des fixtures.
4. [PR DRAFT de réconciliation #945](https://github.com/hraaaaf/IAMINA-MVP/pull/945) : exiger la campagne source et la CI sur son **propre** HEAD final ; cette mention ne constitue pas la preuve qu'une PR ou un run existe avant son retour GitHub.

## Limites et gates

**Portée de la preuve :** correspondance des sept lignes et deux portions USDA 2026-04. C'est une réconciliation nutritionnelle et non une approbation médicale ou individuelle ; la qualité/variabilité de mesures n'est pas évaluée ici. Aucun client actuel (0), première V1 patient locale. Toute UI montrant les valeurs modifiées doit être soumise à vérification BEFORE/AFTER même viewport et traduction si les nombres changent.

**Non réglés par ce document :** CAL-09/10 définition du jour clinique + fuseau IANA du patient, CAL-12 contrat PDF clinique Unicode/RTL et consentement, revue clinique/sécurité/linguistique des fonctionnalités actives, autorisations explicites distinctes merge et Vercel. Aucune donnée réelle de patient ni activation clinique de PDF.

**Statut à l'écriture :** `OFFICIAL_SOURCE_ROWS_VERIFIED_LOCALLY / PR_HEAD_CI_PENDING / NO_MERGE / NO_DEPLOY / NOT_PATIENT_AUTHORIZED`.
