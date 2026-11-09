# IAMINA D10-B — Rapport de pré-audit sécurité et confidentialité
**Date :** 15 octobre 2026 · **SHA audité :** `de2afee9f5b8fe11fa806c361f246eae6854bbd0`  
**Prompt :** [2026-10-15-d10-b-independent-audit-prompt.md](./2026-10-15-d10-b-independent-audit-prompt.md)  
**Nature :** deux passes contradictoires sécurité/privacy par ChatGPT. Ce document ne constitue PAS deux revues humaines indépendantes, ni une certification. Aucune signature externe, aucun test sur vrai patient.  
**Verdict : `CHANGES_REQUIRED — NO-GO` pour activer D10-B (app-lock facultatif) avec données médicales réelles.**

## Résultat par plateforme
| Plateforme | Verdict | Justification |
| --- | --- | --- |
| **Web** | **NO-GO** | Coffre SQLite/IndexedDB ; pas de chiffrement de coffre démontré ; même origine = frontière web, pas séparation des personnes qui utilisent le même profil navigateur |
| **Android** | **NO-GO** | Manifeste sans politique explicite backup/données sensibles ; pas de chiffrement de DB démontré ; backend app-lock natif non implémenté |
| **iOS** | **NO-GO** | Protection renforcée du fichier DB/WAL/SHM non démontrée ; backend app-lock natif non implémenté ; contrôle post-verrouillage non vérifié |

Ces jugements sont des **décisions de gate release fondées sur une absence de preuve suffisante**, et non la constatation d'une fuite effective.

## Passe 1 — Security reviewer (pré-audit IA)

