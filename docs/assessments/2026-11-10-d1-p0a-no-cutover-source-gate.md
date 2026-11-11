# IAMINA D1 P0-A — SAFE-HOLD / no-cutover (10 novembre 2026)

**Décision active :** [roadmap canonique D1–D12](https://app.notion.com/p/3df77c66336281f5b308ec17f7f0a63b). Conserver l'historique, prouver chiffrement/recovery avant activation patient et n'autoriser qu'une migration volontaire, jamais implicite. **CUTOVER : NO-GO.**

## Goal
Empêcher qu'un changement accidentel de code active un migrateur/chiffreur expérimental ou attribue l'ancien coffre `amina` à un compte authentifié. Préserver ce blocage pendant la recherche de preuves réelles sur des bases jetables.

## État sur main / frontière clinique
- `AppDatabase.defaults()` utilise la base historique `amina`, sans identité patient.
- `AppDatabase.forPatientVault(scope)` utilise une autre base physique nommée par `scope.databaseName` ; les noms patient Django, appareil local et audit restent distincts.
- Un ancien JS/PWA hors ligne peut encore accéder au coffre historique sans prendre les Web Locks ajoutés plus tard.
- Aucun code Flutter de production, de base, de SW, de migrateur, de chiffreur ni de Vercel n'est changé dans cette PR.

## Protection test-only ajoutée
- `tools/d1_legacy_cutover_guard.py` part de quatre points d'entrée Dart, parcourt imports/exports, imports conditionnels et `part` atteignables. Il refuse un `d18_*.dart` expérimental, les appels destructifs explicitement connus dans tout le graphe atteignable, ainsi que des modifications évidentes des constructeurs et espaces de noms de coffres.
- Revue contradictoire (même exécutant, **non indépendante**) : trois contournements de sources synthétiques reproduits puis corrigés : (a) `deleteDatabase('amina')` dans un helper transitif, (b) `PatientVaultScope.nativeDjango` réaffecté au legacy `amina` avec anciens préfixes laissés en commentaire, (c) constructeur legacy modifié dont le texte attendu existait dans un constructeur leurre. Le contrôle limite maintenant les invariants à chaque initialiseur, épingle l'empreinte SHA-256 du fichier `patient_vault_scope.dart` et couvre imports conditionnels/`part`. Chaque modification future de ce scope est fail-closed jusqu'à revue volontaire et mise à jour explicite de l'empreinte. Les faux positifs d'analyse ont été corrigés en exploitant les directives Dart complètes.
- `tools/tests/test_d1_legacy_cutover_guard.py` : **15/15** tests unitaires PASS sur le code final contrôlé localement et garde sur graphe réel PASS ; CI GitHub exacte à relever sur le dernier commit documentaire. La vérification reste une heuristique de défense en profondeur, pas une analyse sémantique ni un verrou runtime.
- `tools/d1_p0a_stale_tab_negative_probe.js` : 24 assertions Chromium et 24 WebKit, **48/48 PASS** en CI sur le dernier HEAD contrôlé. Ce PASS signale que l'ancien écrivain peut rester actif : il confirme un **risque**, pas une migration sûre.
- `frontend/lib/ui_d1_p0a_real_drift_legacy_probe_main.dart` + `tools/d1_p0a_real_drift_browser_probe.js` + workflow `d1-p0a-real-drift-vfs-proof.yml` : compilation Flutter Web distincte et non déployée ; profil Chrome/Playwright jetable, SQLite WASM via les vrais constructeurs `AppDatabase`.

## Preuve physique v12 (synthetique uniquement)
- [Workflow #42905600841](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/42905600841), HEAD de code évalué `7b17cfed3b1ed8e0e6ac73b14166b8d73859bb0f` : **completed/success** ; rapport JSON téléchargable depuis l'artefact du run.
- **9 phases / 9 PASS :** `seed_legacy` → `seed_a` → `late_legacy_write` → `seed_b` → `verify_a` → `verify_b` → `verify_legacy` → `verify_a` → hard reload `verify_a`.
- Chaque phase utilise la vraie connexion Drift/SQLite WASM, vérifie les lignes synthétiques attendues / l'absence des lignes d'autres coffres, puis exécute `PRAGMA integrity_check = ok`. Conservation après fermeture, navigation et recharge complète démontrée.
- `late_legacy_write` emploie le **constructeur legacy du bundle v12 actuel** après création de A ; ce n'est **pas** un ancien bundle JS d'une vraie version précédente ni une course de deux onglets réellement concurrents.
- Le mécanisme VFS exact sélectionné en interne (OPFS ou fallback IndexedDB) n'a pas été identifié indépendamment ; ne pas surévaluer cette preuve.

## Preuve de migration depuis le vrai code historique v5 (synthétique uniquement)
- **Source Git réellement compilée :** `a1d46f9be5f2190a1e8380f28fe4679954f9863f`, dont `AppDatabase.schemaVersion=5` ; ce n'est pas une simple base SQL v5 recréée manuellement. Le même profil Playwright Chromium et la même origine localhost hébergent les bundles `/historical/` (v5) et `/current/` (v12) sous chemins distincts.
- [Run exact #42909817420](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/42909817420) : **completed/success**, code courant `8e6315a2b281eab6a8bab991f6237b51e50be801` ; artefact GitHub **#13807555471**. Trois phases `historical_v5_seed`, `v12_upgrade_v5`, `v12_reopen_after_upgrade` : **3/3 PASS**, avec hard reload également PASS.
- L'ancien bundle crée des enregistrements **entièrement synthétiques** dans deux tables (`log_entries` et `patient_profiles`), incluant `client_uuid`, `sync_status`, un type de diabète fictif, un traitement fictif et un horodatage de consentement fictif. Le bundle v12 ouvre la même base legacy `amina`, confirme `PRAGMA user_version=12`, la conservation des champs de ces deux tables, le nombre de logs, l'absence d'éléments scoped A/B et `PRAGMA integrity_check=ok`. Ces assertions sont revérifiées après fermeture et recharge.
- Première méthode historique : checkout additionnel GitHub Actions bloqué *avant compilation* par un gitlink invalide de `.claude/worktrees` dans l'ancien commit ; contourné sans modifier cet historique via `git worktree add --detach`. Deuxième méthode : **preuve navigateur validée** sur synthétique.
- Ce PASS prouve **une trajectoire séquentielle v5→v12 pour deux enregistrements synthétiques**, pas la migration exhaustive de tous les schémas ni un fencing de vieux onglets encore vivants. Le backend VFS exact (OPFS ou IndexedDB fallback), le cache PWA distribué, un vieux handle simultané, la v1 authentique, le crash et les restaurations chiffrées restent à éprouver.

## Preuves NON obtenues / gates bloquants
1. **Véritable ancien bundle déployé et encore vivant** en cache PWA/offline, plusieurs onglets simultanés, verrou physique à coupure sécurisée, vieux handles en versionchange, A→B→A avec collisions réelles.
2. **Migration exhaustive depuis les anciens schémas**, dont v1→v12 et v5→v12 avec volumes, profils multiples, conflits, crashes et anciens onglets. Une migration séquentielle partielle v5→v12 sur deux enregistrements synthétiques est prouvée, sans généralisation. La source v1 authentique n'a pas été retrouvée.
3. Crash pendant transactions, journaux SQLite, intégrité byte-level, sauvegarde/restauration vérifiée, replay/sync `client_uuid`, chiffrement, récupération/perte de clé, exactitude des mappings patient.
4. **Revue indépendante** sécurité/données et convergence sur exact HEAD final ; contrôles CI finaux après tout changement documentaire ou applicatif.

**Verdict :** garde et preuve de persistance v12 utiles, mais **migration clinique D1 P0-A toujours NO-GO**, aucune approbation de release. **Next exact :** contrôler les six workflows du HEAD final après cet amendement documentaire ; obtenir une revue effective par un reviewer séparé (la demande IA09/IA08/IA15 est publiée dans la conversation PR, **aucune review indépendante reçue à cette date**) ; poursuivre sur la vraie PWA historique avec vieux onglets simultanés, versionchange/crash/restore et recherche de source v1. Aucun test CI positif n'autorise une migration patient. Aucun merge, aucun déploiement Vercel ni donnée patient réelle sans leurs gates explicites.
