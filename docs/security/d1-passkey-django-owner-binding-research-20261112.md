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
- Prototype Django ajouté **dans des fichiers distincts** `core/d1_passkey_binding_research.py`, `passkey_research/models.py`, migration isolée `passkey_research/0001_initial`, tests dédiés, et routeur HTTP monté **seulement** sous `core/tests/d1_passkey_test_urls.py`.
- Service **jamais monté** dans `diabetes/api/main.py` ou `amina/urls.py`. Un adaptateur Django-Ninja **de test** exige session cookie + CSRF et rejette l'en-tête Authorization ; le routeur demeure non exposé sur l'application réelle.
- **Correction architecture :** la première tentative stockait des `BinaryField` dans `core`, ce qui a fait échouer le contrat relationnel (`2966 pass, 1 fail`) ; la correction préserve ce contrat sans l'assouplir : les seuls octets d'authentification (clé publique, challenge, handle) sont dans une application de stockage **strictement dédiée aux credentials**, `passkey_research`, sans données cliniques, avec FK aux utilisateurs. La migration initiale dans `core` a été retirée de la branche avant toute fusion ou migration réelle. La nouvelle app exige une revue de cycle de vie, purge, protection et stockage avant mise en service. Réglage `D1_PASSKEY_RESEARCH_ENABLED` absent de la configuration publiée, **false par défaut**. Aucun effet sur PWA/Flutter, App Lock, routeur clinique, sauvegarde, migration des données patients ou secrets.
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
- le branchement de l'adaptateur HTTP de test sur l'API de production (interdit dans cette tranche) ; les scénarios Django Client de session réelle/CSRF/A→B→A peuvent vérifier le routage dans l'URLconf isolée, sans démontrer un parcours physique iPhone signé ;
- un fonctionnement authentifié sur iPhone avec le backend.

## Risques et critères d'arrêt

**BLOCKER :** la configuration RP ne doit jamais accepter de wildcard ou dériver automatiquement l'origine d'une requête ; les URL Vercel immuables successives sont des origines différentes, les anciens credentials ne sont donc pas interchangeables.

**BLOCKER :** un login Django seul ne doit jamais fournir la DEK ; la preuve WebAuthn ne doit jamais suffire pour se connecter à une identité Django étrangère ; aucune réutilisation de challenge ou de credential révoqué.

**BLOCKER :** le modèle n'a **aucune API patient montée** (l'URLconf de test est privée à `pytest`), pas de token de session émis et n'autorise pas le coffre patient. Toute intégration doit être d'abord vérifiée en Preview **uniquement après une autorisation Vercel distincte**.

## Propriété du stockage et limites restantes

Les `BinaryField` sont exclus du modèle patient par contrat repository, mais le stockage WebAuthn a besoin d'octets de clé publique, challenge et handle. La séparation `passkey_research` est une frontière de données **non cliniques**, non une exemption de sécurité. Les tables restent sujettes à politique de rétention, contrôle d'accès, suppression sur effacement compte, limitation de taille et migration auditée. Le credential seul n'authentifie personne à la clinique.

## Next exact

