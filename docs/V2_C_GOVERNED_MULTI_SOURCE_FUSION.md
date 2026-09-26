# IAMINA — V2-C FUSION MULTI-SOURCE GOUVERNÉE

Reprendre après V2-B certifié post-merge. Base main = 5d889f57c92cb7497854f2461e43d34f300155cc. Objectif : définir puis implémenter un contrat explicite et fail-closed de fusion multi-source entre Journal et CGM/import, sans mélanger silencieusement les populations ni dégrader la provenance.

## Goal

Créer une primitive serveur de fusion glucose multi-source qui n'admet aucune population implicitement, conserve la provenance de chaque fait, exclut les voies CGM ambiguës et ne déduplique jamais silencieusement deux observations issues de sources différentes.

## Succès

- le contrat doit exiger explicitement Journal + CGM et/ou import ;
- Journal reste limité aux sources patient manual et voice verrouillées par V2-B ;
- l'import reste une population distincte, sa provenance ne peut pas être revendiquée via les écritures patient `/logs`, et une ligne historique non vérifiable par l'identité déterministe d'import serveur est exclue fail-closed ;
- le CGM admis provient uniquement de CGMReadingRecord relié à une session capteur cohérente appartenant au même patient ;
- les anciens LogEntry(source="cgm") restent exclus ;
- chaque fait fusionné conserve source_type, source_ref et provenance ;
- aucune déduplication inter-source n'est autorisée par ce contrat ;
- patient, fenêtre temporelle et timezone sont validés fail-closed ;
- aucun nouveau diagnostic, seuil, causalité, prédiction, dose ou conseil thérapeutique n'est introduit.

## Preuve attendue

Tests déterministes couvrant : contrat invalide, fusion Journal+CGM+import, conservation de provenance, doublons inter-source conservés, ancien CGM LogEntry exclu, CGM non relié à une session exclu, isolation patient et fenêtre timezone-aware obligatoire.

## Hors scope V2-C

- changement de calcul des patterns Journal existants ;
- promotion de métriques CGM normatives ;
- déduplication probabiliste ou heuristique ;
- fusion documentaire/laboratoire ;
- changement UI ;
- déploiement Vercel ;
- autorisation real-patient.

## Closeout certifié

- PR produit : #797 — `V2-C: governed multi-source glucose fusion`.
- HEAD candidat certifié : `08367fb57ef425fa9d17b752c61a08d8f90dd2d0`.
- Pré-merge : CI #5032 SUCCESS ; Django migration drift #4082 SUCCESS.
- Merge commit exact : `70c14005a3def61b203a88b64045479858705c43`.
- Post-merge sur ce SHA : CI #5033 SUCCESS ; Django migration drift #4083 SUCCESS ; Dashboard global certification v2 #49 SUCCESS.
- Résultat : V2-C certifié post-merge.
- UI : aucun changement.
- Schéma DB : aucune migration.
- Déploiement Vercel : aucun.
