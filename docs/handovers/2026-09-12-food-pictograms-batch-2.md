# IAMINA Food Pictograms — Batch 2

## Goal
Étendre de 24 à 48 pictogrammes natifs IAMINA sans modifier la logique nutritionnelle ni la structure du FoodPicker.

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

## Preuve attendue
Tests unitaires/widget + workflow Chrome exact-head + inspection AFTER 390/768/1280 avant merge.