1. Résoudre CI / migrations / Bandit / Ruff / PostgreSQL et revue adversariale sur le SHA final du candidat.
2. Vérifier la suite de tests Django Client/CSRF/A→B→A du **routeur isolé**, puis, dans une tranche distincte et après revue, définir un protocole intégré de sessions réelles, auth epoch et révocation in-flight (l'API patient demeure non montée).
3. Ajouter test réel de signature `webauthn` + certificat d'absence de fuite PRF sur navigateur, puis revue cryptographique indépendante.
4. Conserver D1 PATIENT NO-GO, PR Draft et zéro Vercel tant que les gates n'ont pas de preuves.

**Notion canonique :** [01 — ROADMAP CANONIQUE](https://app.notion.com/p/3df77c66336281f5b308ec17f7f0a63b). Aucun document de roadmap concurrent n'est créé.

## D1-6 HIGH / adversarial correction candidate — 2026-11-12

**State: CODE CANDIDATE / NO-GO, tests and independent review pending.** This section does not certify deployment or patient access.

### BEFORE / AFTER (candidate, not certification)

| Issue | Before on `cc9936c` | Candidate correction | Required regression |
|---|---|---|---|
| HIGH — stolen cookie enrolling credential | Valid Django session alone started enrollment | Fresh Django password verified against current user + persistent account-scoped attempt limiter (10 per 10 minutes); passwordless identity fails closed | HTTP absent/wrong password, rate limit, A→B→A |
| HIGH — logout in-flight | Old request could use prior `user` and session key without reloading server session | Session engine backend re-read, current Django auth-hash checked at start and commit; stateless cookie sessions denied; account epoch locked during writes | Real Django logout during mock signature, expired/rotated session |
| HIGH — credential mutation | No research revoke method with fresh proof | Owner-only credential revoke, Django password step-up, revocation epoch and credential row locks, `revoked_at` persistence | Foreign/revoked credential, bad password, replay |
| HIGH — account recovery/device compromise | No cryptographic binding to real vault | **NOT FIXED** — PRF, DEK and encrypted local vault still separate from this service | Safari/iPhone physical E2E, XSS, old PWA, multi-tab, account recovery |

### Web/PWA integration protocol to implement (no patient route activated)

1. Resolve the current user exclusively from the authenticated server-side Django session and current revocation epoch, with cookie + CSRF and an explicit deny of conflicting Authorization. Never trust a client-provided `owner`, email, session ID or RP/origin.
2. Before every enrollment or credential mutation require recent account reauthentication through the password-verified research step-up or a separately audited equivalent (for passwordless accounts, fail closed until an independently validated mechanism exists). Limit attempts in persistent storage.
3. WebAuthn options are server-generated: origin and RP ID fixed by server configuration, random challenge 32 bytes, short TTL, atomic one-time consumption, UV required, globally unique credential ID. Verify assertion signature and authenticator data server-side against the stored account credential; reject foreign/revoked credentials.
4. The future client Web PRF flow computes KEK and unwraps synthetic DEK **only on the client** after actual UV. Neither PRF results nor KEK/DEK shall be included in requests/responses, logs, telemetry or crash traces. A PRF browser extension claim is not a server-side hardware attestation.
5. The browser owns a session generation/token scoped to the account, credential, origin and active tab. Every logout, Django identity change, revocation, BFCache restore, cross-tab signal or late asynchronous result invalidates the local generation, drops unwrapped keys and forces new Django + WebAuthn gates; re-entering A after B never reuses A's previously unwrapped DEK.
6. Future local encrypted vault envelopes must use authenticated encryption and bind account/credential identifiers as authenticated associated data; no silent legacy reattribution, no cleartext DEK persistence, no automatic migration. Recovery and backup require an explicit separately reviewed key-rotation policy.

### Proof boundary

- Current service and HTTP test suite may demonstrate Django/SQLite and PG16 isolation, revocation and fail-closed control flow; mocked `verify_*` returns cannot prove WebAuthn signature math or physical Face ID.
- A real iPhone passkey/PRF fixture from a **different** PR/SHA is not a Django↔PRF↔vault end-to-end test. Chromium virtual authenticators and WebKit stubs are likewise not physical-device certification.
- `D1_PASSKEY_RESEARCH_ENABLED` remains absent/OFF; all added endpoints are mounted only by the test URLconf. No patient data, clinical API mutation, physical migration, Vercel Preview or merge authorized.
- Required before VERIFIED: independent cryptography/security review at exact final SHA, real browser/device evidence, account A→B→A with encrypted vault, logout and in-flight plus multi-tab, persisted key recovery without Face ID bypass, no HIGH/CRITICAL open, and all exact-SHA CI gates green.
- Developer portability and Pulper Golden Corpus remain distinct potentially-red gates. Do not infer their status from the backend CI result.
