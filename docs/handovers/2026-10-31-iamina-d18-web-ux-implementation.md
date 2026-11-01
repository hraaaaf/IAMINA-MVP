## 01/11/2026 — D18 migration synthétique VERIFIED ; intégration produit NON autorisée

[Run #41334344187](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41334344187) SUCCESS, commit `660e8d26` : `syntheticMigrationRehearsal` rapporte `sourcePreserved:true`, `destinationVerified:true`, `wrongKeyRejected:true`, `cutoverAllowed:true`. Le dernier booléen ne concerne **que le test synthétique** ; aucun basculement IAMINA ni transfert des données réelles. Les scénarios précédents (restart, rekey, SIGKILL) sont aussi validés sur Chromium synthétique.

**Point critique** : la source simulée est une DB SQLite OPFS non chiffrée, tandis que l'application utilise potentiellement un autre adaptateur Drift/IndexedDB. Ne pas extrapoler cette preuve à la migration réelle. Le chemin exact de la connexion Web, les schémas/migrations, les règles de multi-identités et la gestion de clé doivent être inspectés sur le HEAD produit avant toute implémentation. Aucune preuve de ces éléments dans ce lot. Garder source intacte, sauvegarde chiffrée indépendante, comparaison exhaustive et rollback ; aucune migration automatique sans approbation clinique/sécurité. Aucun merge ni déploiement Vercel.

**Next exact :** localiser les fichiers réels de connexion SQLite Web dans le repo (recherche de code sur branche, non présumer `lib/` racine), documenter l'adaptateur source, puis concevoir migration idempotente et tests fail-closed.

---

## 01/11/2026 — D18 OPFS worker VFS VERIFIED GREEN with COOP/COEP

Run [#41322017662](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41322017662), job `124894118686`, SUCCESS. Chromium `crossOriginIsolated:true`, `sharedArrayBuffer:"function"`, worker `opfsRegistered:true`, `vfsList` includes `opfs-wl` and `opfs`. Previous missing OPFS was caused by absent browser cross-origin isolation in probe server. `kvvfs` still rejects `PRAGMA key`; `encryptedPersistenceVerified:false`. Next: worker-backed OPFS encrypted open/write/close/reopen and wrong-key fail-closed with raw OPFS byte inspection; do not claim at-rest encryption or merge/deploy yet.

---

## 01/11/2026 — D18 KV VFS incompatibility VERIFIED

Run [#41315678291](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41315678291), job `124875080793`, SUCCESS as *diagnostic*. `kvvfsExploration.attempted:true`, `opened:true`, `reopened:false`, `encryptedPersistenceVerified:false`; error **`SQLite3Error: SQLITE_ERROR: sqlite3 result code 1: Setting key failed. Encryption is not supported by the VFS.`** Therefore `kvvfs` is not a viable encrypted persistence backend for this pinned sqlite3mc build. The green CI reflects diagnostic completion, not security readiness. Next: investigate a sqlite3mc-compatible persistent encrypted VFS/OPFS-enabled WASM build; require keyed reopen, wrong-key rejection, and raw storage inspection. No merge/deploy.

---

## 01/11/2026 — D18 persistence gate VERIFIED GREEN

Run [#41313544113](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41313544113), job `124868750666`, SUCCESS. Chromium output: `opfsRegistered:false`, `kvvfsRegistered:true`, `persistenceGate:"BLOCKED_NO_OPFS_VFS"`, `encryptedPersistenceVerified:false`. This validates the explicit *negative* persistence gate, **not encryption at rest**. Next: isolated keyed persistence investigation with available `kvvfs` or a compatible OPFS-enabled build; require close/reopen, wrong-key rejection and raw bytes inspection. No merge/deploy.

---

## 01/11/2026 — D18 Chromium worker/OPFS discovery VERIFIED GREEN

Run [#41312403276](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41312403276), job `124865343681`, SUCCESS. Browser evidence: `sqliteRoundtrip:true`, `keyApi:"function"`, `opfsApi:"undefined"`, `opfsStorageApi:"function"`, `workerApi:"function"`, `encryptedPersistenceVerified:false`; worker `workerReady:true`, `configType:"config-get"`, `configKeys:["bigIntEnabled","version","vfsList"]`. Browser OPFS API and upstream SQLite worker work, but `oo1.OpfsDb` absent in main-thread context. **No keyed persistent database or wrong-key proof yet.** Next: inspect worker VFS list, prove persisted encrypted keyed SQLite across browser restart and wrong-key rejection. No merge/deploy.

---

## 01/11/2026 — D18 : worker/OPFS discovery (test CI pending)

Commit `5054aab4` extends the isolated Chromium probe to load upstream `sqlite3-worker1-promiser.js`, require worker readiness and inspect `config-get`, `navigator.storage.getDirectory` and worker API. This targets the observed `oo1.OpfsDb:undefined` on #41312036909 without modifying the application or claiming persistence. **Not yet CI-verified**. Next: inspect worker result; only then implement keyed persisted database, wrong-key and restart checks. No merge/deploy.

---

## 01/11/2026 — D18 sqlite3mc Chromium API probe VERIFIED GREEN

GitHub Actions [#41312036909](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41312036909), job `124864238545`, **SUCCESS** on code commit `613e2405`. Browser evidence: `sqliteRoundtrip:true`, `keyApi:"function"`, `opfsApi:"undefined"`, `encryptedPersistenceVerified:false`. **Implication:** in-memory SQLite and `sqlite3_key` API proven in Chromium; `oo1.OpfsDb` absent in this context, so persistence adapter/worker must be investigated before attempting keyed OPFS/restart. Do not conflate API presence with keyed encryption. No merge/deploy. Next: isolated persistent backend proof (OPFS/alternative) + keyed reopen/wrong-key.

---

## 01/11/2026 — D18 POC Chromium : découverte API réelle du moteur

Après probe acquisition #41308799558 SUCCESS, commits `17c7cced`, `64c05057`, `1876f451`, `4066f850` ajoutent un **test navigateur synthétique isolé** sur la release WASM épinglée : charge `sqlite3.js` dans Chromium, crée une DB en mémoire, effectue un aller-retour SQLite et vérifie si `sqlite3.capi.sqlite3_key` est exposé ; rejette l'absence d'API de clé. Workflow CI installe Playwright/Chromium pour ce probe. **CI à vérifier : test non encore validé, ne démontre pas OPFS/IndexedDB, fermeture/réouverture, ni chiffrement au repos.** Si le moteur encapsule autrement la clé, inspecter la JS API et corriger le probe sans masquer l'absence de clé. Aucun changement production, merge ou déploiement.

---

## 01/11/2026 — D18 sqlite3mc WASM acquisition probe VERIFIED GREEN

GitHub Actions [#41308799558](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41308799558), job `124854658956`, **SUCCESS**. Logs : `D18 WASM preflight: 4 synthetic checks PASS; encryption NOT tested`, binaire WASM inspecté avec `status: BINARY_VALID_ONLY`, SHA256 binaire `0b5a4bfff35f1ec87bf6f68ea293f425b86cbd661b77628a955cb827c9fbf524`, `encryptedDatabaseVerified: false`, et `D18 release SHA and WASM structure inspected; encrypted persistence NOT verified`. Archive amont vérifiée contre SHA256 épinglé. **Sous-lot acquisition/intégrité clôturé ; intégration Drift, clé, persistance et chiffrement au repos toujours ouverts.** Pas de merge/deploy.

---

## 01/11/2026 — Probe sqlite3mc : correction du déclenchement PR

HEAD précédent `3fc3e7ac` : D18 #41266682333 SUCCESS, CI #41266682462 SUCCESS. Aucun run du nouveau probe dans la liste des runs PR ; l'API GitHub utilisée filtre uniquement les runs `pull_request` (ce qui peut masquer des runs `push`). Commit `bdd8a0b9` : ajout du déclencheur `pull_request` sur chemins pertinents à `.github/workflows/d18-sqlite3mc-release-probe.yml`, sans modifier l'application. Nouveau run non encore observé. Archive v2.6.1 et SHA256 vérifiés sur page release amont, mais **pas encore téléchargés et validés en CI**. Aucune preuve d'intégration Drift ni de chiffrement au repos.

---

## 01/11/2026 — Source WASM chiffrée officielle trouvée ; acquisition CI en vérification

Sources primaires : `utelle/SQLite3MultipleCiphers` publie v2.6.1 / SQLite 3.54.0, archive `sqlite3mc-2.6.1-sqlite-3.54.0-wasm.zip`, SHA256 annoncé `aba121490fd6123bcbef8404ee26df9b26c0301063781e2aa31f05aed6f48384` ; documentation officielle Drift Web impose un WASM/worker compatible. Commits `66fe46c8` et `20788682` ajoutent un probe CI isolé qui télécharge l'archive, vérifie SHA256 et inspecte WASM. **Non exécuté/validé à la rédaction ; aucune preuve de clé, persistance, worker Drift ni chiffrement au repos.** Attention : le préflight actuel exige des exports `sqlite3_*` qui peuvent ne pas être directement exposés par le WASM officiel ; si le probe échoue, inspecter la JS API fournie et ne pas supprimer les vérifications sans remplacement par un test effectif. Aucun déploiement/merge.

---

## 01/11/2026 — Correction du préflight WASM (fail-closed)

`e230b70e` modifie le préflight : un WASM structurellement valide sans export SQLite identifiable est désormais **rejeté** (exit 1), au lieu de produire BINARY_VALID_ONLY. `802acff7` adapte la régression synthétique correspondante. Attention : des moteurs SQLite avec API encapsulée pourraient aussi être rejetés ; ce filtre n'est ni une preuve de chiffrement ni un substitut à un test moteur/worker. Nouveau HEAD CI à vérifier. POC Chromium et moteur chiffré toujours absents ; aucun merge/deploy.

---

## 01/11/2026 — Preflight WASM : tests synthétiques exécutés

HEAD code `c9eb9a06` : `tools/d18_sqlite_cipher_preflight_test.js` ajoute quatre contrôles (binaire absent, non-WASM, WASM malformé, WASM structurellement valide mais non chiffrant). Une copie locale équivalente du test a été exécutée avec Node 22 : `4 synthetic checks PASS; encryption NOT tested`. L'absence de moteur sqlite3mc WASM compatible empêche toujours la preuve Chromium de chiffrement au repos. CI GitHub sur ce HEAD à vérifier. Aucun merge/deploy.

---

## 01/11/2026 — WASM encrypted SQLite candidate preflight

Added `tools/d18_sqlite_cipher_preflight.js` (`eb1cb8c4`). Local Node checks: missing binary exits 2; invalid binary exits 1. The probe only checks WASM structure and prints a SHA-256 for provenance; it explicitly does not certify encryption. No sqlite3mc WASM binary was available in the execution environment and direct GitHub fetch failed DNS resolution, so keyed database persistence/reopen tests are **blocked**, not passed. Next: obtain a pinned, auditable candidate WASM + matching Drift worker, then implement and run real browser keyed open/restart/wrong-key tests. No merge/deploy.

---

## 01/11/2026 — POC chiffrement au repos : cadrage exécutable, gate ouvert

Nouveau document `docs/architecture/d18-web-at-rest-encryption-poc.md` (commit `7f93671e`) : threat model, preuves exigées sur vrais octets persistés, restart mauvaise/bonne clé, rotation, migration et rollback, couverture toutes tables cliniques, compatibilité Drift worker/OPFS/IndexedDB. **Aucun moteur chiffré intégré ni POC exécuté** à ce stade. Un simple scan sans chaîne en clair ne constitue pas une certification. Décision humaine requise sur clé/récupération avant migration. Dernier D18 CI vert : #41262090166 sur HEAD antérieur `be3f967e`; CI du nouveau HEAD non encore prouvée. Aucun merge/deploy.

---

## 01/11/2026 — D18 browser : régression téléchargement périmé

HEAD fonctionnel `3770d1b1` : `tools/d18_web_file_e2e.js` vérifie désormais après un téléchargement réel que la nouvelle ouverture du dialogue et une tentative d'export invalide (phrase vide) montrent le message de validation, mais **aucun** bouton de téléchargement d'un ancien fichier. Screenshot de preuve `rejected-new-export-no-stale-download`; échec explicite si action périmée visible. Limite : ce scénario teste consommation après téléchargement, **pas** un échec crypto après un export préparé encore en mémoire ; ce dernier nécessite une injection d'échec ou un test widget dédié. CI de ce nouveau HEAD à vérifier. Pas de merge/deploy.

---

## 01/11/2026 — D18 FUE navigateur

Run D18 #41255659421 rouge sur af8e63dc : bouton Enregistrer désactivé après saisie de l'année, Playwright timeout. Cause précise non prouvée. Commit a67ab5a2 : le test vérifie désormais la saisie effective par copier/coller avant clic, exige bouton actif et capture si inactif. Pas de suppression d'assertion, pas de changement clinique. CI nouveau HEAD à vérifier. Next : consulter les preuves du nouveau run, tester export réussi puis export échoué, FUE 200%, POC crypto. D7 hors lot.

---

## 01/11/2026 — D18 export Web : prévention d'un téléchargement périmé

**Goal :** après une nouvelle tentative d'export D18, ne jamais proposer le fichier chiffré issu d'une tentative précédente. **Avant :** `_prepared` restait défini quand `D18EncryptedBackup.exportEncrypted` échouait, donc le bouton télécharger pouvait encore servir le backup précédent. **Changement :** `frontend/lib/features/profile/d18_backup_section.dart` efface les octets de `_prepared` via `fillRange(0, length, 0)` puis remet `_prepared = null` avant chaque tentative valide d'export. **Commit :** `8ea64e5bc3a2e8b7c0c395b9dfb442c7bbe7745f`. **Preuve :** inspection du chemin de contrôle et diff de code ; CI de ce commit non encore certifiée. **Risque résiduel :** mémoire navigateur / copie antérieure déjà téléchargée hors de portée ; chiffrement de la base Web non résolu. **Next :** test widget export succès→échec→bouton absent et FUE Web ; POC chiffrement entier séparé. Aucun merge ni déploiement.

---

# IAMINA — D18 Web / profil progressif + sauvegarde chiffrée — 2026-10-31

## Goal
Intégrer l'UX approuvée au vrai `ProfileScreen` Web IAMINA : données facultatives, poids daté et corrigeable, coffre patient local-first, export chiffré et restauration D18 uniquement. **Pas de synchronisation automatique des données D18 ni de déploiement Vercel.**

## Décisions validées
- Web local-first (option A), profil sans obligation d'onboarding.
- Export manuel chiffré ET restauration testée comme critères bloquants D18.
- Direction UX validée avec obligation d'adaptation aux cartes/typos/couleurs/interaction existantes d'IAMINA. Ce n'est pas une autorisation de merge/deploy.

## État vérifié avant certification
- Base main au démarrage : `fc0366f4c55f2bb25c2b9e2a15367d9241567c76`.
- Branche : `feat/iamina-d18-web-progressive-profile-20261031`.
- PR brouillon : https://github.com/hraaaaf/IAMINA-MVP/pull/1207
- Intégration : `frontend/lib/features/profile/profile_screen.dart` + `profile_screen_presentation.dart` (Web uniquement), et widgets D18 propres au thème `AminaVisualLanguage`.
- Données : `patient_progressive_demographics_store.dart`, `patient_weight_history_store.dart`. PatientVaultScope contraint physiquement le stockage ; pas d'appropriation du coffre legacy.
- Sauvegarde : `d18_encrypted_backup.dart` ; AES-256-GCM avec AAD v1 ; PBKDF2-HMAC-SHA256 600000 itérations + sel aléatoire ; wrapper sans identité ni données patient ; file picker dédié dans Données et appareils. Restauration uniquement si données D18 destination vides, transaction D18-only, vérification après écriture. Jamais `LocalBackup.restoreVaultJson` qui écrase des tables médicales étrangères à D18.
- Poids : version correcte écrite comme nouvelle observation liée à la précédente ; écran n'affiche que la dernière version ; suppression explicite purge la famille.
- Tests ajoutés/portés : démographie indépendante du profil médical, historique + correction/suppression, crypto, altération/mauvaise phrase secrète, mauvais propriétaire, import non destructif, transfert local volontaire.

## 31/10/2026 — Exécution du gate POC : environnement et CI (sans résultat crypto inventé)

**Tentative réelle :** inspection du runtime de travail : Chromium et Node présents, **Dart/Flutter absents** ; accès externe au registre pub.dev indisponible (résolution DNS). Les binaires `sqlite3mc.wasm` ne sont pas présents dans les fichiers montés. Impossible de lancer ici un POC WASM/Drift fidèle aux versions verrouillées. **Résultat : POC BLOCKED_EXTERNAL_TOOLING**, pas « PASS ». Il serait trompeur d'utiliser un simple test de contrat statique comme preuve de chiffrement.

**CI observée sur HEAD précédent `84ded8f4` :** 16 workflows détectés, dont plusieurs in_progress ; **D7 returning patient Web FUE #41252769623 FAIL**. Log précis : `frontend/test/services/d7_consent_withdrawal_fue_test.dart` introuvable lors de l'étape `D7 C01-C05 consent safety, refusal, lock and retry synthetic FUE`. C'est un échec de **fixture de test manquante**, distinct du chiffrement D18 et de la régression produit ; il interdit de déclarer la CI globale verte. TD-008 #41252769487 et D18 #41252769806 étaient in_progress au relevé. **Next indépendant :** rétablir la fixture D7 manquante ou corriger son chemin en vérifiant la référence canonique, puis exécuter POC sur runner équipé de Dart/Flutter/WASM ; ne pas relancer aveuglément le run D7.

**Aucune donnée clinique, crypto, déploiement ou migration modifiés.** Scores D18 restent privacy BLOCKED 5.9 ; aucune certification FUE obtenue sur ce HEAD.

---

## 31/10/2026 — POC chiffrement Web / gate préflight versions réelles

**Goal :** vérifier le candidat `sqlite3mc.wasm` **sur les dépendances réellement verrouillées** avant toute migration. **Succès observable :** preuve Web exécutable avec base synthétique, mauvaise clé rejetée, persistance et octets non lisibles sans clé, Drift worker fonctionnel ; **statut : NON EXÉCUTÉ**, aucun binaire WASM chiffrant ni runner Dart disponibles dans l'environnement de cette revue.

**Preuve vérifiée sur `frontend/pubspec.lock` :** `drift 2.31.0`, `drift_flutter 0.2.8`, `sqlite3 2.9.4`, `sqlite3_flutter_libs 0.5.42`. Le `pubspec.yaml` avec contraintes `^2.20.0` ne reflète **pas** la version installée ; la documentation `sqlite3 latest` présentant `sqlite3mc.wasm` est une version plus récente et ne prouve pas sa disponibilité avec `sqlite3 2.9.4`. Les exemples de chiffrement Drift `NativeDatabase` ne s'appliquent pas tels quels à `WasmDatabase.open` ; la documentation Drift Web précise que le callback `setup` natif n'est **pas disponible directement** lorsque la DB est ouverte dans le worker et recommande un worker personnalisé pour initialiser les connexions. Voir [Drift Web — Custom functions and database setup](https://drift.simonbinder.eu/platforms/web/), [sqlite3 Web](https://pub.dev/packages/sqlite3), [Drift Encryption](https://drift.simonbinder.eu/platforms/encryption/).

**Ordre POC à exécuter sur runner équipé de Flutter/Dart et Chromium (pas de tests inventés) :**
1. **Préflight :** résoudre la disponibilité d'un `sqlite3mc.wasm` correspondant à l'API `sqlite3 2.9.4`; si impossible, isoler une montée de versions dans une branche/fixture **sans toucher à la production**, noter diff du lockfile et compatibilité Flutter/Dart.
2. **Crypto autonome :** créer base synthétique avec un secret aléatoire, fermer et rouvrir avec secret valide ; mauvaise clé et absence de clé doivent échouer sur lecture réelle du schéma ; examiner le fichier persistant (ne pas se contenter de la réponse de `PRAGMA key`).
3. **Drift :** brancher le moteur chiffrant dans un worker **spécifique au POC**, exécuter `PRAGMA key` avant introspection/DDL et valider transactions, rechargement, 2 onglets, IndexedDB et OPFS. Sans hook de clé prouvé, **NO GO**.
4. **Protection complète :** tests de migration sans perte du coffre entier et de rollback, pas seulement des tables D18 ; conserver les données synthétiques et la preuve brute dans artefact CI.
5. **Critère de clôture :** SHA exact, versions, rapports, screenshots et logs sans données patients, pass/fail négatifs ; aucun « POC PASS » sans artefacts.

**Résultat actuel :** préflight versions **PASS**, POC runtime **NOT_RUN**, intégration Drift **NOT_RUN**. L'environnement local ne fournit pas les exécutables Dart/Flutter ni le binaire chiffrant ; ne pas prétendre à un essai. **Scoring recherche/compatibilité** : EXECUTION_SCORE 7.0/10, ADVERSARIAL_SCORE 7.0/10, retained 7.0/10 (preuve runtime absente) ; score global D18 reste plafonné à 5.9/10 par le gate privacy. **Next exact :** exécuter POC sur runner Dart/Flutter disponible, sans lancer benchmark lourd ni modifier coffre clinique ; FUE Web indépendante à compléter. Aucun merge/deploy.

---

## 31/10/2026 — Étude de faisabilité vérifiée sur sources primaires : sqlite3mc.wasm (pas encore POC)

**Goal :** déterminer une voie techniquement plausible pour chiffrer **le coffre clinique Web entier** sans fausse promesse de compatibilité Drift. **Critère de succès du présent sous-lot :** confronter la configuration IAMINA aux APIs documentées et distinguer faisable en principe de testé dans IAMINA. **Preuves :** `frontend/lib/data/drift/database.dart` (constructeurs `driftDatabase(name: ..., web: DriftWebOptions(sqlite3Wasm: Uri.parse('sqlite3.wasm'), driftWorker: Uri.parse('drift_worker.js')))`), `frontend/pubspec.yaml` (`drift: ^2.20.0`, `drift_flutter: ^0.2.0`, `cryptography: ^2.9.0`), documentation primaire [sqlite3 Dart Web](https://pub.dev/documentation/sqlite3/latest/) et [Drift Web](https://drift.simonbinder.eu/platforms/web/), [Drift encryption](https://drift.simonbinder.eu/platforms/encryption/), [DriftWebOptions API](https://pub.dev/documentation/drift_flutter/latest/drift_flutter/DriftWebOptions-class.html).

**Résultat :** le package `sqlite3` documente officiellement **`sqlite3mc.wasm`**, un binaire Web SQLite3MultipleCiphers et une ouverture explicite via `WasmSqlite3.loadFromUrlString(...)`, `sqlite3.open(...)` et `PRAGMA key`. C'est une **capacité amont démontrée par documentation**, pas un essai IAMINA. La documentation Drift chiffre surtout `NativeDatabase` sur plateformes natives ; elle ne prouve **pas** que l'option `DriftWebOptions` de la version installée exécute `PRAGMA key` avant toute lecture dans son worker. L'API `DriftWebOptions` publiée expose `sqlite3Wasm`, `driftWorker`, `onResult`, `initializeDatabase`, mais **pas de callback explicite de configuration de clé**. Il est donc interdit de déclarer le simple remplacement `sqlite3.wasm` → `sqlite3mc.wasm` comme suffisant ou sûr. Les versions `latest` documentées ne sont pas automatiquement celles verrouillées par IAMINA ; vérifier le lockfile et les signatures effectives.

**Choix technique prioritaire pour POC isolé (non implémenté) :** créer un harness Web séparé, base **synthétique uniquement**, utilisant `sqlite3mc.wasm` et `WasmSqlite3` directement, pour établir (1) création chiffrée et relecture avec clé, (2) échec sans/mauvaise clé, (3) inspection des octets stockés IndexedDB/OPFS, (4) fermeture/rechargement, (5) Safari/Chrome/Firefox et fallback de stockage. Puis démontrer **l'intégration Drift** avec le worker IAMINA et un hook de clé avant accès au schéma ; si non possible avec versions verrouillées, documenter l'adaptateur ou upgrade minimal et son impact. Pas de migration patient tant que le POC n'est pas probant.

**Risques à falsifier :** disponibilité/maintenance binaire et intégrité du WASM, compatibilité avec Drift `^2.20.0`/`drift_flutter ^0.2.0`, support des VFS et accès multi-onglets, persistance en clair pendant migration, performance KDF mobile, gestion du secret sans stockage, données de santé d'autres tables, reprise sur interruption, protection contre XSS pendant session ouverte. **Status : FEASIBILITY_PARTIAL / POC_NOT_RUN / PRIVACY_GATE_BLOCKED.**

**Score du sous-lot de recherche uniquement :** EXECUTION_SCORE 7.5/10 ; ADVERSARIAL_SCORE 7.5/10 ; retained 7.5/10 (compatibilité non testée, preuve manquante) ; ne pas confondre avec la note du lot D18 qui reste plafonnée à 5.9/10 par le risque privacy. **Next exact :** POC indépendant sur versions verrouillées avec mesures navigateur ; FUE clavier/200% et BEFORE↔AFTER sur host identique ; approbation humaine du modèle de clé/récupération avant migration clinique. Aucun merge/deploy.

---

## 31/10/2026 — D18 / architecture de protection locale proposée (ADR non approuvée)

**Décision :** D18-LOCAL-VAULT-ENCRYPTION. **Objectif :** confidentialité au repos du profil Web D18, sans perte de données ni promesse trompeuse de protection XSS. **État : PROPOSED / HUMAN SECURITY GATE.** Aucune modification de chiffrement ni migration exécutée.

**Périmètre vérifié par lecture du code :** `PatientVaultScope` construit les noms de coffres `amina_vault_v1_native_<userId>` ou `amina_vault_v1_device_<uuid>`, mais documente explicitement que ce namespace **ne constitue pas une autorisation**. `D18EncryptedBackup` chiffre les exports avec AES-256-GCM, PBKDF2-HMAC-SHA256 600000 itérations, sel 16 octets, AAD versionné ; le payload contient identifiant de coffre et propriétaire **dans le contenu chiffré**, l'enveloppe publique ne contient pas d'identité. L'import refuse les propriétaires incompatibles, sauf transfert volontaire entre coffres device-only, et refuse les données D18 destination déjà présentes. La section Web annonce correctement l'absence de chiffrement local au repos. **Ces garanties ne s'étendent pas à SQLite/IndexedDB.**

**Architecture candidate (à valider, ne pas implémenter sans gate) :**
1. Définir d'abord l'actif à protéger : **tout le coffre clinique local**, pas seulement les deux tables D18, puisque le même SQLite héberge d'autres données médicales. Chiffrer seulement D18 laisserait une fausse impression de coffre protégé. Définir explicitement le comportement offline et multi-appareils.
2. Préférer un mécanisme de chiffrement **du stockage entier** compatible Drift/SQLite Web, maintenu et auditable. Vérifier concrètement la compatibilité SQLite Wasm, OPFS/IndexedDB, migrations et transactions avant choix. Si aucune solution éprouvée ne fonctionne, documenter une architecture de chiffrement applicatif par enregistrement avec ses fuites (index, schéma, métadonnées) plutôt que prétendre à un chiffrement complet.
3. Clé maître générée aléatoirement côté client, enveloppée par clé dérivée d'une phrase secrète via KDF robuste versionné avec sel unique ; **ne pas conserver la clé déchiffrée, la phrase secrète ou un secret équivalent en IndexedDB/localStorage**. Déverrouillage explicite par session, effacement de références au verrouillage/déconnexion ; expliquer qu'un navigateur compromis peut garder des copies en mémoire. Lier l'accès au coffre au propriétaire authentifié ; ne jamais inférer une autorisation du seul nom du fichier.
4. Récupération : phrase de récupération distincte ou export chiffré validé ; si perdue, impossibilité de déchiffrer les données locales. Ne pas inventer de récupération silencieuse serveur. Établir politique de rotation de secret, export/import et changement de dispositif, y compris anciennes sauvegardes et révocation impossible des copies exportées.
5. Migration **sans perte** : préflight sur base existante, copie chiffrée, contrôle des comptes et nombres de lignes + hash/lecture des enregistrements, rollback et reprise après interruption. Ne jamais supprimer le coffre clair avant vérification complète et confirmation de l'utilisateur. Vérifier que caches, journaux, fichiers temporaires et backups ne laissent pas de données claires résiduelles ; documenter les limites de purge physique du navigateur.
6. Durcissement indépendant : CSP stricte adaptée à Flutter Web, interdiction d'injection et scripts tiers non maîtrisés, revue dépendances, séparation des contextes authentifiés, fermeture de session et prévention de fuite via DevTools/XSS. **Le chiffrement au repos n'empêche pas l'exfiltration durant une session déverrouillée.**

**Critères d'acceptation de l'ADR et de son implémentation future :** test de lecture directe des fichiers IndexedDB/OPFS sans secret (aucune donnée clinique en clair), redémarrage navigateur verrouillé, mauvaise phrase secrète et altération refusées, A→B→A réel sans fuite, perte du secret explicitée, migration interrompue puis reprise sans perte, export/import D18 inchangés, compatibilité FR/AR et 390/768/1280, keyboard/200%, contrôle CSP/XSS, preuve Web réelle au SHA exact. Documenter limites de sécurité et scénario de récupération. Aucun de ces critères nouveaux n'est marqué PASS aujourd'hui.

**Arbitrage requis :** accepter l'extension du périmètre au coffre clinique entier et le modèle de récupération avec perte possible si secret oublié, ou conserver D18 désactivé pour l'usage clinique Web. **Recommandation :** ne pas introduire une pseudo-protection partielle ; faire approuver l'architecture de coffre complet avant toute modification de persistance. Pas de Vercel sans autorisation séparée.

**Perfection Pass (revue critique, sans fausse validation) :** le risque est plus large que D18 : le même stockage peut contenir d'autres données cliniques. Une simple phrase secrète pour l'export ne traite pas ce risque. La faisabilité de chiffrement complet SQLite Wasm reste **non vérifiée** et doit être évaluée avant sélection de bibliothèque. Le chemin court sûr est de maintenir le gate bloquant et d'avancer sur FUE Web indépendant.

---

## 31/10/2026 — D18 sécurité/privacy : revue de risque ciblée, décision recommandée

**Décision nommée :** `D18-PRIVACY-AT-REST`. **Goal :** autoriser l'usage Web du profil facultatif sans exposer silencieusement les données de santé à une compromission locale ou de même origine. **Succès observable :** stockage local protégé selon modèle de menace approuvé + parcours réel de session/effacement et restauration validés. **Preuve actuelle :** inspection de `frontend/lib/features/profile/d18_backup_section.dart`, `d18_profile_panel.dart`, `d18_encrypted_backup.dart`, `patient_vault_scope.dart` (revue antérieure) et rapports E2E 6/6 + 23/23 + 8/8 ; HEAD `a7652ced439b9ff3ecce5d002376cc7a3bab5b5e` CI 15/15 SUCCESS.

**Constats vérifiés dans le code :** l'export `.iamina` est chiffré et protégé par une phrase secrète ; le texte d'information Web FR/EN/AR indique expressément que **le stockage SQLite/IndexedDB local n'est pas chiffré par IAMINA au repos**. Le stockage est lié au coffre physique patient et non synchronisé automatiquement. La suppression de pesée purge les versions locales ; une sauvegarde antérieure peut réintroduire une pesée effacée, avec avertissement de restauration. L'accès à l'IndexedDB via un script malveillant de même origine (XSS) et l'accès aux données sur appareil partagé/compromis ne sont pas neutralisés par le chiffrement du fichier exporté. La disponibilité de données local-first est exposée à l'effacement/éviction du navigateur ; la restauration chiffrée est une mesure de récupération, pas une garantie de conservation.

**Recommandation technique (NON implémentée) :** pour une utilisation clinique Web avec données de santé, ne pas accepter « avertissement utilisateur seul » comme contrôle de confidentialité suffisant. Prioriser (A) chiffrement applicatif au repos avec clé dérivée d'un secret non conservé dans le navigateur, déverrouillage explicite et purge des clés en mémoire à la déconnexion ; modèle de récupération et rotation documenté ; ou (B) si (A) incompatible avec l'architecture/local-first, restreindre D18 à un mode non clinique synthétique jusqu'à validation documentée des terminaux gérés, session/OS et modèle de menace. Le chiffrement applicatif ne neutralise pas à lui seul un XSS exécuté pendant une session déverrouillée : CSP, dépendances, injection, isolation des sessions et contrôle d'accès restent indispensables. **Décision recommandée : A, sous réserve d'un design de clé et de récupération prouvé ; pas d'implémentation cryptographique improvisée.**

**Matrice de menace / statut :**
| Menace | Contrôle observé | Lacune / preuve exigée | État |
| --- | --- | --- | --- |
| Fichier de sauvegarde volé | AES-256-GCM, PBKDF2, secret non persisté ; WebCrypto 8/8 | revue force des secrets / metadata et limites du modèle | PASS technique, revue sécurité OPEN |
| Copie locale IndexedDB / appareil partagé | information claire FR/EN/AR ; séparation physique des coffres | chiffrement au repos/clé, verrouillage et suppression session testés | **BLOCKING PRIVACY OPEN** |
| XSS même origine pendant session ouverte | aucune garantie par chiffrement export | CSP, sanitization, dépendances, test de récupération d'un coffre déverrouillé | NOT_RUN |
| Bascule réelle compte patient A→B→A | patient-scoped DB, preuves synthétiques A/B/A | test session réelle hébergée et absence de fuite d'état | NOT_RUN |
| Perte/éviction du navigateur | export manuel + restauration prouvée | UX de rappel/échec de restauration et récupération sans sauvegarde | PARTIAL |
| Effacement local puis ancienne sauvegarde | avertissement de restauration et import non destructif | confirmation explicite des conséquences et test scénario | PARTIAL |
| Accessibilité FR/AR | captures géométriques 390/768/1280 | Tab/Shift+Tab, focus visible, lecteurs d'écran, 200% texte | NOT_RUN |
| Fidélité visuelle | captures du vrai profil Flutter | BEFORE↔AFTER comparables, mêmes états et viewports | NOT_RUN |

**Scoring provisoire de cette revue (pas une certification de lot) :** Goal=confidentialité Web D18 ; succès=risques critiques traités et preuve FUE ; EXECUTION_SCORE `5.9/10` (E2E robuste mais stockage local non protégé au repos), ADVERSARIAL_SCORE `5.9/10` (attaque appareil partagé / XSS et accès intercompte non écartés), gap 0, plafond bloquant privacy `5.9/10`, RETAINED_SCORE `5.9/10`, statut `BLOCKED`. Ce score est **un jugement de revue** fondé sur le risque identifié, non un résultat de pentest ou une mesure expérimentale.

**Human gate réel :** approbation du modèle de menace, du design de clé/recouvrement et de la décision de stockage des données cliniques. Sans cela, pas de `D18_VERIFIED`, pas de merge clinique et pas de Vercel. **Next exact :** concevoir et documenter le schéma de protection des données au repos (clé, récupération, session, migration), faire revue sécurité ciblée, puis implémenter/tester après approbation du choix de risque ; parallèlement exécuter FUE clavier et captures BEFORE/AFTER comparables.

---

## 31/10/2026 — D18 Web — CI FUE étendue VERTE sur HEAD exact (nouvelle preuve, sans certification produit)

**Goal :** profil facultatif, historique de poids append-only, export chiffré/restauration D18 via vrais widgets Web, persistance et suppression patient-scoped. **Critère de succès du sous-lot automatisé :** 3 rapports obligatoires PASS au même SHA et leur artefact examiné, aucune assertion supprimée pour obtenir le vert.

**HEAD vérifié :** `91956649e826e18d149e4622cbe3275860b89e38` sur `feat/iamina-d18-web-progressive-profile-20261031` / [PR #1207](https://github.com/hraaaaf/IAMINA-MVP/pull/1207) OPEN/DRAFT. [D18 Web #41211784682](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41211784682) **SUCCESS** (job #124568181629, contrôle final « Strict D18 release gate — all independent evidence required » SUCCESS). [CI générale #41211784767](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41211784767) **SUCCESS**. [Artefact #13046393733](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41211784682/artifacts/13046393733) téléchargé, extrait et ses JSON effectivement lus :
- `report.json` **6/6 PASS** : vues réelles Flutter Chrome FR et AR RTL, 390×844, 768×1024, 1280×900, profil fermé/ouvert et dialogues export/restauration, sans erreurs reportées ; 24 captures dans l'artefact.
- `ui-file-roundtrip-report.json` **passed=true, 23/23 étapes PASS** : année 1994, identité préférant ne pas répondre ; pesée réelle 72,50 kg ; correction append-only 73,00 kg, lecture du même coffre SQLite physique (1 puis 2 lignes, chaîne `replaces_uuid`) via **sonde de lecture seule strictement dans l'hôte de test synthétique**, téléchargement Blob d'un fichier `.iamina` chiffré (1233 octets), sélection de fichier dans un nouveau contexte Chromium, déchiffrement/aperçu/consentement/restauration, rechargement et contrôle de la présence des deux versions, année et identité, suppression de la famille de versions puis vérification base vide après reload. 12 captures de ce parcours. La sonde `d18_e2e_proof=1` n'est **pas compilée dans `main.dart`** ; ne pas interpréter sa réussite comme un audit d'authentification hébergée.
- `encrypted-recovery-report.json` **8/8 PASS** : isolation A/B/A synthétique, mauvais secret et fichier altéré rejetés, transfert/validation C, refus de restauration destructrice.
- Vérification visuelle additionnelle des 8 vues sur planche contact : hiérarchie et sens de lecture FR/AR corrects sur états sélectionnés ; **aucun score de fidélité Target↔Render attribué**, les captures comparables `main` vs PR à mêmes états/hosts restent manquantes.

**Matrice de preuves partielle (FUE de décision, sans prétendre tout le périmètre clos) :**
| Fonction / risque D18 | Preuve et état |
| --- | --- |
| Profil / année / genre facultatifs, persistance | PASS synthétique Chrome + SQLite ; validation métier négative en test Dart, revue clavier réelle non complète |
| Poids daté, édition append-only et suppression après reload | PASS sur réel Chrome + lecture seule du coffre physique, 23 étapes communes |
| Export fichier chiffré / re-import avec consentement / persistance | PASS réel navigateur, reports exact-HEAD et WebCrypto |
| FR / AR RTL, mobile/tablette/desktop sur écrans et dialogues | PASS screenshots géométrie 6 cas ; **Tab/Shift+Tab/focus/lecteur d'écran NOT_RUN ou sans preuve complète** |
| Compte hébergé patient A→B→A, verrouillage et accès par identité | **NOT_RUN pour D18 hébergé**, séparation A/B/A démontrée seulement en navigateur synthétique via test crypto |
| Sécurité/confidentialité navigateur : IndexedDB, session locale, XSS, récupération et gestion de clé | **OPEN** : dossier de risque + approbation requises, pas de chiffrement IAMINA au repos ; sauvegarde `.iamina` chiffrée uniquement |
| Target ↔ Render Web BEFORE/AFTER strictement comparables aux mêmes états / host / tailles | **OPEN** : précédents hôtes de captures non équivalents ; score dimension visuelle **plafonné à 7,5/10**, pas de note inventée |

**Verdict correct :** `D18_AUTOMATED_E2E_PASS` au SHA ci-dessus, mais `D18_FUE_NO_GO / DECISION_OPEN / RELEASE_NOT_AUTHORIZED` tant que les preuves requises manquantes, arbitrages sécurité/privacy et Perfection Pass ne sont pas réalisés. En vertu de `docs/QUALITY_SCORING_POLICY.md`, pas de `VERIFIED`, pas de note totale ≥9 sans tous gates ; *deux reviewers indépendants ne sont pas obligatoires par défaut* (sauf note conservée ≥9,5 ou risque spécifique). Les anciennes phrases de ce handover mentionnant deux reviewers comme gate systématique sont historiques et **supplantées** par AGENTS.md et QUALITY_SCORING_POLICY.md.

**Perfection Pass, encore ouvert :** étudier une comparaison réellement équivalente BEFORE↔AFTER ; Tab/Shift+Tab/focus/RTL ; revue des menaces IndexedDB non chiffré et authentification hébergée multi-identités A→B→A ; statuer protection par chiffrement au repos, dérivation/conservation/récupération des clés et consentement. Le scénario d'anciennes sauvegardes pouvant ressusciter une donnée effacée est divulgué mais doit rester dans le modèle de menace. Corriger les défauts trouvés, relancer les preuves concernées, établir séparément EXECUTION_SCORE et ADVERSARIAL_SCORE (score conservé min), puis gate humain et merge **seulement après autorisation applicable**.

**Next exact :** confirmer sur PR et Notion l'état automatisé PASS et les limitations ; dresser la revue sécurité/privacy ciblée et matrice FUE restante, puis décider explicitement avec le responsable humain si IndexedDB non chiffré est acceptable pour une fonction clinique Web. Pas de déploiement Vercel sans accord explicite distinct. Après toute modification GitHub du document canonique, l'ancien SHA reste la preuve d'exécution des tests et ne vaut pas validation automatique du nouveau SHA docs.

---

## Reprise vérifiée — 31/10/2026 — REVUE PRE-FUSION

**Statut :** fonctionnel en Web synthétique, **NO GO merge / production** : gate UX et privacy à lever. PR [#1207](https://github.com/hraaaaf/IAMINA-MVP/pull/1207) OPEN/DRAFT ; `feat/iamina-d18-web-progressive-profile-20261031`. Baseline fonctionnelle avant cette modification de divulgation : `1acb97048a3c60f08c6b790ae702cee2b3cdd316`.

**Preuves automatisées exactes au SHA 1acb970** :
- [CI générale #41199621553](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41199621553) **SUCCESS** ;
- [D18 Web #41199621556](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41199621556) **SUCCESS** ; [artefact #13042555691](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41199621556/artifacts/13042555691) vérifié par extraction ;
- `report.json` 6/6 : Flutter profil réel FR/AR RTL 390×844, 768×1024, 1280×900, géométrie/browser sans erreur détectée ;
- `ui-file-roundtrip-report.json` true (8 checks) : formulaire Web, passphrase, téléchargement réel .iamina chiffré, nouvel environnement Chromium, sélection du fichier, aperçu, consentement, restauration et relecture année 1994 après reload ;
- `encrypted-recovery-report.json` 8/8 : A→B→A, wrong passphrase / tampering rejetés, transfert vers nouveau coffre C, vérification postimport et refus d'écraser C.
- Ce sont des tests **sur patients synthétiques** ; pas de vraie session hébergée multi-patient ni audit externe complet.

**Revue visuelle interne (review 1/2, pas d'approbation humaine)** : captures FR/AR aux 3 breakpoints examinées ; hiérarchie cartes, couleurs et typographies compatibles avec l'UX native IAMINA ; pas de débordement constaté ; les dialogues export/restauration sont présents. BEFORE main provient de [run #41184549732](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41184549732). AFTER synthétique est dans #41199621556. **Les hosts/fixtures diffèrent** (main app avec navigation inférieure et profil initial non complété contre D5 audit host avec profil fictif complété et alerte pays). Ne pas attribuer une note pixel-perfect : exiger une comparaison à host, états et viewports identiques, double reviewer et acceptation visuelle du SHA.

**UX de restauration et effacement :** une ancienne sauvegarde peut réintroduire des données supprimées. Le dialogue Web comporte désormais une mise en garde FR/EN/AR et le FUE vérifie sa présence en FR/AR. `D18BackupPreview.hasDemographics` ne signale plus « présentes » quand la ligne stockée contient les deux champs facultatifs à null ; test Dart ajouté. Ces changements de sécurité/UX attendent leur validation CI au nouveau SHA.

**Revue sécurité/privacy par inspection du code** :
- Le fichier `.iamina` est chiffré AES-256-GCM ; clé dérivée via PBKDF2-HMAC-SHA256 600k et sel aléatoire ; secret non persisté dans le formulaire ; enveloppe validée, D18-only, restauration transactionnelle, non destructive, testée dans navigateur réel.
- **Le coffre local SQLite Wasm / IndexedDB n'est PAS chiffré par IAMINA au repos**. Le chiffrement du fichier exporté ne protège pas le profil navigateur contre un accès local malveillant ni un XSS de même origine. Références primaires : [OWASP client-side databases](https://cheatsheetseries.owasp.org/cheatsheets/HTML5_Security_Cheat_Sheet.html), [OWASP Cryptographic Storage](https://cheatsheetseries.owasp.org/cheatsheets/Cryptographic_Storage_Cheat_Sheet.html). Données navigateur évincées/supprimées selon [MDN Storage quotas](https://developer.mozilla.org/en-US/docs/Web/API/Storage_API/Storage_quotas_and_eviction_criteria).
- Correctif information utilisateur dans cette PR : avertissement FR/EN/AR sous `D18BackupSection` : **export chiffré ≠ stockage navigateur chiffré** ; test navigateur FR/AR ajouté.
- Pas de conclusion de conformité ou protection contre XSS : décider un modèle de menace, tester session réelle A→B→A, vérifier confidentialité/données de santé et stockage local. Pour usage clinique, arbitrage réel **chiffrement au repos + gestion de clé** vs exploitation sur appareils maîtrisés et information/acceptation explicites ; ne pas choisir en silence.
- Session controller retire l'accès au coffre précédent sur transition d'auth, mais parcours réel connecté D18 multi-identités à tester.

**CI externe non Web** au précédent SHA 1acb970 : 14/15 workflows verts ; [TD-008 Android #41199621412](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41199621412) rouge car **Dart Development Service failed to start** sur émulateur, 0 test métier exécuté. Une seule relance ciblée du job `124532669723` lancée sur le même SHA, tentative 2. Conserver comme run séparé, non lié au D18 Web.

## Gates restant OPEN — ne pas merger
1. CI et D18 test ciblé verts au **HEAD produit + avertissement privacy** ; actualiser SHA preuves.
2. Capture BEFORE/AFTER réellement comparables, double revue UX/accessibilité, score et approbation humaine au SHA final.
3. Revue indépendante sécurité/privacy + arbitrage explicite du stockage IndexedDB au repos et preuve auth réelle A→B→A avant clinique.
4. Suivre TD-008 natif séparément ; après accord humain, merge et postmerge avec nouveaux états prouvés.
5. **Pas de Vercel sans autorisation explicite distincte.**

## Next exact
Vérifier CI et D18 au nouveau HEAD, reviewer UX 390/768/1280 + RTL sur contexte identique, modéliser les menaces local/XSS et demander décision humaine sur le stockage au repos et signoff visuel ; ne jamais déclarer D18 DONE prématurément.

## Rappel
Chantier A = 4/13 (30,8%) closes ; D18 OPEN.
