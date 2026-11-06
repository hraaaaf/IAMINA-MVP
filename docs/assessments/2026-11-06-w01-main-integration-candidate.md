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
