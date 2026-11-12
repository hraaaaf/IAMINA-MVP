# IAMINA D1-6 — passkey PRF ↔ identité Django (recherche isolée)

**Date :** 2026-11-12  
**État :** CODE CANDIDAT / DRAFT — **PATIENT NO-GO**.  
**Décision unique :** vérifier côté serveur qu'un credential WebAuthn appartient au compte Django authentifié **avant** toute future autorisation d'usage de la DEK locale.

## Goal / Success / Proof

- **Goal :** supprimer l'hypothèse erronée « un `owner` au format correct est une preuve d'identité ». Les passkeys PRF chiffrent une clé locale ; elles ne sont pas, seules, une session Django authentifiée.
- **Success de la tranche de recherche :** challenge serveur à usage unique, propriétaire FK, session exacte, version de révocation, RP/origine exacts, vérification de signature + UV via la bibliothèque `webauthn`; aucune autorisation patient ni endpoint live.
- **Proof requise :** CI backend SQLite **et** PG16, migration `makemigrations --check`, 10+ négatifs (A→B→A, expiré, consommé, origine, credential étranger, absence signature, compteur), contre-audit indépendant. Un test avec vérificateur simulé n'est **pas** une preuve de cryptographie WebAuthn E2E.

## Base et périmètre

- Base : `hraaaaf/IAMINA-MVP main@d742f93e9b8678d7324d5adbfaa0ad2aced8777c`.
- PRF iPhone Preview (séparé) : `f02402ac0653933db76cc26a737717cc920aa476`; deux PASS exacts sur capture, refus Face ID et reprise observés, retour positif après réouverture.
- Prototype Django ajouté **dans des fichiers distincts** `core/d1_passkey_binding_research.py`, `core/models/d1_research_passkey.py`, migration `0021_d1_research_passkey`, tests dédiés.
- Service **jamais monté** dans `diabetes/api/main.py` ou `amina/urls.py`. Réglage `D1_PASSKEY_RESEARCH_ENABLED` absent de la configuration publiée, **false par défaut**. Aucun effet sur PWA/Flutter, App Lock, routeur clinique, sauvegarde, migration des données patients ou secrets.
- `git.deploymentEnabled: false` existant sur les trois configs Vercel ; **aucun déploiement automatique ou manuel autorisé**.

## Chaîne d'autorité visée (pas encore intégrée)

1. Authentification préalable Django `SessionAuth` avec CSRF cookie (ou futur bearer strictement vérifié). Ne jamais accepter un `user_id` fourni par le client comme autorité.
2. Le serveur crée un challenge aléatoire dans un enregistrement lié par FK au `request.user`, à sa session, au `auth_token_version`, à un RP ID/origine configurés explicitement et à une échéance de 120 s.
3. `navigator.credentials.create/get` produit une réponse WebAuthn. Le navigateur doit demander UV ; **le serveur** valide réellement le challenge, l'origine, le RP ID et la signature d'assertion via `webauthn`. Le résultat `prf.enabled` côté navigateur n'est **pas** une attestation matérielle.
4. La consommation de challenge est atomique en DB avant la vérification (un échec consomme aussi le nonce). Le credential ID est globalement unique, le propriétaire est fixé à l'inscription, les compteurs non nuls doivent progresser, un credential révoqué est interdit.
5. **Étape séparée non codée :** une fois la preuve serveur vérifiée, établir un protocole client↔serveur de déverrouillage local lié à l'identité Django courante, au changement de session/epoch et aux anciens onglets A→B→A. **Aucune clé PRF, KEK ou DEK ne doit être transmise au backend.**

## Tests (niveau de preuve honnête)

Les tests Django utilisent des comptes `User` fictifs, `BasePatientProfile` de test et un faux résultat du vérificateur uniquement dans les cas de preuve d'orchestration. Ils démontrent les comparaisons et refus du service, mais **pas** :
- la signature ECDSA réelle d'une passkey physique ;
- la résistance XSS ou au compromis d'un script de même origine ;
- l'invalidation de toutes les opérations JS in-flight après logout ;
- la conformité d'une ouverture de coffre SQLite3MC/Drift ni le retrait des vieux coffres en clair ;
- l'attachement réel `request.user`↔`session_key` dans une route Django-Ninja intégrée ;
- un fonctionnement authentifié sur iPhone avec le backend.

## Risques et critères d'arrêt

**BLOCKER :** la configuration RP ne doit jamais accepter de wildcard ou dériver automatiquement l'origine d'une requête ; les URL Vercel immuables successives sont des origines différentes, les anciens credentials ne sont donc pas interchangeables.

**BLOCKER :** un login Django seul ne doit jamais fournir la DEK ; la preuve WebAuthn ne doit jamais suffire pour se connecter à une identité Django étrangère ; aucune réutilisation de challenge ou de credential révoqué.

**BLOCKER :** le modèle n'a pas d'API publique, pas de token de session émis et n'autorise pas le coffre patient. Toute intégration doit être d'abord vérifiée en Preview **uniquement après une autorisation Vercel distincte**.

## Next exact

1. Résoudre CI / migrations / Bandit / Ruff / PostgreSQL et revue adversariale sur le SHA final du candidat.
2. Préparer l'adaptateur HTTP Django-Ninja **dans une prochaine tranche distincte** avec CSRF, cookie/bearer anti-collision, sessions A→B→A, tests réels HTTP et révocation in-flight.
3. Ajouter test réel de signature `webauthn` + certificat d'absence de fuite PRF sur navigateur, puis revue cryptographique indépendante.
4. Conserver D1 PATIENT NO-GO, PR Draft et zéro Vercel tant que les gates n'ont pas de preuves.

**Notion canonique :** [01 — ROADMAP CANONIQUE](https://app.notion.com/p/3df77c66336281f5b308ec17f7f0a63b). Aucun document de roadmap concurrent n'est créé.
