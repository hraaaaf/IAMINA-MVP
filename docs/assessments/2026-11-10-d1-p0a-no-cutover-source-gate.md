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
- Revue adversariale : un helper transitif contenant `deleteDatabase('amina')` échappait au premier garde ; contournement reproduit sur fixture jetable, puis corrigé. Deux faux positifs liés au parsing ont imposé de passer à des directives Dart complètes, pas à une recherche globale de morceaux de texte.
- `tools/tests/test_d1_legacy_cutover_guard.py` : **11/11** tests unitaires PASS sur code source de la branche ; garde sur graphe du dépôt PASS. La vérification reste une heuristique de défense en profondeur, pas une analyse sémantique ni un verrou runtime.
- `tools/d1_p0a_stale_tab_negative_probe.js` : 24 assertions Chromium et 24 WebKit, **48/48 PASS** en CI sur le dernier HEAD contrôlé. Ce PASS signale que l'ancien écrivain peut rester actif : il confirme un **risque**, pas une migration sûre.
- `frontend/lib/ui_d1_p0a_real_drift_legacy_probe_main.dart` + `tools/d1_p0a_real_drift_browser_probe.js` + workflow `d1-p0a-real-drift-vfs-proof.yml` : compilation Flutter Web distincte et non déployée ; profil Chrome/Playwright jetable, SQLite WASM via les vrais constructeurs `AppDatabase`.

## Preuve physique v12 (synthetique uniquement)
- [Workflow #42905600841](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/42905600841), HEAD de code évalué `7b17cfed3b1ed8e0e6ac73b14166b8d73859bb0f` : **completed/success** ; rapport JSON téléchargable depuis l'artefact du run.
- **9 phases / 9 PASS :** `seed_legacy` → `seed_a` → `late_legacy_write` → `seed_b` → `verify_a` → `verify_b` → `verify_legacy` → `verify_a` → hard reload `verify_a`.
- Chaque phase utilise la vraie connexion Drift/SQLite WASM, vérifie les lignes synthétiques attendues / l'absence des lignes d'autres coffres, puis exécute `PRAGMA integrity_check = ok`. Conservation après fermeture, navigation et recharge complète démontrée.
- `late_legacy_write` emploie le **constructeur legacy du bundle v12 actuel** après création de A ; ce n'est **pas** un ancien bundle JS d'une vraie version précédente ni une course de deux onglets réellement concurrents.
- Le mécanisme VFS exact sélectionné en interne (OPFS ou fallback IndexedDB) n'a pas été identifié indépendamment ; ne pas surévaluer cette preuve.

## Preuves NON obtenues / gates bloquants
1. **Véritable ancien bundle** offline (historique), plusieurs onglets simultanés, verrou physique à coupure sécurisée, vieux handles en versionchange, A→B→A avec collisions réelles.
2. **Migration depuis anciens schémas**, surtout v1→v12 et v5→v12 ; première version visible du code `database.dart` dans l'historique Git consulté : `a1d46f9b`, `schemaVersion=5`. Une source v1 authentifiée n'a pas été retrouvée ici.
3. Crash pendant transactions, journaux SQLite, intégrité byte-level, sauvegarde/restauration vérifiée, replay/sync `client_uuid`, chiffrement, récupération/perte de clé, exactitude des mappings patient.
4. **Revue indépendante** sécurité/données et convergence sur exact HEAD final ; contrôles CI finaux après tout changement documentaire ou applicatif.

**Verdict :** garde et preuve de persistance v12 utiles, mais **migration clinique D1 P0-A toujours NO-GO**, aucune approbation de release. **Next exact :** contrôler les CI exact-HEAD après la documentation, faire réviser le garde par une personne/agent indépendant (builder ≠ reviewer), puis élaborer un banc de vrais bundles historiques sur une origine isolée avec scénarios versionchange/crash/restore. Aucun merge, aucun déploiement Vercel ni donnée patient réelle sans leurs gates explicites.
