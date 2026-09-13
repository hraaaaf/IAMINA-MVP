# IAMINA Food Pictograms — Batch 3

## Goal
Étendre la couverture visuelle native du FoodPicker de 48 à 72 concepts sans modifier la logique nutritionnelle, la structure du catalogue ni les priorités de rendu.

## Source de vérité du lot
Le lot est dérivé du vrai algorithme `frontend/tool/food_pictogram_manifest.dart` sur `main@f8e28d5d2a23e7f802f5e62bcbd1db84ec55d31e` : 48 IDs launch prioritaires, puis reste du catalogue trié par `MealFoodCategory.index` et libellé FR, par batches de 24.

Batch 3 exact :
`baguette`, `batbout`, `bulgur`, `chebab`, `couscous`, `crepe`, `cereal`, `oats`, `waffle`, `granola`, `harcha`, `krachel`, `corn`, `muesli`, `barley`, `white_bread`, `toast_bread`, `khameer_bread`, `pita_bread`, `regag_bread`, `pancake`, `porridge`, `pasta`, `quinoa`.

## BEFORE
Référence retenue : batch 2 certifié et mergé via PR #587. Exact-head `5116306e1038ef25aef7540a3ad0924625d94649`, Chrome #34726793095 SUCCESS, mêmes viewports 390×844 / 768×1024 / 1280×900.

## Référence visuelle
Même langage natif IAMINA : illustration compacte, locale/offline, lisible à 44–48 px, ombre douce, accents teal, aucune dépendance externe, aucun texte dans le pictogramme.

## Implémentation
- `FoodPictogramPainterBatch3` natif Flutter ;
- 24 concepts céréales/pains dérivés du manifest ;
- priorité runtime conservée : asset certifié > batch 3/2/1 natif > fallback emoji ;
- aucune donnée nutritionnelle modifiée ;
- aucun asset binaire ajouté.

## Succès observable
- batch 3 = exactement 24 IDs ;
- 72 concepts natifs cumulés, sans chevauchement ;
- chaque ID existe dans le catalogue ;
- fallback emoji conservé pour le long tail ;
- CI/geometry/E2E verts ;
- Chrome AFTER réel aux 3 viewports ;
- aucune régression de layout ;
- surface `meal-picker` certifiée avec la requête `pain` afin d’exposer plusieurs pains nouvellement natifs.

## Preuve attendue
Tests unitaires/widget + workflow Chrome exact-head + inspection AFTER 390/768/1280 + comparaison au BEFORE avant merge.
