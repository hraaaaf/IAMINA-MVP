## 23/10/2026 — D11 L0 : candidat d'intégration prêt pour CI exacte

**GOAL** : aucun faux historique médical dans un compte réel (API, coffre Drift, bootstrap Web). **CRITÈRE de succès** : tentatives synthétiques A/B authentifiées et hors-auth renvoient 401/403 sans création ni mutation de profil/log ; aucun seed sur un coffre de patient ; seule la base explicitement d'audit peut contenir les fixtures ; les chemins visuels Web restent fonctionnels sans altérer IndexedDB patient.

**Code repris** : 11 fichiers de l'ancienne PR #1021 recopiés blob pour blob sur `main@8ada5aab`, sans écrasement d'autres modifications de ces chemins. L'API `POST /demo/seed` refuse systématiquement 403 ; le coffre médical interdit `seedDemoData` ; le script bootstrap nettoie seulement service-workers/cache applicatif de Preview. **Durcissement supplémentaire** : commande `setup_demo` refuse PostgreSQL, même si DEBUG et le drapeau `--confirm-synthetic-only` sont présents. Un test négatif simule le moteur PostgreSQL.

**Preuves disponibles** : ancienne #1021 = 6/6 CI SUCCESS sur son ancien HEAD. **AUCUNE validation encore au HEAD d'intégration** ; attendre CI backend/Flutter, tests Web first-use et authentification negative. **Limites** : SQLite autorisé n'est pas une preuve automatique que la base est strictement synthétique ; audits indépendants sécurité/clinique et intégration W01 A→B→A restent requis.

**Statut : PR DRAFT d'intégration à publier, NO-GO merge et Vercel, pas d'écriture Neon/Production.**

---

## 23/10/2026 — D11 P0 indépendamment durci (candidat non publié)

**Faiblesse préexistante** : `setup_demo` acceptait `DEBUG=True` plus `--confirm-synthetic-only`, sans vérifier le moteur SQL. Une instance PostgreSQL accidentellement démarrée en DEBUG pourrait donc recevoir des profils, lectures fictives et des comptes démo.

**Correction candidate** : ajouter **refus explicite si moteur DATABASES['default'].ENGINE différent de `django.db.backends.sqlite3`**, en plus des deux gates existants. Test négatif avec PostgreSQL simulé et DEBUG/flag pourtant valides ; test de non-création des utilisateurs. Pas de manipulation DB réelle. Restriction au moteur SQLite = réduction du risque, **ne certifie pas à elle seule la nature isolée de toute base SQLite**, qui reste un prérequis d'exploitation.

**Goal** : interdiction démontrable d'écriture de données fictives dans PostgreSQL depuis la commande, y compris un environnement mal configuré en DEBUG. **Preuve requise** : exécuter le nouveau test et la suite D11 avant d'exposer cette candidate en PR, puis contrôle indépendant du raccordement API/vault A→B→A. En attendant D11 est **NON LIVRÉ**, W01 NO-GO.

---

# IAMINA WEB — D11 P0 No-Demo real accounts, préparé pour intégration — 22/10/2026

**GOAL :** récupérer le code déjà écrit dans [PR #1021](https://github.com/hraaaaf/IAMINA-MVP/pull/1021) pour qu'un utilisateur médical réel ne reçoive jamais de glycémies, repas ou profils artificiels.

**Preuve d'intégrabilité** : source PR HEAD `1c9e3a27d36c8802ef50295737691b24deb00e88`, [6/6 CI historiques SUCCESS](https://github.com/hraaaaf/IAMINA-MVP/pull/1021). Les 11 chemins impactés sur `main@8ada5aab8e8006bbbdc275eabbabf014a4714e0b` ont **exactement les mêmes blobs** que l'ancêtre Git `58f0dc940449e0cdace099df5350be79e34d53b4`, aucune divergence à écraser ; une nouvelle tree candidate copie les blobs PR **exactement** (y compris OpenAPI, bootstrap et tests).

**Comportement source** : HTTP patient `POST /api/v1/demo/seed` refuse la création de données artificielles même authentifié ; `setup_demo` restreint à configuration DEBUG explicitement synthétique ; Drift coffre patient refuse les seeds de test, seuls audit vault et suites synthétiques restent possibles. Pas de déploiement Vercel ou mutation DB.

**Risques/gates** : ne pas détruire les données déjà enregistrées ; vérifier migrations et chargement du bootstrap, zéro patient réel injecté, les comptes A→B→A, auth/CSRF négatifs, navigateur Flutter Web 390/768/1280, tests exact SHA, revue confidentialité/clinique et préservation éventuelle des jeux synthétiques dans *leur sandbox*. W01/W02 non certifiés, pas de GO patient. Le précédent signal de page blanche après tests D11 doit être couvert par capture réelle et reprise d'installation PWA.

**Statut** : objet commit Git DÉTACHÉ, non publié comme branche ni PR, aucune CI supplémentaire lancée pour ne pas concurrencer L0 #1140. **NEXT** : après vérification du lot réseau L0, publier PR dédiée D11 défensive, lancer CI + captures / tests négatifs, corriger tout fail, obtenir revues, puis merge/postmerge sous gates et permission de déploiement distincte.
