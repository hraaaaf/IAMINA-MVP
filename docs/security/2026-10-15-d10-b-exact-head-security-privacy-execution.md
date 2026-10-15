# IAMINA D10-B — exécution contradictoire sur HEAD exact (sécurité + confidentialité)

**15 octobre 2026 · référence auditée :** `58f0dc940449e0cdace099df5350be79e34d53b4` · [Décision D10 #968](https://github.com/hraaaaf/IAMINA-MVP/issues/968) · [Gate #1013](https://github.com/hraaaaf/IAMINA-MVP/issues/1013)

**Rôle exécuté :** ChatGPT, deux analyses thématiques (sécurité, puis confidentialité), relecture directe de 15 fichiers du dépôt et confrontation aux standards primaires. **Pas de deux experts indépendants, aucune signature professionnelle, aucune inspection de binaire natif, aucun test physique, aucune preuve de chiffrement observée.**
**Verdict : CHANGES_REQUIRED / NO-GO pour l'activation de D10-B avec de vraies données médicales, sur iOS, Android et Web.**
**Important :** ce n'est pas un refus du choix produit B, ni une preuve de fuite actuelle, ni un verdict sur toutes les fonctionnalités IAMINA.

## Goal et critères

**Goal :** permettre la suppression volontaire du verrou supplémentaire IAmina *sans* rendre les données médicales d'un compte accessibles à un tiers, ni élargir la synchronisation clinique / les consentements.

**Succès observable :** propriétaire vérifié, appareil qualifié, protection effective du coffre au repos y compris backup/exports, préférence explicite et réversible propre au couple compte+appareil, zéro transfert non autorisé, parcours A→B→A et récupération robuste ; tests instrumentés sur builds finaux puis signatures séparées sécurité + privacy.

## Vérifications exécutées (nouvelle passe exacte)

| Contrôle de source | Résultat |
| --- | --- |
| Coffre `AppDatabase.forPatientVault` / `driftDatabase` | Configuration SQLite+IndexedDB vérifiée ; **pas de provision de clé / SQLCipher dans le constructeur inspecté** |
| `AndroidManifest.xml` `allowBackup` / `dataExtractionRules` | **Absents du manifeste source** ; manifeste fusionné RELEASE **non inspecté** |
| iOS `Info.plist` et Xcode project `default-data-protection`/classe DB | **Non trouvés dans ces deux fichiers** ; protection des fichiers en exécution **non mesurée** |
| `app_lock_authenticator_factory.dart` + stub natif | Sélection non-web du stub ; `capability=unavailable`, enroll/unlock `unsupported_platform` |
| `AppLockService` | `initialize` fail-closed, `recoveryRequired` si disparition du verrou avec coffre ; **aucune option B active** |
| `AuthService.enrollLocalDevice` | Commentaire source : continuité d'appareil **ne constitue pas une authentification forte** |
| `PatientVaultAppHost` + `main.dart` | Synchro clinique conditionnée aussi à `appLock.isUnlocked` : NE PAS simuler `true` pour B |
| `ApiClient.canSyncClinicalData` | **Protection favorable vérifiée : false par défaut**, sauf permission spécifique de tests synthétiques ; distinguer de l'absence de verrou |
| `LocalBackup` | `jsonEncode` de journaux/profil/messages/traitements, **sans chiffrement dans ces méthodes**. Aucune diffusion réelle démontrée |
| Trois tests D10-B dans `app_lock_service_test.dart` | Présents et intégrés dans main : protection contre faux opt-out/recovery non vérifiée/cold start ; **pas de parcours B réel testé** |

**Preuve GitHub/CI :** [CI main #38694366634](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38694366634) **SUCCESS** sur `58f0dc940449e0cdace099df5350be79e34d53b4`; pré-audit antérieur [PR #1017](https://github.com/hraaaaf/IAMINA-MVP/pull/1017) et handover [#1018](https://github.com/hraaaaf/IAMINA-MVP/pull/1018) fusionnés. Aucune CI de fonctionnalité B inexistante n'est revendiquée.

## Passe A : revue de sécurité

| ID | Gravité / preuve directe | Risque si on active B | Condition avant GO |
| --- | --- | --- | --- |
| **S01** | **Bloquant Web** · [database.dart L107–146](https://github.com/hraaaaf/IAMINA-MVP/blob/58f0dc940449e0cdace099df5350be79e34d53b4/frontend/lib/data/drift/database.dart#L107-L146) | IndexedDB sépare les **origines** web, pas les personnes réutilisant un même profil navigateur ; protection applicative du coffre non démontrée | Qualifier menace XSS, navigateur partagé, autorisation du coffre/chiffrement/clé ; si non réalisable, B désactivée pour Web |
| **S02** | **Bloquant Android** · [AndroidManifest.xml L11–14](https://github.com/hraaaaf/IAMINA-MVP/blob/58f0dc940449e0cdace099df5350be79e34d53b4/frontend/android/app/src/main/AndroidManifest.xml#L11-L14) | Aucune politique explicitement déclarée dans le manifeste source sur le backup des données cliniques | Inspecter le *merged manifest release*, cloud/D2D ; exclusions/chiffrement prouvés et restauration fictive contrôlée |
| **S03** | **Bloquant iOS** · [Info.plist](https://github.com/hraaaaf/IAMINA-MVP/blob/58f0dc940449e0cdace099df5350be79e34d53b4/frontend/ios/Runner/Info.plist), [project.pbxproj](https://github.com/hraaaaf/IAMINA-MVP/blob/58f0dc940449e0cdace099df5350be79e34d53b4/frontend/ios/Runner.xcodeproj/project.pbxproj) | Protection niveau DB/WAL/SHM inaccessible/non visible au niveau source inspecté ; après le premier déverrouillage, le défaut iOS ne remplace pas forcément un verrou app | Attester classe de chaque fichier et protection du backup, état verrouillé, snapshot ; essai appareil natif |
| **S04** | **Bloquant native** · [factory L1–6](https://github.com/hraaaaf/IAMINA-MVP/blob/58f0dc940449e0cdace099df5350be79e34d53b4/frontend/lib/services/app_lock_authenticator_factory.dart#L1-L6), [stub L1–19](https://github.com/hraaaaf/IAMINA-MVP/blob/58f0dc940449e0cdace099df5350be79e34d53b4/frontend/lib/services/app_lock_authenticator_stub.dart#L1-L19) | Le chemin d'authentificateur non-web est volontairement unsupported ; aucun contrôle OS qualifié spécifique à D10 B | Concevoir et tester une attestation d'identité propriétaire + protection OS native, sans faux déverrouillage |
| **S05** | **Haut identité** · [auth_service.dart L248–260](https://github.com/hraaaaf/IAMINA-MVP/blob/58f0dc940449e0cdace099df5350be79e34d53b4/frontend/lib/services/auth_service.dart#L248-L260), [scope](https://github.com/hraaaaf/IAMINA-MVP/blob/58f0dc940449e0cdace099df5350be79e34d53b4/frontend/lib/data/drift/patient_vault_scope.dart) | ID local stable n'est pas une preuve forte ; opt-out hérité/tampered pourrait ouvrir mauvais coffre | Option versionnée signée/liée au bon propriétaire+appareil ; step-up, A→B→A, recovery fail-closed |
| **S06** | **Haut egress** · [main.dart L99–108](https://github.com/hraaaaf/IAMINA-MVP/blob/58f0dc940449e0cdace099df5350be79e34d53b4/frontend/lib/main.dart#L99-L108), [patient_vault_app_host.dart L154–163](https://github.com/hraaaaf/IAMINA-MVP/blob/58f0dc940449e0cdace099df5350be79e34d53b4/frontend/lib/services/patient_vault_app_host.dart#L154-L163) | Le verrou pilote aussi la permission de synchro ; simuler `isUnlocked` pourrait contourner un niveau d'autorisation | Séparer droit de lecture, assertion verrou, session propriétaire, egress ; préserver default-deny [api_client.dart L274–281](https://github.com/hraaaaf/IAMINA-MVP/blob/58f0dc940449e0cdace099df5350be79e34d53b4/frontend/lib/services/api_client.dart#L274-L281) |
| **S07** | **Haut backups/export** · [local_backup.dart L8–11,25–65](https://github.com/hraaaaf/IAMINA-MVP/blob/58f0dc940449e0cdace099df5350be79e34d53b4/frontend/lib/data/drift/local_backup.dart#L8-L65) | JSON médical retourné en clair dans les méthodes de backup ; risque si ensuite exposé à destination non sûre | Audit des call sites et destination, protection/chiffrement de l'export, test sentinelle, interdiction export via opt-out sans step-up |

**Contrôles favorables et limites :** [AppLockService L54–109](https://github.com/hraaaaf/IAMINA-MVP/blob/58f0dc940449e0cdace099df5350be79e34d53b4/frontend/lib/services/app_lock_service.dart#L54-L109) bloque la disparition/corruption des identifiants ; [ApiClient L274–282](https://github.com/hraaaaf/IAMINA-MVP/blob/58f0dc940449e0cdace099df5350be79e34d53b4/frontend/lib/services/api_client.dart#L274-L282) refuse le transport clinique par défaut. Ces garanties existantes sont importantes, mais ne prouvent pas B.

## Passe B : revue confidentialité et conformité

- **Données en jeu** : glycémie, diagnostics/profils, traitements, messages, médicaments, documents, sauvegardes. L'option B sur un appareil **déjà déverrouillé ou partagé** facilite l'accès physique aux données ; risque identifié, pas fuite constatée.
- **P-01 (haut)** : information et consentement à l'option B doivent être compréhensibles, non cochés d'avance, réversibles et **distincts du consentement IA**, du partage/export et de la synchronisation.
- **P-02 (haut)** : enregistrer analyse des destinataires, lieux de traitement, durées de conservation, effacement, sauvegardes et responsabilité du traitement. La [CNDP](https://www.cndp.ma/notifier-un-traitement/) mentionne l'autorisation préalable pour les traitements de données sensibles, dont données de santé ; **aucune preuve de la situation juridique/finalité/démarche IAMINA n'a été obtenue**. Examen par juriste/responsable privacy requis.
- **P-03 (haut)** : pas de preuve signée externe de protection OS/chiffrement pour Web, Android, iOS ni de validation sur appareil. D31 physique sur D7/D9 ne remplace pas la validation sécurité spécifique D10-B.

**Références primaires vérifiées :** [OWASP MASVS-STORAGE-1](https://mas.owasp.org/MASVS/controls/MASVS-STORAGE-1/), [MASVS-AUTH-1](https://mas.owasp.org/MASVS/controls/MASVS-AUTH-1/), [MASTG protection fichiers iOS](https://mas.owasp.org/MASTG/tests/ios/MASVS-STORAGE/MASTG-TEST-0052/), [Apple niveaux de protection](https://developer.apple.com/documentation/uikit/encrypting-your-app-s-files), [Android allowBackup et exceptions D2D](https://developer.android.com/guide/topics/manifest/application-element), [MDN IndexedDB same-origin](https://developer.mozilla.org/en-US/docs/Web/API/IndexedDB_API/Basic_Terminology), [CNDP](https://www.cndp.ma/notifier-un-traitement/).

## Verdict final et preuve d'indépendance

| Web | Android | iOS |
| --- | --- | --- |
| **NO-GO release B** | **NO-GO release B** | **NO-GO release B** |

- **VÉRIFIÉ** : chemins de code, absences limitées aux fichiers inspectés, défaut OS selon sources officielles, statut CI main.
- **INCERTAIN** : contenu des binaires signés et merged manifests, at-rest OS réel, backups réels, sécurité Web sur navigateur physique, comportement d'une fonctionnalité B **non implémentée**.
- **NON EFFECTUÉ** : pentest, instrumentation iOS/Android, chiffrement réellement mesuré, tests UI BEFORE/AFTER, 2 professionnels indépendants, conformité juridique formelle.
- **Audit / avis externe indépendant** : **NON OBTENU**. Il n'existe aucune signature qualifiée dans [#1013](https://github.com/hraaaaf/IAMINA-MVP/issues/1013). Le même assistant ne peut se déclarer indépendamment certifieur.
- **Séquence restante** : (1) deux revues externes signées ; (2) architecture coffre et traitements des blockers ; (3) implémentation B sécurisée ; (4) tests T01–T10 et UI vérifiée ; (5) CI/merge/postmerge ; (6) décision de mise en service distincte.

**Prochaine action exacte :** remettre le [prompt de revue](https://github.com/hraaaaf/IAMINA-MVP/blob/main/docs/security/2026-10-15-d10-b-independent-audit-prompt.md) et ce rapport à des professionnels externes distincts et obtenir leurs décisions nominatives dans #1013. Conserver les protections actuelles jusqu'à cette preuve. P5 historique : 50 %.
