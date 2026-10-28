# W02 — Memory-only SQLite WASM executor candidate (2026-10-28)

## Goal / observable criterion

Create an isolated Flutter Web/Drift candidate with explicit InMemoryFileSystem instead of Drift's default OPFS/IndexedDB storage selection; allow an already-authenticated SQLite byte snapshot to be opened as an in-memory SQLite file, queried through a Drift executor, exported as bytes, and closed with memory cleared.

**Not a patient runtime integration.** The existing Web clinical patient vault deny gate in database.dart is UNCHANGED. No JS bridge, user recovery UX, key authority or automatic encrypted commit is implemented by this candidate; the preceding JavaScript AES-GCM envelope/IndexedDB ciphertext store remains independent.

## Exact pinned API evidence

Project lock: drift 2.31.0, sqlite3 2.9.4, typed_data 1.4.0. Primary source code inspected:
- https://api.github.com/repos/simolus3/drift/contents/drift/lib/wasm.dart?ref=drift-2.31.0 — WasmDatabase.opened(CommonDatabase, closeUnderlyingOnClose:false) and explicit inMemory API.
- https://api.github.com/repos/simolus3/sqlite3.dart/contents/sqlite3/lib/src/in_memory_vfs.dart?ref=sqlite3-2.9.4 — InMemoryFileSystem.fileData and virtual file bytes.
- https://pub.dev/packages/sqlite3/versions/2.9.4 ; https://drift.simonbinder.eu/platforms/web/ .

Implementation: frontend/lib/data/drift/w02_web_memory_sqlite_candidate.dart. Seeds an explicit memory VFS with a previously authenticated SQLite image (if supplied), validates header and maximum 64 MiB, rejects bad journal/temp-store mode and quick-check, exposes WasmDatabase.opened, refuses exporting during uncommitted SQLite transactions or nonempty sidecars, copies bytes, closes executor and disposes the SQLite connection and volatile file system. The NULL initial snapshot path is test-only; it cannot confer authorization to create a new real patient vault. Caller is responsible for validating AAD, patient scope, recovery key and independent rollback floor; not implemented here.

Tests authored: frontend/test/web/w02_web_memory_sqlite_candidate_test.dart (3 Flutter Web/Chrome cases: synthetic SQL insert -> memory snapshot -> reopen/SELECT, invalid image rejected, new independent memory vault empty). **NOT EXECUTED**: no Dart/Flutter SDK installed in the local runner, browser loading restricted by administrator; tests and compilation require an eligible isolated sandbox/CI on exact SHA. Do not claim browser passes or successful Flutter build.

Static Node regression contract: scripts/tests/test_w02_memory_sqlite_source_contract.mjs. Locally 4 PASS / 1 SKIP (runtime database.dart absent from standalone partial checkout). This tests only source shape, NOT runtime behavior. Existing 39/39 Node test evidence applies to previously published JavaScript ciphertext primitives and is NOT a substitute for Dart/Chrome verification.

## Release blockers / NO-GO

1. Run dart analyze + flutter test --platform chrome with pinned dependencies and WASM asset served correctly; prove actual WASM/SQLite replay and inspect physical browser IndexedDB/OPFS for plaintext. Repair any incompatibilities.
2. Build a durable authenticated JS-Dart bridge to the prior ciphertext-only IndexedDB store: no unverified account enrollment, atomic flush, stale-tab conflict prevention, quotas, offline, crash and deletion.
3. Independently trusted revision floor and account-to-slot mapping; safe key/recovery lifecycle and user-facing recovery UX. Browser raw storage must not reveal clinical data.
4. No-loss quarantine and authorized migration of legacy plaintext stores, independent security/privacy review, real browser synthetic A-to-B-to-A.
5. Close W01 before W02 merge as required by roadmap; run only one final GitHub CI once integrated; seek separate explicit Vercel Preview GO, then real hosted synthetic Web to BFF to API to Neon with independent SQL cleanup auth_user=0.

**W02 patients/Production NO-GO**. No Vercel deployment, Neon mutation, PR merge, patient data or clinical app-path activation in this subpass. No UI/UX change in the product.


