# IAMINA W02/D10 — staging W01-compatible, 28 octobre 2026

## Goal
Certifier sur Preview (pas Production) l'ancre serveur Option A en respectant le schéma W01/D2. Périmètre d'abord CI isolée PostgreSQL 16 + Chrome, ensuite Preview exacte, uniquement lecture tant que Neon indépendant n'est pas disponible.

## Préparation
Base Git W01/D2 `84ac2ccc30957be00b29c9b4445406310dd92668` ; composants synthétiques W02 `86738a4d06e4bd09f45fafd1c56ec56fbb611300` copiés sans écraser le BFF, l'AuthService, les routes ou les composants UI W01. Migration W02 devient `core.0024_w02_vault_revision_anchor` dépendant de `0023_d2_in_app_notice`, et non la `0020` divergente. Le garde patient `encrypted_web_patient_vault_unavailable` reste inchangé.

**Blocage externe :** Neon `noisy-truth-00115950` refuse une branche dédiée supplémentaire (`branches limit exceeded`). Ne pas effacer de branche existante, toucher à Production ou appliquer de migration sur le parent synthetic-only partagé sans vérification et autorisation appropriée. W02 REST Preview reste OFF par défaut. Cette branche est créée pour permettre le build/health/deny E2E sans patient ni écriture réelle.

## Critère de succès
Tests CI Python PG et Flutter Chrome exact-SHA ; Vercel two-project Preview READY ; vérification identité SQL sur base indépendante avant tout test d'écriture ; tests A→B→A, antirollback, cleanup et SQL zéro ; audit sécurité indépendant avant GO patient. Ne pas prétendre complet sans preuve. Fichier canonique de reprise.

## Sécurité vérifiée : écart W01 Web

La base W01/D2 utilisait encore `driftDatabase(web: DriftWebOptions(...))` dans `AppDatabase.forPatientVault`. Le test W02 a correctement échoué au contrat de protection. Correctif **uniquement sur staging** : helper `_w02ProtectedPatientVaultExecutor` rejette `kIsWeb` avec `encrypted_web_patient_vault_unavailable` avant création de la base patient. Chemin Native inchangé. **Attention :** `AppDatabase.defaults()` reste un chemin legacy Web pouvant créer du SQLite navigateur non chiffré. L'ensemble de l'app n'est pas certifié, et aucune donnée patient réelle ne doit passer par ce chemin. Ce staging permet uniquement preuve de build, deny et intégrations synthétiques ; pas d'activation Web patient. Go conditionné à inventaire des consommateurs de `defaults()` et suppression de tout stockage clinique plaintext.


## Deployment Preview attesté — 28/10/2026 (après code SHA 1e2a2409)

