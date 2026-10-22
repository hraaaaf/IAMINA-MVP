# IAMINA WEB — D11 P0 No-Demo real accounts, préparé pour intégration — 22/10/2026

**GOAL :** récupérer le code déjà écrit dans [PR #1021](https://github.com/hraaaaf/IAMINA-MVP/pull/1021) pour qu'un utilisateur médical réel ne reçoive jamais de glycémies, repas ou profils artificiels.

**Preuve d'intégrabilité** : source PR HEAD `1c9e3a27d36c8802ef50295737691b24deb00e88`, [6/6 CI historiques SUCCESS](https://github.com/hraaaaf/IAMINA-MVP/pull/1021). Les 11 chemins impactés sur `main@8ada5aab8e8006bbbdc275eabbabf014a4714e0b` ont **exactement les mêmes blobs** que l'ancêtre Git `58f0dc940449e0cdace099df5350be79e34d53b4`, aucune divergence à écraser ; une nouvelle tree candidate copie les blobs PR **exactement** (y compris OpenAPI, bootstrap et tests).

**Comportement source** : HTTP patient `POST /api/v1/demo/seed` refuse la création de données artificielles même authentifié ; `setup_demo` restreint à configuration DEBUG explicitement synthétique ; Drift coffre patient refuse les seeds de test, seuls audit vault et suites synthétiques restent possibles. Pas de déploiement Vercel ou mutation DB.

**Risques/gates** : ne pas détruire les données déjà enregistrées ; vérifier migrations et chargement du bootstrap, zéro patient réel injecté, les comptes A→B→A, auth/CSRF négatifs, navigateur Flutter Web 390/768/1280, tests exact SHA, revue confidentialité/clinique et préservation éventuelle des jeux synthétiques dans *leur sandbox*. W01/W02 non certifiés, pas de GO patient. Le précédent signal de page blanche après tests D11 doit être couvert par capture réelle et reprise d'installation PWA.

**Statut** : objet commit Git DÉTACHÉ, non publié comme branche ni PR, aucune CI supplémentaire lancée pour ne pas concurrencer L0 #1140. **NEXT** : après vérification du lot réseau L0, publier PR dédiée D11 défensive, lancer CI + captures / tests négatifs, corriger tout fail, obtenir revues, puis merge/postmerge sous gates et permission de déploiement distincte.