## 28/10/2026 — Diagnostic Chrome sur branche de test, non certifié

Rappel du résultat réellement observé dans le sandbox précédent : après correction du chemin WASM via `WasmSqlite3.load(bytes)` et `rootBundle`, Dart analyze 0 issue, mais Chrome encore **1/3 PASS, 2/3 TIMEOUT (30 s)**. L'origine n'a pas été identifiée (aucune trace de l'étape exacte). **Ces modifications sandbox n'avaient pas été publiées**.

Le présent candidat de diagnostic fournit un chargeur de bytes explicite (asset Flutter existant `web/sqlite3.wasm`), la dépendance `sqlite3:2.9.4`, la binding de tests Flutter et une trace par étape `asset_load`, `wasm_load`, `vfs_register`, `sqlite_open`, `pragma`, `drift_executor`, `runCustom`, `insert`, `export`, `reopen`, `select`. Un délai explicite de 12 s sur le chargement asynchrone remplace un gel silencieux par `w02_wasm_load_timeout`. La trace ne contient aucune donnée patient.

**Statut au moment de la préparation : CI Chrome non exécutée sur ce nouveau SHA.** Une branche de test isolée, non mergée, sert uniquement à obtenir le journal GitHub Actions complet. Si la CI révèle une autre étape bloquée, corriger la cause, relancer le test au nouveau SHA et n'appeler 3/3 PASS que sur preuve exacte. Garde clinique Web inchangé, aucune activation de coffre patient, aucun Vercel/Neon/Production.


## 28/10/2026 — Résultat CI instrumentée #40710384590 et correction du harness (pré-CI)

Preuve vérifiée au commit `59520a9e` : contrats Node 45/45 PASS, Flutter analyze PASS, mais Chrome 1/3 PASS, 2/3 FAIL. Journal exact du job #122893748668 : `W02_STAGE asset_load:start` puis `TimeoutException after 0:00:12.000000` deux fois. Aucun `asset_load:done` ni `wasm_load:start`. **La panne est la récupération de l'asset `rootBundle.load` dans le harness `flutter test --platform chrome`**, et non une défaillance SQLite WASM prouvée. Le diagnostic précédemment inconnu est maintenant isolé.

Nouvelle stratégie de test (branche uniquement) : supprimer l'appel `rootBundle` du test et fournir les octets WASM exacts déjà commités sous `frontend/web/sqlite3.wasm` via serveur HTTP de fixture lié à 127.0.0.1:7399, Content-Type `application/wasm`, CORS explicite ; `WasmSqlite3.loadFromUrl` reçoit une URL strictement locale injectée avec `--dart-define`. Le serveur ne sert que ce binaire, jamais d'autre fichier. Analyse, contrat Node et trois tests Chrome doivent encore passer au **nouveau SHA** avant toute revendication. Garde patient inchangé, aucun déploiement Vercel ni mutation Neon.


## 28/10/2026 — Deuxième CI complète : WASM/SQLite PASS, Drift exige ensureOpen

[Run #40711232856](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/40711232856), job 122896788781, exact SHA a122393d : Node 45/45 PASS et analyse Flutter PASS ; **Chrome 1/3 PASS, 2/3 FAIL**. Trace : `wasm_load:done → vfs_register:done → sqlite_open:done → pragma:done → drift_executor:done` (WASM chargé sur HTTP localhost en ~0,31s). Première et troisième requêtes échouent immédiatement : `Bad state: Tried to run an operation without first calling QueryExecutor.ensureOpen()!`. Il ne s'agit donc plus d'un timeout ni d'une indisponibilité WASM : cause confirmée = tests appelant directement le `QueryExecutor` Drift sans protocole d'ouverture.

Correctif suivant **dans le test seulement** : implémentation `QueryExecutorUser` synthétique version 1, `beforeOpen` no-op (sans migrations cliniques), `await executor.ensureOpen(user)` pour les trois connexions créées dans le scénario avant toute requête. Source Drift 2.31.0 vérifiée : interface QueryExecutorUser et exigence d'ensureOpen. N'active ni ne modifie le runtime patient. **CI nouveau SHA requise** pour 3/3 Chrome avant toute validation.

## W02 — Isolated Chrome proof and direct candidate branch integration (2026-10-28)

**Verified diagnostic branch:** [run #40711893615](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/40711893615), SHA `30e92e86e3eec97ce20855db04ae07ddd87d2ccf`, Chrome `3/3 PASS` for actual SQLite WASM -> Drift -> synthetic insert -> binary snapshot -> reopen/SELECT and new-connection isolation, Node `46/46 PASS`, focused Flutter analysis PASS. Driver used loopback HTTP fixture for binary WASM load, not `rootBundle.load` under `flutter test`, and explicitly `executor.ensureOpen` before Drift direct queries. This fixes the synthetic test harness only, not a clinical vault. All assertions were run on diagnostic SHA, not yet on the new candidate SHA.

**Candidate branch integration:** these exact Dart/test/Node/fixture files are being copied into `feat/w02-web-bff-readonly-preflight-20261028` with a workflow trigger for that branch. **The new candidate SHA must prove its own CI**; the previous diagnostic PASS must not be represented as proof on the new SHA. The patient Web deny gate in `database.dart` remains unchanged. No JS-Dart encrypted persistence bridge, key recovery, anti-rollback or legacy data migration has been implemented or certified; no Vercel deploy, Neon mutation, real patient or merge. W01 closeout remains prerequisite to W02 merge.

## W02 — Final focused analyzer lint tightening (2026-10-28)

[Feature branch run #40712512060](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/40712512060) at source SHA `8c02657f370bc46eaf9a08a8b0d97ad8d2a5290f` was **SUCCESS**: Chrome 3/3 and Node 46/46 PASS, with 14 nonfatal analyzer INFO diagnostics (`avoid_print`) in test instrumentation. Before claiming a completely clean focused analyze, replace test-only `print` with Flutter's `debugPrintSynchronously` and require `flutter analyze --fatal-infos` in the isolated W02 workflow. These are test/harness-only hygiene changes; a **fresh exact-SHA successful CI is required**.


## Liens avec D10 — coordinateur synthétique parallèle vérifié (2026-10-28)


## Closeout technique des tests synthétiques parallèles — 28/10/2026

**Code exact vérifié :** [620ef4d7](https://github.com/hraaaaf/IAMINA-MVP/commit/620ef4d7fc8ade120aaba2f503aef2184de1269c) ; [GitHub Actions #40715637997](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/40715637997) **SUCCESS** (job 122912426747) : **62/62 tests Node PASS, 3/3 Flutter Chrome SQLite WASM PASS, analyse Flutter `--fatal-infos` « No issues found! »**. Le coordinateur représente **16 tests Node** ; les 46 autres contrats Node portent sur l'enveloppe AES-GCM, IndexedDB CAS, test Drift source. Ce résultat ne prouve pas un bridge Dart↔JS ou l'activation de `AppDatabase`.

**Inventaire legacy, lecture seule du code :**
- `frontend/lib/data/drift/database.dart` : `AppDatabase.defaults()` ouvre la base **historique non scopée** `amina`. Elle ne peut jamais être rattachée automatiquement au prochain utilisateur connecté.
- `AppDatabase.forPatientVault()` construit un coffre nommément isolé par `PatientVaultScope` : `amina_vault_v1_native_<userId>` ou `amina_vault_v1_device_<uuid-v4-normalisé>` ; la preuve d'autorisation propriétaire doit provenir de l'auth, pas du nom de DB.
- Schéma Drift version **12**, cinq tables déclarées `LogEntries, PatientProfiles, ChatMessages, MedicationEvents, Reminders` plus `patient_treatment_declarations_v1` créée par migration ; v11→12 enrichit le statut de sync. Ne pas inventer identité ou traitement de l'ancienne base, ni effacer/migrer avant consentement et preuve de propriété.
- `frontend/web/index.html` charge actuellement uniquement `iamina_app_lock.js` et Flutter bootstrap, **pas** le coordinateur synthétique ; garde `encrypted_web_patient_vault_unavailable` maintenu.

**Gate migration :** propriété de `amina` inconnue sans preuve externe → contrôle humain et plan no-loss ; sauvegarde chiffrée et contrôle des données avant bascule, quarantaine puis effacement uniquement après confirmation vérifiée. Pas d'opération sur une vraie base dans ce lot.

**Références externes :** [OWASP HTML5 Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/HTML5_Security_Cheat_Sheet.html) et [MDN IndexedDB durability](https://developer.mozilla.org/en-US/docs/Web/API/IDBTransaction/durability) : `strict` reste un hint et IndexedDB ne constitue ni secret store ni backup, XSS restant menace. Aucune « garantie anti-XSS » revendiquée.

**Restant critique D10-B Web :** vrai bridge JS↔Dart sous auth epoch/owner vérifié, autorité de révision monotone indépendante durable et recovery sans pertes, véritable implémentation app-lock facultative uniquement après sécurité, migration consentie, E2E multi-comptes + navigateurs, revue sécurité/privacy indépendante, UI BEFORE/AFTER, GO W01 avant merge W02, autorisation distincte de Preview Vercel. **NO-GO patient** ; rien déployé, rien muté sur Neon, aucune fusion. Pourcentage D10 global **non certifiable** à partir des seuls tests synthétiques.


## 28 octobre 2026 — Closeout exact-SHA : navigateur réel et durcissement VFS PASS

**Preuve finale :** HEAD code [5d534e04d4fa](https://github.com/hraaaaf/IAMINA-MVP/commit/5d534e04d4fa5ac954e742f1c814e5be4c2f2630), [GitHub Actions run #40721633619](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/40721633619), job `122933807084`, **SUCCESS**, logs : **63/63 Node PASS**, **5/5 Flutter Chrome PASS**, **0 Flutter analyzer issue** (`--fatal-infos`). Chrome a testé le flux complet SQLite WASM/Drift → JS Uint8Array → AES-256-GCM WebCrypto → CAS IndexedDB ciphertext-only → déchiffrement → second exécuteur Drift SELECT, plus mauvais secret, scope B et floor supérieur. Le VFS mémoire écrase avec `fillRange` les buffers atteignables avant `clear`, sans garantir l'effacement complet en RAM/GC.

**Historique des échecs préfinal :** runs 40721290007, 40721377823, 40721481773 FAIL sur assertion source Node liée à l'ancien `clear()` / `buffer?.fillRange` après refactor ; aucun de ces trois runs n'a exécuté Chrome. Contrat corrigé après lecture du log et test exact des regex contre le Dart courant, puis CI entièrement verte sur nouveau SHA. Ne jamais présenter les anciennes CI FAIL comme PASS. Runs 40720479457 et 40720733757 ont été annulés pendant corrections, et run #40720861475 SUCCESS sur ancien code **sans** le scrub VFS.

**Portée vérifiée :** diff GitHub entre `ac8b682f` et `5d534e04` limité à huit fichiers dans le banc W02, aucun changement à `frontend/lib/data/drift/database.dart` ni `frontend/web/index.html`. Fixture ES module exclusivement sous `scripts/fixtures`, servie sur loopback par whitelist GET/HEAD, non livrée dans les assets Web. Vercel `list_deployments(branch=W02)` renvoie **0 déploiement**. Aucune fusion, mutation Neon, consultation de données patient ou activation clinique.

**Décision D10-B patient : NO-GO.** L'autorité de révision est injectée/mock dans les tests ; un floor navigateur n'est pas une ancre sûre. La gestion des clés/récupération offline, le protocole atomique externe et BFF auth-epoch, le schéma clinique réel, la migration legacy no-loss, l'E2E A→logout→B→A et l'audit sécurité/privacy indépendants ne sont pas achevés. W01 reste préalable au merge W02 ; Vercel exige autorisation explicite séparée.

**Next exact :** valider le choix d'ancre durable côté identité BFF avec politique de cohérence hors-ligne et récupération de crash (enjeu produit : local-first vs anti-rollback strict), puis implémenter en isolation la vérification d'auth-epoch et le commit/récupération sans activer les patients. Tests multi-navigateurs et audit indépendant après établissement du protocole.