- **Code/build SHA :** `1e2a24092f7f58d690f575709e5aed1b4216c3df`, staging fork uniquement, branch `feat/w02-d10-option-a-w01-preview-20261028`. `main` / W01 integration / W02 initial non fusionnés.
- **API Vercel Preview :** `iamina-certified`, deployment `dpl_5WYwKTfkXQG6ZiUErejXHAzEoHqM`, READY, URL `https://iamina-certified-b74eac8ia-achraf-benmoussa-s-projects.vercel.app`. Protection SSO conservée. W02 flag absent → *OFF*. Aucune migration Neon.
- **Web Vercel Preview :** `iamina-review`, deployment `dpl_23hdDJqMQWmdFS8GTMEo8kLuRPnv`, READY, URL `https://iamina-review-abtkl3ybg-achraf-benmoussa-s-projects.vercel.app`. Projet et SHA exacts vérifiés. Variable `IAMINA_REVIEW_PREVIEW_API_BASE_URL` strictement limitée à cette branche Preview et à cet exact déploiement API. Aucune activation du login synthétique/inscription distante.
- **SQL cible indépendante et lecture seule :** Neon projet `noisy-truth-00115950`, branche `br-sweet-frog-b9ok6ptp`, base `iamina925_empty`, rôle `iamina_preview_app`, `auth_user=0`, `to_regclass('public.core_w02vaultrevisionanchor') IS NULL` avant/après déploiement. Aucun schéma ni compte patient modifié. Neon `create_branch` retourne `branches limit exceeded`. Ne pas supprimer/repurposer une branche Neon ancienne sans approbation.
- **CI Postgres 16 (éphémère GitHub Actions) :** [#40731783684](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/40731783684) SUCCESS, 8/8 Node, 10/10 Python PostgreSQL, `makemigrations --check --dry-run` = No changes detected, `core.0024` appliquée à la DB CI seulement.
- **CI Chrome :** run [#40732061792](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/40732061792) QUEUED au dernier contrôle. Un run précédent [#40731783604](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/40731783604) a échoué correctement : l'ancien W01 `forPatientVault` était un chemin IndexedDB non chiffré. Correctif sur staging : `encrypted_web_patient_vault_unavailable` à l'ouverture Web de `forPatientVault` seulement. Nouvelle preuve Chrome non encore obtenue.
- **Protection restante :** `AppDatabase.defaults()` Web reste un chemin legacy non chiffré et n'est pas certifié pour données patients ; produit D10 patient **NO-GO**. Les fixtures JS et Drift WASM sont test-only. Ne pas confondre READY Vercel et E2E clinique.

**Goal atteint :** deux artefacts Preview exact-SHA compilés/READY et migration compatible vérifiée en CI, pas Production. **Goal NON atteint :** E2E Web → BFF → API → Neon sur DB indépendante avec cleanup SQL indépendant, clé et durable recovery, absence de chemin plaintext global, tests app-lock BEFORE/AFTER, audit sécurité indépendant.

**Next exact :** résoudre quota Neon via décision humaine sur archivage ou capacité ; créer branche QA neuve, vérifier quatre identifiants et les privilèges, y appliquer `core.0024` sur QA uniquement, autoriser explicitement `IAMINA_W02_REVISION_ANCHOR_ENABLED=true` uniquement sur nouvelle branche Vercel et exécuter E2E A→B→A/crash puis nettoyage SQL zéro. Si quota non résolu, poursuivre Chrome CI et code sécurité sans données patients. Aucun merge ni Production GO.


## Closeout complémentaire exact-SHA — 28/10/2026

**CI Chrome finalement VERTE** : [GitHub Actions #40732061792](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/40732061792) **SUCCESS** au code `1e2a24092f7f58d690f575709e5aed1b4216c3df`, job `122970703740` : **63/63 Node PASS**, **15/15 Flutter Chrome PASS**, `flutter analyze --fatal-infos` = **No issues found**. Test navigateur inclut les octets SQLite Drift/Flutter → JS WebCrypto AES-GCM → IndexedDB ciphertext-only et restauration, l'adaptateur d'identité native mockée, le refus du mauvais compte et de l'ancienne révision. Le garde de la base patient Web non chiffrée est rétabli au SHA exact. Ce vert n'est pas un E2E hébergé authentifié.

**Deux Preview Vercel READY, même SHA code**, preuve indépendante via les deux IDs de déploiement déjà consignés ; logs Web = `✓ Built build/web`, origine `https://invalid.iamina-preview.invalid` interne (le BFF même origine est requis). Domaine API authentifié par Vercel SSO, pas de bypass ou de désactivation de protection. Une tentative de consultation HTTP publique non authentifiée n'a pas fourni de réponse exploitable, donc **pas de prétention de vérification API par requête réelle**.

**PR revue** : [#1158](https://github.com/hraaaaf/IAMINA-MVP/pull/1158), **DRAFT**, base `integration/w01-d2-preview-only-20261027`, GitHub `mergeable=true`, `mergeable_state=clean` lors de vérification. Aucun merge.

**SQL post-déploiement indépendant** : Neon sandbox `iamina925_empty` rôle `iamina_preview_app`, `auth_user=0`, `core_w02vaultrevisionanchor` absent ; aucune mutation de données/DDL en cloud. Les branches supplémentaires sont refusées par quota. L'E2E hébergé avec vraies créations synthétiques exige une nouvelle base QA isolée ; interdiction de contourner par le parent partagé ou Production.

**Bilan Goal / preuve :** staging compatible migrations et deux déploiements Preview exact-SHA atteints ; tests isolés PG & Chrome verts ; NO-GO patient et E2E Neon non atteint. **Human gate réel :** libérer un slot Neon par suppression ciblée d'une branche QA explicitement autorisée (après vérification de son utilité), ou augmenter quota ; puis exécuter les étapes d'isolement/migration, A→B→A/crash, nettoyage SQL zéro, audit sécurité indépendants. Nulle fusion, déploiement Production ou activation de données médicales n'est autorisée par ce closeout.


## Préparation quota Neon — choix humain précis (28/10/2026)

Vérification via `list_branches`, `get_branch`, `list_branch_computes`, et recherche de références GitHub : Neon sandbox `noisy-truth-00115950` contient 10 branches, et `create_branch` retourne `branches limit exceeded`. Meilleure candidate pour **demander** une suppression ciblée : `br-spring-hat-b9hm0c47`, `w01-endpoint-swap-holding-20261021`, créée 21/10, dernière mise à jour 21/10, `default=false`, `primary=false`, `protected=false`, aucun compute associé, aucun enfant dans la liste Neon du 28/10, aucune référence trouvée par recherche de code GitHub sur la branche par défaut. **Ce dernier contrôle n'est pas une preuve absolue d'absence d'usage externe ni de valeur de reprise**. Ce candidat est dérivé de `br-lingering-shape-b9gh0xn6`, elle-même une branche de preuve de restauration. Il pourrait donc servir d'ancien point de récupération ; la suppression est définitive et exige un GO humain nominatif.

Branches à **préserver** sans examen/GO spécifique : défaut `br-sweet-frog-b9ok6ptp` ; `br-royal-wave-b9d5eaw1` QA D2 récente avec compute ; `br-delicate-truth-b9jwiqfd` photo pré-cleanup G5 ; `br-soft-rain-b9bs5and` photo pré-migration D2 ; `br-sweet-mountain-b9skxry9` sauvegarde pré-0036 ; `br-autumn-*` et `br-lingering-shape-b9gh0xn6` reprises G6. Snapshot Neon existant `snap-orange-mode-b9tjsdd1` sur défaut, **pas une sauvegarde vérifiée de la branche candidate**. Ne pas le présenter comme tel.

**Human gate :** autoriser explicitement « supprimer uniquement `br-spring-hat-b9hm0c47` du projet `noisy-truth-00115950` ». Avant l'action, relire le détail et l'absence d'enfant; STOP si la cible ou l'usage ont changé. Si GO, supprimer cette branche seulement, puis créer `w02-d10-option-a-preview-qa-20261028`, vérifier les quatre identifiants de connexion isolée, et seulement ensuite poursuivre migration `0024`, E2E, révocation, cleanup et SQL `auth_user=0`. Aucune écriture Production.


## Supersession vérifiée — W02/D10 Web guest boot AFTER — 28/10/2026

**Portée / Goal exact :** rendre le Web Preview accessible à l'invité SANS ouvrir de coffre patient Web en clair. Ce closeout **supplante** les anciens constats « quota Neon à résoudre », « W02 Chrome encore queued » et « legacy Web toujours ouvert au boot ». Le quota QA a été résolu par création d'une branche spécifique, mais la migration QA n'a PAS été faite.

### Correctif source (GitHub)

- **Code commit exact :** [`3903f5e42b2abdb9dc829dfd677ab0edc6ed858d`](https://github.com/hraaaaf/IAMINA-MVP/commit/3903f5e42b2abdb9dc829dfd677ab0edc6ed858d), branche `feat/w02-d10-option-a-w01-preview-20261028`, [PR #1158](https://github.com/hraaaaf/IAMINA-MVP/pull/1158) DRAFT, **non mergée**.
- `PatientVaultAppHost.initState` invité ouvre désormais `AppDatabase.guestAuditOnly()` en mémoire SQLite WASM sur Web. Le garde `AppDatabase.forPatientVault` continue à lancer `encrypted_web_patient_vault_unavailable` sur Web patient non chiffré. `main.dart` ne déclenche plus `AppDatabase.defaults()` legacy plaintext au démarrage Web.
- **Risques résiduels :** `AppDatabase.defaults()` reste un constructeur possible ailleurs ; le statut Web `legacyProtected=true` impose une récupération app-lock conservatrice et n'est pas validé par un parcours de première authentification. Aucune donnée patient clinique prête pour Production.

### CI exact-SHA et observation BEFORE/AFTER

- [GitHub #40747416807](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/40747416807) **SUCCESS** : 4 tests statiques source, analyse Flutter ciblée, compilation release Web du vrai `main.dart`, vrai Chrome guest WASM volatile/recréation sans lignes, et refus `forPatientVault` Web patient.
- [GitHub #40747416583](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/40747416583) **SUCCESS** : garde WASM et 3 tests Chrome mémoire synthétiques.
- **BEFORE** [TinyFish `55ccac03-81c5-4de4-b85e-afec0d0babcc`](https://agent.tinyfish.ai/runs/55ccac03-81c5-4de4-b85e-afec0d0babcc) : code Preview antérieur `1e2a2409`, `flutter-view` présent mais écran gris/blanc et login absent après attente → **FAIL**.
- **AFTER** [TinyFish `5fa9f5bc-a4d8-4f07-abed-d12f9cf755e5`](https://agent.tinyfish.ai/runs/5fa9f5bc-a4d8-4f07-abed-d12f9cf755e5) : Web Preview `dpl_5UAZBrbp47y6dUd6KVHkhx52yXPH`, commit `3903f5e4` READY ; URL finale `/#/login`, écran « Set up IAmina here » et bouton « Set up this device » réellement visibles, pas d'écran blanc → **PASS**. Même navigateur TinyFish *lite* demandé ; pixels/viewports chiffrés des captures non obtenus, ne pas présenter une comparaison géométrique pixel parfaite. **Score d'acceptation visuelle sur le seul critère boot : PASS (1/1).** Aucun compte, formulaire ni donnée patient ; pas d'E2E authentifié.
- Préviews maintenues en SSO. Lien d'accès temporaire pour TinyFish révoqué via API Vercel ensuite. Aucun déploiement de l'API ni de Production.

### QA Neon : gate toujours BLOQUÉ

- **Projet** `noisy-truth-00115950` ; branche QA créée `br-green-meadow-b9j6o0bp` (distincte du parent `br-sweet-frog-b9ok6ptp`) ; DB `iamina925_empty` ; rôle `iamina925_empty_owner`. Le quota n'est plus le blocage actuel.
- Sandbox Vercel isolé et non persistant `sbx_BPUoaCGdR5KggdtfBTTKsolu2hQY` au code exact : Python 3.12 + Django, préflight **lecture seule PASS** sur quatre identités, compte 0, migration planifiée uniquement `core.0024`. Exécution de migration **refusée par les contrôles de sécurité** : aucune instruction de contournement, aucun DDL manuel. Session **STOPPED** pour arrêter les ressources.
- **SQL Neon indépendant après le refus :** `auth_user=0`, `core.0024=0`, `to_regclass('public.core_w02vaultrevisionanchor') IS NULL`. Aucun compte ni table W02 ajouté. **NO-GO patient**.

### Séquence restante réelle

1. Voie de migration QA Django autorisée sur exactement cette branche et ces identités, puis SQL indépendant post-migration `auth_user=0`, ancre W02 vide et `core.0024=1`.
2. Revoir l'app-lock première connexion/remote recovery et le legacy Web avant toute autorisation patient ; confirmer tests Chrome et captures BEFORE/AFTER à mêmes dimensions explicites si score géométrique demandé.
3. Valider E2E hosted Web→BFF→API→Neon QA : compte synthétique A→logout→B→A, bearer invalide, crash/commit/recovery, révocation, suppression applicative, SQL final `auth_user=0`. Flag W02 exclusivement QA, jamais Production sans GO distinct.
4. Résoudre le gate W01 first-user : [run #40739595534](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/40739595534) **FAIL** sur « Maroc » et inscription. Refaire suite W01, audit sécurité indépendant, revue PR DRAFT, décision humaine GO, puis merge/post-merge et closeout.
5. **Aucun % lot/chantier certifié** tant que ces gates échouent ou ne sont pas exécutés. Pas de GO clinique, pas de main, pas de données réelles.

