# IAMINA Web — L0 phase 2, sécurité glycémie (#972 + #974) — 22/10/2026

**GOAL** : reprendre deux correctifs déjà codés mais non mergés sur exact `main@8ada5aab8e8006bbbdc275eabbabf014a4714e0b` : `#972` rejette NaN/Infini, saisies vides/négatives et dépassements de conversion sans inventer de valeur ; `#974` empêche de quitter une saisie pendant la sauvegarde Drift.

**Préparation sans nouvelle CI** : le blob `add_log_sheet.dart` de `#972` est appliqué sur `main` puis les **trois lignes de garde `_saving`** de `#974` sont insérées en tête de `_confirmLeave`. La version `main` et la base commune `13b7cce1` partagent le même blob `8b1bf31b`, donc aucun changement récent de ce fichier n'est écrasé. Les tests et docs de chacune des deux PR sont repris sans modification.

**Preuve héritée (ne certifie pas cette combinaison)** : #972 **8/8 CI SUCCESS** sur `f7a66597`; #974 **8/8 CI SUCCESS** sur `27f069c3`. Les deux diffèrent dans le même fichier et ne doivent pas être mergées en parallèle à l'aveugle.

**Critères binaires avant intégration** : test de saisie à virgule et conversion; NaN/±Inf/overflow refusés; test temporel réel Drift sauvegarde différée, bouton retour/dismiss bloque durant insertion puis libère après; conservation du rendu UI 390/768/1280, FR/AR; contrôles unitaires exact-HEAD + FUE et garde pas de fausse glycémie; review sécurité clinique. **Aucun merge/deploy autorisé par cette préparation.**

**Statut** : COMMIT DÉTACHÉ NON PUBLIÉ, aucun PR/CI lancé pour ne pas concurrencer les 9 workflows L0 phase 1. Next : après verdict de #1140, publier PR phase 2, exécuter CI et corriger, puis préparer décision de livraison autorisée.
