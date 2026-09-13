# IAMINA Food Pictograms — Batch 2

## Goal
Étendre de 24 à 48 pictogrammes natifs IAMINA sans modifier la logique nutritionnelle ni la structure du FoodPicker.

## État
CLOSED / MERGED.

## BEFORE
Référence retenue : captures exact-head du batch 1 (PR #584), certifiées par `UI browser screenshot certification` aux viewports 390×844, 768×1024 et 1280×900.

## Référence visuelle
Même langage que le batch 1 : illustration alimentaire compacte, locale/offline, formes lisibles à 44–48 px, ombre douce, accents IAMINA teal, pas de texte dans le pictogramme.

## Batch 2
24 concepts : rfissa, tajine poulet citron confit, tajine kefta, zaalouk, taktouka, amlou, thé à la menthe, thé marocain sucré, pain arabe, pain tannour, machboos poulet, kabsa poulet, mandi poulet, harees, jareesh, thareed, balaleet, luqaimat, dattes, dattes Ajwa, café arabe, karak, shawarma poulet, houmous.

## Succès observable
- 48 concepts natifs au total, 24 + 24 sans chevauchement ;
- aucun ID absent du catalogue ;
- fallback emoji conservé pour le long tail ;
- semantics textuelles inchangées ;
- CI, geometry et E2E verts ;
- Chrome AFTER réel aux 3 viewports ;
- aucune régression de layout ;
- le surface `meal-picker` expose volontairement plusieurs concepts batch 2 via la requête de certification `ta`.

## Preuve retenue
Exact-head final `5116306e1038ef25aef7540a3ad0924625d94649` :
- CI #34726793044 — SUCCESS ;
- UI geometry #34726793036 — SUCCESS ;
- P5-5 E2E #34726793035 — SUCCESS ;
- P7 responsive #34726793058 — SUCCESS ;
- UI browser screenshot #34726793095 — SUCCESS ;
- AFTER inspecté aux 390×844 / 768×1024 / 1280×900, sans clipping/overflow observé ;
- PR #587 squash-merge confirmée ;
- merge `main@f8e28d5d2a23e7f802f5e62bcbd1db84ec55d31e`.

Aucun déploiement Vercel n’a été demandé ni effectué pour ce lot.
