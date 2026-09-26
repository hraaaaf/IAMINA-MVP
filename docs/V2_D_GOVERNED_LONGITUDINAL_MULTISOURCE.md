# IAMINA — V2-D GOVERNED LONGITUDINAL MULTI-SOURCE INTELLIGENCE

Base certifiée : `main@efc4ac1517040f7253073dec6d5a2ccad1aeafbc`.

## Goal

Consommer le contrat de fusion V2-C dans une primitive longitudinale gouvernée, sans fusionner anonymement les populations ni transformer une corrélation descriptive en causalité.

## Succès

- V2-D exige un `GovernedGlucoseFusionContract` V2-C explicite ;
- Journal, CGM et import restent des populations séparées ;
- aucune population n'est ajoutée implicitement ;
- chaque fait conserve son `source_ref` et sa provenance ;
- le statut `ready` exige une suffisance produit explicite dans chaque population demandée ;
- si une population est insuffisante, le résultat fail-closed vers `insufficient_data` sans supprimer les faits observés ;
- les statistiques restent descriptives et séparées par population ;
- aucune causalité, cible clinique, prédiction, réponse thérapeutique, dose ou recommandation n'est produite ;
- les producteurs historiques `personal_response` et `paired_meal_response` restent Journal-only.

## Contrat V2-D

`governed-longitudinal-multisource.v1`

Suffisance produit par défaut :
- au moins 3 faits par population ;
- au moins 2 jours distincts par population.

Ces seuils représentent une règle de suffisance produit pour autoriser une vue longitudinale descriptive. Ils ne constituent ni un seuil clinique ni une preuve statistique.

## Preuve attendue

Tests déterministes :
- contrat invalide fail-closed ;
- Journal + import suffisants → `ready` ;
- une population insuffisante → `insufficient_data` ;
- conservation des faits et `source_ref` ;
- isolation patient ;
- limitations explicites anti-causalité.

## Hors scope

- modification des patterns Journal existants ;
- inférence causale repas→glycémie ;
- corrélation statistique ou significativité ;
- seuils/targets cliniques ;
- conseil thérapeutique ou dose ;
- UI ;
- migration DB ;
- déploiement Vercel.
