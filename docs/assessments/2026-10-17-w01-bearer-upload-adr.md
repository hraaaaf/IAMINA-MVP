# IAMINA W01-G5 — Identité Web Bearer et documents privés : décision candidate (17/10/2026)

## Périmètre et état

Base d'analyse : PR #1128 avant correctif `46902848bb501ee67de6dddaf0b0529436d0b768`. La Preview Web utilise une fonction Node same-origin qui ne transmet aucun cookie Django/SSO, Origin ou X-CSRFToken à l'API ; seule l'authentification IAMINA Bearer est candidate. Django dispose simultanément de `HybridBearerAuth` et de `SessionAuth`. **SSO Vercel n'est pas l'identité patient.** La liaison OIDC Trusted Sources Preview→Preview n'est pas prouvée (historique HTTP 404).

## Contrat d'identité P1 (limité à Preview)

| Phase | Invariant exigé | Preuve |
|---|---|---|
| Login | POST `/api/v1/auth/login`, puis `access_token` IAMINA natif, sans dépendre du cookie Django | Test Django login puis nouveau client sans cookie |
| Requête protégée | `Authorization: Bearer iamina.…`, identité issue exclusivement du jeton vérifié côté Django | Tests `/auth/me` A→B→A |
| Expiration/altération | 401, sans identité de secours ni promotion de SSO Vercel | Test négatif expiration/signature |
| Logout | Effacement local synchrone, demande de révocation Bearer côté Django, ancien jeton refusé ensuite | Test API token révoqué + test Dart existant ; navigateur hébergé OPEN |
| Session Django | Cookie + CSRF pour opérations mutantes, préservé côté Django ; **non supporté par ce BFF** | Test session sans CSRF = 403 |
| Réponse BFF | 401/403 Django non reclassifiés en succès, ni cookie SSO/CSRF transmis ; refus HTML/redirect | CI Node synthétique existante ; tests négatifs additionnels souhaitables |
| Isolation médicale | A n'accède jamais au contenu B (y compris mutation, offline/sync et uploads) | Identité A→B→A partiellement testée ; endpoints médicaux et hosted E2E **OPEN** |

**Recommandation :** limiter W01 Preview au Bearer natif et afficher clairement la non-prise en charge du mode SessionAuth via le BFF. Ne pas créer un pont de cookies Vercel vers Django. Ne pas certifier la confidentialité patient par un seul test d'identité.

## P2 — Écart documents médicaux

**Constat :** le Flutter/backend acceptent jusqu'à 15 MiB et le BFF impose une limite effective de 4 MiB. Augmenter le proxy au-dessus de 4 MiB est exclu : limite de corps des fonctions Vercel (~4,5 MB selon documentation officielle au moment de la conception). Aucune donnée patient réelle utilisée pour cette étude.

| Option | Architecture | Forces | Risques / coût | Verdict |
|---|---|---|---|---|
| A — uploads fractionnés via Django/BFF | Segments sous 4 MiB, session d'upload serveur, somme finale, vérification et finalisation atomique | Réutilise potentiellement le stockage backend | Nombreuses écritures serverless, états intermédiaires, replay, concurrence, coûts et recovery ; architecture inconnue | Ne pas implémenter sans prototypage + tests de charge |
| B — upload privé direct autorisé par Django | Django authentifie patient+but, retourne autorisation brève liée à objet privé/patient, navigateur transfère directement au stockage approuvé ; Django vérifie empreinte, taille, type et état avant activation | Évite la limite de corps du BFF et sépare contrôle patient / transfert volumineux | Nouveau flux egress/stockage, CORS, anti-rejeu, résidence, chiffrement, coût, purge et consentement ; fournisseur non choisi | **Option cible recommandée, sous gates de sécurité/compliance** |
| C — augmenter le plafond BFF à 15 MiB | Envoyer l'intégralité via Node Function | Simple seulement en apparence | Incompatible avec les limites Vercel, risque OOM et de faux succès | **REJETÉE** |

### Contrat obligatoire de l'option B avant code

1. Initialisation : Bearer IAMINA validé côté Django ; identité serveur dérivée du jeton ; type, taille maximum, usage et propriétaire liés à un upload ID imprévisible, TTL court et one-shot.
2. Objet isolé et privé par patient ; clés d'objet construites serveur, jamais proposées par le client ; permission minimale d'écriture vers un seul objet, aucun listing public ; pas d'identifiant patient explicite dans l'URL.
3. Flux stocké dans une zone de quarantaine, CORS restrictif, validation serveur de taille/empreinte/MIME/contenu, antivirus si applicable, atomicité de finalisation ; aucune création clinique avant contrôle.
4. Rejeu, transfert incomplet, timeout, révocation, changement de patient A→B, concurrence et orphelins : refus fail-closed et purge programmée vérifiable. Journaux sans payload médical, sans URLs signées ni tokens.
5. Cas limites : 0, 4, 4+ et 15 MiB ; uploads parallèles A/B ; extension mensongère, objet différent, somme incorrecte, dépassement de TTL, lien réutilisé, perte réseau.
6. Gate juridique/sécurité : résidence et sous-traitants, consentement/purpose, chiffrement, rétention, coûts, modèle de restauration ; architecture certifiée par reviewers indépendants.

**Décision actuelle :** ne pas sélectionner de fournisseur ni activer les documents 4–15 MiB tant que ces gates ne sont pas étudiés et éprouvés. Conserver le plafond 4 MiB pour les appels BFF existants ; toute UI de documents Preview doit empêcher de promettre un upload 15 MiB fonctionnel.

## Human gate et preuves absentes

- Vercel `iamina-certified` Trusted Sources autorisant uniquement `iamina-review:preview → iamina-certified:preview`, lecture retour de règle, OIDC éphémère non exposé : **OPEN / action propriétaire**.
- Validation de la fonction réelle, Chrome SSO → BFF → Django → Neon synthétique, 401/403 et A/B : **OPEN**.
- Test PostgreSQL 16 exact HEAD, revue sécurité indépendante, G4–G7, restore distant, release-certifier, closeout et merge : **OPEN à recontrôler**.
- Aucun déploiement Vercel, migration Production ou traitement de données patients réelles autorisé dans ce lot.

**GOAL** : Web Preview sans confusion de privilèges. **W01 NO-GO ; W02 GELÉ** tant que les gates ci-dessus restent ouverts.
