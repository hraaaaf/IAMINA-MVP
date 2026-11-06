# IAMINA W01 — Candidat d'intégration main, 06/11/2026

**Statut : CANDIDAT ISOLÉ, NON CERTIFIÉ. Aucun GO clinique, aucun merge sur main, aucun déploiement Vercel.**

## But et base exacte
Parents du merge de travail : W01 `357fd6b4978a307713b13e0194f60a4be9074621` et main `2f1bb986eb0ef778a8ac9edb040208cc36084803`. Runtime Web W01 précédemment testé `31c7b057d76dc757a575047d36eec799773d5174` (18/18 CI SUCCESS) ; cette preuve NE s'applique PAS automatiquement au merge candidat. La divergence initiale est de 52 commits W01 et 2 commits main.

## Résolution des six chemins recoupés
- `login_screen_fr_certified.dart`, `login_screen_mena.dart`: fusion par hunks non chevauchants, garde `syntheticLoginOnly` W01 conservée, nouveaux chemins de logo V4 et styles main conservés.
- `local_device_enrollment_screen.dart`: garde d'enrôlement W01 avec logo V4 main.
- `test_pilot_consent_governance.py`: fixture temporelle main et test main de rejet de preuve périmée conservés ; test W01 de rejet de commande live également conservé.
- `test_pilot_release_provider_scope.py`: version main, tests de dates et refus conservés, différences W01 seulement dans la fixture historique équivalente.
- `d7_web_actual_profile_e2e.py`: version W01 conservée, assertions explicites de sélection mg/dL et navigation.

Les 28 autres chemins ajoutés/modifiés par main sont repris au SHA de blob de main (logos, tests V4, PWA/service worker). **Attention :** `frontend/vercel.json` de W01 ajoute une réécriture `/api/v1/:path*` vers le proxy BFF ; sa version W01 est conservée, car cette fonctionnalité manque dans main. Tous les fichiers Vercel gardent `git.deploymentEnabled=false`.

## Critères de clôture encore exigés
CI au SHA exact de ce candidat : tests backend gouvernance, W01 G7 FR/AR A→B→A en navigateur réel avec PG16 éphémère, authentification/CSRF/401/403/404, D7 Chrome, D8 unité, branding V4, PWA/service worker. Revue indépendante appropriée des risques sécurité et privacy, vérification éventuelle hosted Web→BFF→API→Neon et résultat postmerge après approbation. G2 waived W01 développement, G6 reporté préproduction, G7 développement déjà PASS au code précédent. Production clinique demeure NO-GO et aucun handover W02 avant fermeture intégrale W01.


## 06/11/2026 — Intégration W01 et recette hébergée confirmées (audit au 18:09 UTC)

**Décision de fusion : exécutée** sur autorisation explicite du propriétaire, après audit du `main` réel. L'avertissement « main a évolué » a été traité par lecture de la branche : base `2f1bb986eb0ef778a8ac9edb040208cc36084803`, incluant les changements V4 logo du 06/11 ; branche W01 `1e8580a5ab331abfd7767cbf391cf421700ddf90` **57 commits ahead, 0 behind** et mergeable. **PR #1276 MERGED** le 06/11, `main` au commit de merge **`782c04bffb5aab5aaf156f4b30ece2274a1d1652`**, parents exacts base+W01. Les fichiers de sécurité/auth/proxy importants ont été comparés par SHA de blob et sont strictement identiques entre W01 testé et main fusionné.

**Preuves sur le SHA applicatif validé `1e8580a5` :** GitHub **19/19 workflows COMPLETED/SUCCESS** (D11 routed FR/AR PostgreSQL16, G7 A→B→A Flutter Chrome FR/AR, CI Ruff/pytest, PostgreSQL source-of-truth, Flutter/PWA, navigateur 390/768/1280 et packaging). Vercel **Web Preview** `dpl_GEQ1JMmgj7FKE4B1YPAyV2yzMPDV` READY et **API Preview** `dpl_5xd1uEjEASsnFGSYCvnPnGpJS9Wc` READY, au SHA exact ; liaison Web→API Preview dédiée, SSO conservé. Le propriétaire a ensuite déclaré **« C bon tout marche ! »** après la demande de test A→logout→B→logout→A : **recette fonctionnelle hébergée PASS déclaratif**, pas une trace réseau instrumentée, pas un GO clinique.

**Contrôle des déploiements :** `git.deploymentEnabled=false` dans les trois fichiers `vercel.json`; les 92 workflows GitHub ont été inspectés sans commande de déploiement Vercel trouvée. Le contrôle Vercel des déploiements sur le SHA fusion `782c04b` retournait zéro résultat ; aucun déploiement Vercel n'a été demandé. Une fusion GitHub et un déploiement Production sont **des opérations distinctes**.

**Statut des gates postmerge à l'instant de cet addendum :** 9 workflows de push sur `782c04b` étaient **QUEUED**, non encore validés ; le simple 19/19 prémerge **ne vaut pas** preuve postmerge. Suivi GitHub : https://github.com/hraaaaf/IAMINA-MVP/actions?query=branch%3Amain ; PR https://github.com/hraaaaf/IAMINA-MVP/pull/1276 ; statut Notion https://app.notion.com/p/3fc77c66336281ab8bfcf0c6b0060e2f . **Next :** lire verdicts postmerge et vérification Vercel, documenter les résultats exacts, puis seulement déclarer W01 complètement clos / préparer W02.

**Limites invariantes :** développement Web synthétique seulement. G2 waived développement ; G6 reporté préproduction, G7 FUE développement PASS. Aucune validation de restauration indépendante ni de conformité/Production de données médicales réelles, aucun déploiement clinique.
