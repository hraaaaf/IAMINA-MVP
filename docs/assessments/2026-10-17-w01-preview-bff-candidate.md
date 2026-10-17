# IAMINA W01 — Candidat Web Preview BFF same-origin — 17/10/2026

## Goal, réussite et preuve attendue
Éliminer le fetch cross-origin depuis Flutter Web Preview vers Django sous SSO sans rendre l'API publique, sans fuite d'un bypass vers le JS navigateur, sans impacter Production. Succès uniquement si Chrome authentifié démontre Web→proxy same-origin→API protégée→Neon synthétique, Web SSO et API SSO actifs, cas négatifs, CORS/CSRF/auth, traces assainies et revue indépendante. Aucune affirmation de succès sans cette preuve.

## BEFORE
- Chrome non authentifié : 3 GET + 1 OPTIONS vers l'API Preview ; Fetch TypeError ; `MissingAllowOriginHeader` (deux GET), `PreflightDisallowedRedirect` (OPTIONS). [Run #39043002484](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/39043002484). 
- API Preview SSO actif, Web Preview SSO était inactif, API direct sous domaine distinct ; Django /health HTTP 200 uniquement via accès propriétaire.
- Production et Neon patient inchangés.

## Mesure effective séparée
- Vercel `iamina-review` a reçu `ssoProtection: {deploymentType:'preview'}` le 17/10, relu `enabled=true`, portée Preview ; l'API `iamina-certified` garde son SSO. Derniers déploiements Preview existants inchangés, pas de nouvel artefact.

## Proposition code isolée en PR
- Conserve les deux projets de l'ADR W01. Une fonction Node.js `frontend/api/preview-proxy.js` strictement Preview uniquement est ciblée par une rewrite `/api/v1/:path*` **avant** le fallback Flutter.
- Flutter Preview prend `Uri.base.origin` à l'exécution (même origine) ; production conserve la configuration antérieure.
- Proxy fixe **un hôte API Preview synthétique exact**, vérifie Vercel target/ID projet/Host/Origin, rejette traversal, redirects, méthode inconnue, contenu trop volumineux ; transfère uniquement des en-têtes expressément autorisés et **jamais** Cookie/Host/Origin/x-* client, refuse caches, masque les erreurs. Le secret bypass éventuel est lu uniquement en runtime Node (`IAMINA_W01_API_PROTECTION_BYPASS`) et l'absence de secret donne HTTP 503 ; aucune valeur de bypass n'est créée ou embarquée dans le dépôt.
- Protection Django/Bearer demeure obligatoire pour les ressources médicales. **La confiance au SSO Web en amont est une condition de déploiement, non une assertion prouvée par tests unitaires.**
- Limitation : Vercel Functions plafonne les tailles de corps requête ; proxy candidate limite à 4 MiB et ne valide pas les uploads médicaux de 15 MiB. G5 reste ouvert, ne pas utiliser pour patients.

## Préflight nécessaire avant Preview
1. Revue indépendante du code, tests GitHub Node/Dart Flutter et règles de routing réellement résolues par Vercel (les gardes statiques ne suffisent pas).
2. Examiner la portée **project-wide** des tokens d'automation bypass Vercel et leur possible accès Production ; réduire le droit au strict Preview ou concevoir autre mécanisme serveur. Ne pas provisionner un bypass de portée Production pour résoudre un problème Preview.
3. Vérifier SSO Web Preview actif et origine d'accès requise. Aucun bypass navigateur, aucune ouverture de l'API.
4. Seulement après validation de ces gates, déploiement Preview isolé autorisé puis tests E2E, contrôle négatif non-authentifié, contrôle d'absence de données patients, tests échecs/rollback et preuves.
5. W01-G4/G5/G6/G7 + revue indépendante restant à clôturer ; W02 gelé.

**Statut : PROTOTYPE CANDIDAT NON DÉPLOYÉ, W01 NO-GO, W02 GELÉ.**