| ID | Niveau | Preuve du code | Correction minimale vérifiable |
| --- | --- | --- | --- |
| F01 | Bloquant | `frontend/lib/data/drift/database.dart` lignes 107–146 : `driftDatabase` / `DriftWebOptions`, sans clé ni chiffrement applicatif visible. [MDN IndexedDB](https://developer.mozilla.org/en-US/docs/Web/API/IndexedDB_API/Basic_Terminology) | Attester stockage médical au repos et accès même navigateur/profil partagé ; à défaut B web refusée |
| F02 | Bloquant | `frontend/android/app/src/main/AndroidManifest.xml` : pas de `allowBackup` ou `dataExtractionRules`. [Android manifest](https://developer.android.com/guide/topics/manifest/application-element) : allowBackup par défaut true, nuances OEM | Lire manifeste fusionné RELEASE, exclure/chiffrer données médicales, tester sauvegarde et restauration fictives |
| F03 | Bloquant | `frontend/ios/Runner/Info.plist` et `AppDelegate.swift` : pas de configuration app explicite de protection DB. [Apple Data Protection](https://developer.apple.com/documentation/uikit/encrypting-your-app-s-files) : défaut iOS « until first authentication » | Attester classe des fichiers SQLite/WAL/SHM, tester accès verrouillé et sauvegardes sur appareil |
| F04 | Bloquant | `frontend/lib/services/app_lock_authenticator_factory.dart` choisit web ou `app_lock_authenticator_stub.dart`; ce stub renvoie `unavailable` / `unsupported_platform` | Implémenter et tester une méthode locale forte native réelle et son fallback sûr, sans faux déverrouillage |
| F05 | Haut | `AuthService.enrollLocalDevice()` : continuité locale sans authentification forte ; `patient_vault_scope.dart` : namespace distinct de l'autorisation | Réauthentifier le bon propriétaire ; préférence B attachée à compte+appareil, non falsifiable, tests A→B→A |
| F06 | Haut | `main.dart`, `patient_vault_app_host.dart`, `api_client.dart` conditionnent aussi le transport clinique à `appLock.isUnlocked` | Séparer accès au coffre, assertion app-lock, identité et droit d'émission ; préserver AuthEpoch + deny egress |
| F07 | Haut | `frontend/lib/data/drift/local_backup.dart` renvoie des JSON de profil/mesures/messages, sans chiffrement dans la fonction | Auditer les destinations ; protéger export/backup et tester les données sentinelles |
| F08 | Moyen | `frontend/test/services/app_lock_service_test.dart` protège contre une fausse préférence ; **aucun état B runtime n'existe** | Tests de vraie activation/désactivation, récupération, stockage et langues, pas seulement tests du verrou actuel |

**Éléments favorables :** le verrou actuel échoue fermé en cas de credential perdue/corrompue ; récupération distante vérifiée ; tests négatifs D10-B [PR #1012](https://github.com/hraaaaf/IAMINA-MVP/pull/1012) fusionnés. **Ces tests ne certifient pas l'opt-out B non implémenté.**

## Passe 2 — Privacy reviewer (pré-audit IA)

- Données sensibles en jeu : glycémie, type de diabète, traitements, messages, événements médicaments, documents et sauvegardes. Sur appareil ou navigateur déjà ouvert/partagé, enlever le second verrou augmente l'accès possible à ces données. **Risque déduit, pas fuite constatée.**
- Ne pas confondre la préférence B avec une permission IA, export ou synchronisation. Il faut des autorités distinctes et une information claire sur l'appareil partagé.
- La [CNDP du Maroc](https://www.cndp.ma/notifier-un-traitement/) exige en principe une formalité d'autorisation préalable pour certains traitements de données de santé. L'applicabilité et les démarches propres à IAMINA **ne sont pas vérifiées ici**, doivent être examinées par un expert local.
- Aucun responsable sécurité ou confidentialité externe n'a émis de signature ; [gate #1013](https://github.com/hraaaaf/IAMINA-MVP/issues/1013) reste ouvert.

**Verdict privacy de l'IA : `CHANGES_REQUIRED`.** Ne vaut pas sign-off professionnel.

## Matrice de vérification (non exécutée pour B)
T01 installation saine / T02 coffre préexistant et consentement à la préférence / T03 credential perdue ou corrompue / T04 A→B→A et tampering / T05 OS sans verrou et WebAuthn absent / T06 arrière-plan, screenshots, cold restart / T07 iOS/Android backups, IndexedDB et export JSON / T08 offline et synchronisation clinique refusée / T09 UI FR/EN/AR RTL avant-maquette-après 390×844, 768×1024, 1280×900 / T10 release build et manifest/entitlements réellement inspectés. **Tous NON TESTÉS pour une option B active.**

## Sources et CI exactes
- [OWASP MASVS-STORAGE-1](https://mas.owasp.org/MASVS/controls/MASVS-STORAGE-1/) ; [STORAGE-2](https://mas.owasp.org/MASVS/controls/MASVS-STORAGE-2/) ; [MASWE-0017](https://mas.owasp.org/MASWE-0017/).
- Apple, Android, MDN et CNDP cités sous constats.
- CI D10-B TD-014 [#38657348652](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38657348652) **SUCCESS**, CI finale [#38692754816](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38692754816) **SUCCESS** à `de2afee9f5b8fe11fa806c361f246eae6854bbd0`. Elles concernent le comportement *actuel*, pas un opt-out.
- Ce rapport = **lecture de code/standards**. Pas de test Flutter supplémentaire, preuve de chiffrement, audit réseau, compilation de release, BEFORE/AFTER UX ou outil tiers exécuté.

## Suite obligatoire
1. Examiner stockage, code d'identité, protection OS, backup et Web par deux spécialistes réellement indépendants.
2. Obtenir dans [#1013](https://github.com/hraaaaf/IAMINA-MVP/issues/1013) les preuves versionnées et décisions signées **sécurité ET confidentialité**, plateforme par plateforme ; aucun avis actuellement reçu.
3. Seulement après les approbations : implémentation B contrôlée, T01–T10, BEFORE/AFTER et CI, merge/postmerge. Sinon rester fail-closed et **ne pas offrir B sur la plateforme non qualifiée**.
4. D31 tests physiques D7/D9 [#1006](https://github.com/hraaaaf/IAMINA-MVP/issues/1006) reste une porte distincte.

**CERTIFICATEUR EXTERNE : AUCUN. VERDICT D'EXÉCUTION IA : CHANGES_REQUIRED / NO-GO. D10-B OPEN.**
