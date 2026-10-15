## 15 octobre 2026 — D10-B iOS sauvegardes locales : merge #1053, limites établies

**Goal exact :** réduire l'inclusion accidentelle dans les sauvegardes iOS des fichiers SQLite d'un coffre patient, sans déplacer la base ni toucher au verrou d'accès. **Le choix B de verrou facultatif reste NON implémenté.**

**Succès observé sur HEAD PR `73716e7fcb2b9060b6a5de369374c449102ad0c0` :** [D10 iOS native Swift #38716161853](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38716161853) **SUCCESS** : compilation de la fonction Foundation Swift présente dans `AppDelegate.swift`, correspondance du préfixe patient et des extensions DB/WAL/SHM, exclusion des fichiers sans rapport, idempotence et lecture de `isExcludedFromBackup` **sur macOS**. [CI générale #38716161822](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38716161822) **SUCCESS**. [Packaging iOS #38716161813](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38716161813) **SUCCESS** (build release sans signature). Les trois résultats concernent le même HEAD, sans données patient réelles.

**Fusion constatée :** [PR #1053](https://github.com/hraaaaf/IAMINA-MVP/pull/1053) **MERGED** dans `main@5d3d81a7841257b497cf8e01f1380e2c33d1accf`. Relecture directe du fichier `AppDelegate.swift`, du `SceneDelegate.swift` et du [document explicatif](https://github.com/hraaaaf/IAMINA-MVP/blob/main/docs/security/2026-10-15-d10-b-ios-backup-exclusion.md) sur le nouveau main. **CI post-merge** [D10 iOS #38717221683](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38717221683) et [CI #38717221667](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38717221667) : `IN_PROGRESS` au contrôle initial, à revérifier avant clôture de la preuve post-merge.

**Limites de preuve et risques résiduels :**
- Trois tentatives de construire et exécuter les **XCTest sur iOS Simulator** ont échoué *avant le lancement des tests* avec `Framework 'Pods_Runner' not found`. [Issue de diagnostic #1057](https://github.com/hraaaaf/IAMINA-MVP/issues/1057) **OPEN**. Ni le changement de configuration CocoaPods Debug ni Flutter 3.41.4 n'ont résolu. Le test macOS n'est **pas** un XCTest iOS.
- `isExcludedFromBackup` reste une indication de non-sauvegarde susceptible d'être réinitialisée par modifications de fichiers. Les bases créées entre les callbacks peuvent temporairement ne pas recevoir la marque ; aucune restauration iCloud ou vérification sur appareil réel n'est prouvée. [Issue protection iOS #1052](https://github.com/hraaaaf/IAMINA-MVP/issues/1052) **OPEN**. Pas de preuve de protection `NSFileProtectionComplete` du DB/WAL/SHM.
- [Web #1054](https://github.com/hraaaaf/IAMINA-MVP/issues/1054), [transfert Android→iOS #1048](https://github.com/hraaaaf/IAMINA-MVP/issues/1048), [D10 #968](https://github.com/hraaaaf/IAMINA-MVP/issues/968), [gate #1013](https://github.com/hraaaaf/IAMINA-MVP/issues/1013) **OPEN**. Pas de mise en production du verrou facultatif, ni Vercel, ni certification clinique/juridique.

**Next exact :** contrôler les runs iOS post-merge puis rétablir le simulateur via preuve native des frameworks manquants, et engager la séparation du droit de coffre/synchro + chiffrement Web / identité forte avant d'implémenter l'option B. P5 **50 % historique**, sans recalcul.

---

## 15 octobre 2026 — Android D10-B, correctif de sauvegarde fusionné après 3 CI vertes

**Goal** : éviter que les données médicales locales soient sauvegardées automatiquement sur Android/transportées à un nouvel appareil sans protocole patient autorisé. **Le verrou facultatif B lui-même reste NON IMPLÉMENTÉ.**

**Preuve prémerge SHA `09e48db9961936775fe16987c3db35d2ecda7dfa`** :
- [PR #1046](https://github.com/hraaaaf/IAMINA-MVP/pull/1046) : 6 fichiers uniquement (AndroidManifest `allowBackup=false`, 2 XML Android 11/12+ excluant cloud et D2D, 3 tests XML et GitHub Actions compile/debug merged manifest, doc sécurité), sans autre code patient.
- [D10 Android #38709641432](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38709641432) **SUCCESS** avec `Source XML and negative-path policy tests`, `Compile Android debug APK` et `Validate merged APK manifest policy` toutes SUCCESS.
- [CI générale #38709641394](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38709641394) **SUCCESS** ; [packaging mobile #38709641442](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38709641442) **SUCCESS**.
- **Merge** : [#1046](https://github.com/hraaaaf/IAMINA-MVP/pull/1046) `MERGED` au commit `2e16be596c07b61de877250be1c836beca861579`. `main`, manifeste et [doc de protection Android](https://github.com/hraaaaf/IAMINA-MVP/blob/main/docs/security/2026-10-15-d10-b-android-backup-hardening.md) relus sur ce SHA.

**Postmerge sur `2e16be59`** : [D10 Android #38710694402](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38710694402) et [CI #38710694368](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38710694368) étaient `IN_PROGRESS` au premier contrôle ; enregistrer leur conclusion avant de déclarer la CI postmerge close.

**Limites techniques** : exclusion déclarative et manifeste Android debug compilé ne prouvent **pas** une sauvegarde/restore sur véritable appareil/OEM. Désactiver la sauvegarde réduit les possibilités de restauration sur nouveau téléphone. La [documentation Android Auto Backup](https://developer.android.com/identity/data/autobackup) distingue cloud, D2D et transfert Android 16 QPR2 vers iOS : ce troisième mode n'a **pas** été qualifié faute de `Apple Team ID` vérifié et de test matériel ; [issue #1048](https://github.com/hraaaaf/IAMINA-MVP/issues/1048) **OPEN**. Ne pas prétendre tous les modes de transfert certifiés.

**D10-B statut** : préférence utilisateur B actée, implémentation réelle NON LIVRÉE ; stockage iOS/Web, identité propriétaire forte et droit de synchroniser séparé non attestés. [Issue D10 #968](https://github.com/hraaaaf/IAMINA-MVP/issues/968) et [gate #1013](https://github.com/hraaaaf/IAMINA-MVP/issues/1013) OPEN. Aucune donnée patient réelle ni aucun déploiement Vercel. **Next exact** : vérifier CI postmerge puis qualifier les protections iOS/Web, développer un opt-out cryptographiquement sûr sur plateformes approuvables, tester avant activation. P5 historique : 50 %.

---

## 15 octobre 2026 — Réexécution D10-B sur HEAD actuel, code + standards primaires

**Goal** : appliquer concrètement le prompt d'expert sécurité/confidentialité sur le code final plutôt que reproduire un texte générique.

**Preuve source :** `main@58f0dc940449e0cdace099df5350be79e34d53b4`, 15 fichiers vérifiés directement en GitHub. [Rapport exact-head avec matrices et preuves de lignes](https://github.com/hraaaaf/IAMINA-MVP/blob/main/docs/security/2026-10-15-d10-b-exact-head-security-privacy-execution.md), rapproché du [prompt pour évaluateurs externes](https://github.com/hraaaaf/IAMINA-MVP/blob/main/docs/security/2026-10-15-d10-b-independent-audit-prompt.md). Sources primaires OWASP MASVS/MASTG, Apple, Android, MDN et CNDP vérifiées.

**Verdict technique de l'IA : `CHANGES_REQUIRED / NO-GO` sur Web, Android, iOS pour activer maintenant l'opt-out avec données médicales réelles.** Source `AppDatabase.forPatientVault` sans preuve d'une clé SQLCipher, Android manifest sans politique explicite backup, iOS protection DB non démontrée, stub d'authentification natif `unsupported_platform`, préférence B non implémentée, autorisations réseau liées au verrou, sauvegardes JSON à qualifier. **Aucune fuite effective ni non-conformité juridique avérée n'est prétendue.** Éléments favorables revalidés : `AppLockService` fail-closed et `ApiClient.canSyncClinicalData=false` par défaut.

**Limites :** cette nouvelle passe a été effectuée par ChatGPT et non par deux évaluateurs humains externes. Pas de test instrumenté de la variante B inexistante, pas de build natif ou pentest, pas de sign-off. **Human gate de sécurité/privacy #1013 reste OPEN**. La décision produit B est maintenue, l'option n'est ni implémentée ni mise en production.

**Next exact :** transmettre prompt+rapport à deux spécialistes qualifiés différents, valider protections iOS/Android/Web par attestations signées et tests, puis implémenter un opt-out par owner/appareil sur plateformes autorisées avec non-régression CI et BEFORE→mockup→AFTER UI. D31 physique distincte ; P5 historique 50 %.

---

## 15 octobre 2026 — D10-B : prompt d'audit externe + pré-audit contradictoire réalisés

**Goal** : permettre à deux évaluateurs indépendants (sécurité et confidentialité) de juger l'app-lock facultatif B, sur preuves exactes iOS/Android/Web, sans confondre arbitrage produit et certification.

**Prompts et résultats** :
- [Prompt pour évaluateurs humains indépendants](https://github.com/hraaaaf/IAMINA-MVP/blob/main/docs/security/2026-10-15-d10-b-independent-audit-prompt.md) : protocole reproductible, menaces, standards OWASP/Apple/Android/MDN/CNDP, preuves attendues, signatures individuelles et critères PASS/CHANGES_REQUIRED.
- [Pré-audit contradictoire exécuté](https://github.com/hraaaaf/IAMINA-MVP/blob/main/docs/security/2026-10-15-d10-b-preaudit-security-privacy.md) : lecture source figée sur `main@de2afee9f5b8fe11fa806c361f246eae6854bbd0`. Deux passes thématiques par **une même IA**, donc **pas deux avis indépendants**. Verdict technique `CHANGES_REQUIRED / NO-GO` pour l'activation B en l'état sur iOS, Android et Web. Aucune fuite réelle ni infraction réglementaire déduite sans preuve.
- **Preuves de Git/CI** : [PR documentaire #1017](https://github.com/hraaaaf/IAMINA-MVP/pull/1017) MERGED au commit `5a9e58be4eb38bca60ce1dc642e772310aa4b2a8` ; `main` lu au même SHA, les deux fichiers et leur verdict vérifiés, [CI prémerge #38693983087](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38693983087) SUCCESS ; [CI postmerge #38694135904](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38694135904) SUCCESS.
- **Constats critiques** : chiffrement du coffre médical non prouvé ; règles Android backup absentes du manifeste source ; niveau de protection des fichiers iOS non qualifié ; authentificateur natif non implémenté (`unsupported_platform`) ; identité locale non équivalente à une preuve forte ; accès local et egress clinique couplés à `isUnlocked` ; sauvegarde JSON à qualifier. **Ces constats sont des conditions de release et des incertitudes**, pas une fuite confirmée.
- **Human gate réel** : [issue sécurité/privacy #1013](https://github.com/hraaaaf/IAMINA-MVP/issues/1013) OPEN et **aucune signature externe recueillie**. B = décision produit retenue, **fonctionnalité non implémentée**, aucun bypass, ni déploiement avec données réelles.
- **Next exact** : désigner deux spécialistes distincts, leur transmettre le prompt et fournir accès lecture / artifacts expurgés ; recueillir deux avis signés par plateforme avec risques résiduels et correctifs. Ensuite seulement branches d'implémentation B, tests T01–T10, BEFORE→mockup→AFTER, CI, merge, postmerge. D31 physique reste séparée [#1006](https://github.com/hraaaaf/IAMINA-MVP/issues/1006). P5 historique : 50 %.

---

## 15 octobre 2026 — POST-MERGE FINAL : tests D10-B VERTS, GATE HUMAN OPEN

- **État vérifié GitHub, main HEAD :** `a38285ab72d2cebbcc0f9738096adfc459547932`, [PR #1010](https://github.com/hraaaaf/IAMINA-MVP/pull/1010) / [#1012](https://github.com/hraaaaf/IAMINA-MVP/pull/1012) / [#1014](https://github.com/hraaaaf/IAMINA-MVP/pull/1014) **MERGED**.
- **Avant merge des tests D10** HEAD `a7811eb4` : [TD-014 #38657348652](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38657348652) SUCCESS, [CI #38657348657](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38657348657) SUCCESS, [P5-5 #38657348727](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38657348727) SUCCESS.
- **Après merge D10** HEAD `b9588bf9` : [P5-5 #38657961163](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38657961163) SUCCESS ; CI #38657961166 **CANCELLED** (ne jamais la compter verte), remplacée pour le code identique par CI finale [#38658178252](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38658178252) **SUCCESS sur main exact `a38285ab`** après merge du dossier documentaire.
- **TD-008 réparée** : [run Android postmerge #38657927043](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38657927043) **COMPLETED SUCCESS** sur `7cdda5a3`, en plus de CI #38657927045 SUCCESS. Plus aucun run en cours dans ce sous-lot identifié.
- **D10-B = choix utilisateur acté, NON livrée :** les PR code précédentes ne contiennent que des tests de non-contournement, pas de désactivation du verrou dans l'app. L'expert sécurité et le responsable privacy n'ont pas donné d'avis indépendants : [gate #1013](https://github.com/hraaaaf/IAMINA-MVP/issues/1013) OPEN. Absence de preuve suffisante du chiffrement/protection du stockage médical local (notamment web IndexedDB). **Human gate véritable avant tout opt-out réel ou déploiement B.**
- **Next exact :** obtenir évaluations indépendantes sécurité/privacy par plateforme et preuves du stockage/OS puis reprendre l'implémentation B sécurisée ; garder tests physiques D7/D9 dans D31 [#1006](https://github.com/hraaaaf/IAMINA-MVP/issues/1006). P5 historique = 50 %, aucun nouveau pourcentage inventé.

---

## 15 octobre 2026 — D10-B baseline défensive fusionnée ; gate humaine maintenue

- **Code source main certifié fusionné, pas produit B activé :** [PR #1012](https://github.com/hraaaaf/IAMINA-MVP/pull/1012) **MERGED** commit `b9588bf9fb37fc1d6dc922f91b4039a380f839a9`, HEAD `main` vérifié au même SHA immédiatement après fusion. Un seul fichier de **tests** `frontend/test/services/app_lock_service_test.dart` modifié ; aucun accès clinique, consentement, route, stockage, UI ou lock service runtime modifié.
- **Avant merge, exact HEAD `a7811eb4eb4be167d424b49331892374a9f3b978` : 3/3 SUCCESS** : [TD-014 #38657348652](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38657348652), [CI #38657348657](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38657348657), [P5-5 #38657348727](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38657348727). Trois assertions ajoutées contre faux marqueur de désactivation app-lock : coffre protégé sans credential fail-closed, récupération local-only non vérifiée refusée, cold boot avec credential valide reste verrouillé.
- **Postmerge du SHA `b9588bf9` :** [CI #38657961166](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38657961166) et [P5-5 #38657961163](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38657961163) lancés ; **aucun SUCCESS affirmé sans lecture de leurs conclusions**.
- **Human gate :** [issue indépendante #1013](https://github.com/hraaaaf/IAMINA-MVP/issues/1013) **OPEN**. Absence de preuve suffisante de protection au repos SQLite/IndexedDB et d'avis indépendants sécurité/privacy sur opt-out iOS/Android/Web. Ne pas désactiver le verrou ni déclarer D10 livrée. Option B choisie reste la cible ; implémentation runtime **bloquée** avant avis.
- **Parallèle TD-008 :** [PR #1010](https://github.com/hraaaaf/IAMINA-MVP/pull/1010) MERGED sur `7cdda5a3284306d0dd15ae54f05c0420583413a9`. [Run Android prémerge #38656735672](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38656735672) SUCCESS après réparation KVM, et CI #38656735687 SUCCESS. Postmerge [TD-008 #38657927043](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38657927043) initialement IN_PROGRESS ; CI #38657927045 SUCCESS.
- **Next exact :** vérifier conclusions postmerge des 2 PR ; pour D10, obtenir sign-off indépendant de #1013 et préciser les plateformes autorisant B, ensuite seulement programmer un opt-out propriétaire/terminal sans faux déverrouillage et avec tests. **P5 historique : 50 %.**

---

# IAMINA V1 — D10/B : app-lock facultatif — décision, sûreté, reprise canonique

Date : 14 octobre 2026. Repo : `hraaaaf/IAMINA-MVP`. Base inspectée : `main@e1ae8eb3687bd3b30f49999c437c8fb2bbeedeeb`.

## Décision utilisateur — B, confirmée

L'utilisateur choisit **B : le verrouillage supplémentaire d'IAmina (app-lock) doit être facultatif, y compris si des données médicales locales existent**. Ce n'est **pas** une autorisation de rendre des données de santé publiques, ni une validation indépendante des risques. La protection fournie par le verrouillage du système d'exploitation, le contrôle de session/propriétaire, la confidentialité des fichiers et des sauvegardes, et la sécurité des échanges restent obligatoires. La présence d'un verrou OS fiable doit être **démontrée**, pas supposée.

**Goal produit :** une personne dûment identifiée peut choisir explicitement sur *son appareil* de ne pas voir de demande supplémentaire de déverrouillage IAmina, puis réactiver cet app-lock ; ce choix ne débloque jamais le coffre d'un autre compte, ne récupère pas implicitement un coffre perdu et n'autorise pas un transfert clinique ou consentement IA.

**État : décision métier B VALIDÉE, implémentation NON COMMENCÉE ; revue indépendante sécurité/privacy et preuves techniques REQUISES avant activation**. Aucun patient réel autorisé à tester B.

## Preuve code : baseline BEFORE

Sur le SHA de référence :

1. `frontend/lib/routes/app_router.dart` : `shouldApplyAppLockGate` conduit toute session réelle configurée/non configurée vers `/app-lock/unlock` ou `/app-lock/setup`. L'app-lock est aujourd'hui obligatoire.
2. `frontend/lib/services/app_lock_service.dart` : `initialize` refuse implicitement la disparition d'une credential avec un coffre protégé (état `recoveryRequired`) ; `recoverWithVerifiedRemoteAccount` exige un compte distant et des identifiants fraîchement vérifiés ; `configure` et `unlock` ne passent à `_unlocked=true` qu'après une réponse d'authentification forte.
3. `frontend/lib/main.dart`, `frontend/lib/services/patient_vault_app_host.dart`, `frontend/lib/services/api_client.dart` : le verrou participe aussi à la protection des accès et à la capacité d'émettre des données via les routes cliniques. **Ne jamais forcer `isUnlocked=true` pour simuler B**.
4. `frontend/lib/data/drift/database.dart` : les coffres utilisent `driftDatabase(name: scope.databaseName, web: DriftWebOptions(...))` avec SQLite/IndexedDB sur web. **Aucun chiffrement applicatif du coffre n'a été démontré par ce constructeur** ; cela ne prouve pas l'absence de protections système sur toutes les plateformes, mais interdit de les présumer.
5. `frontend/lib/services/app_lock_authenticator_web.dart` : la capacité dépend de la disponibilité WebAuthn côté navigateur ; aucun contrôle universel du verrou OS sur navigateur web n'est attesté.
6. `frontend/test/services/app_lock_service_test.dart` teste actuellement le démarrage verrouillé, l'absence de credential, le fallback fail-closed et le déverrouillage vérifié. Ce sont des tests réels du verrou actuel, pas de B.

## Modèle de menace et points bloquants

| Risque | Événement redouté | Contrôle à prouver pour B |
| --- | --- | --- |
| Téléphone prêté ou volé mais déverrouillé | Un tiers ouvre le journal médical sans barrière IAmina | Contrôle OS sécurisé et politique d'expiration/session, informations sensibles masquées en multitâche |
| Navigateur/profil partagés, extensions, caches, IndexedDB | Lecture du coffre local par un autre utilisateur du poste | Protection démontrée des données au repos et isolation du profil navigateur ; sinon B indisponible sur web |
| A se déconnecte, B entre | Héritage du choix de A, de ses consentements ou de son SQLite | Option B attachée au *couple compte vérifié + appareil + coffre* et invalidée au changement d'identité/epoch |
| Credential corrompue ou perdue | « Désactiver le verrou » devient une récupération non autorisée | `recoveryRequired` prioritaire ; vérification forte du bon compte avant toute migration ou désactivation |
| Téléphone neuf ou restauration depuis backup | Données supposées présentes, consentement ou sécurité empruntés | Ne jamais restaurer un profil non vérifié ; D9 nouvel appareil non livré, D31 test physique séparé |
| Hors ligne / absence de passcode OS | Érosion de l'identité et impossibilité de sécuriser les données | Définir authentification locale démontrable + refus B si appareil, clé ou stockage non sûrs |
| Export, partage, sync clinique, suppression | Opération sensible réalisée sans revérification de l'identité | Step-up spécifique, autorité serveur et consentement indépendant ; aucune nouvelle permission réseau |

Références de contrôle : [OWASP MASVS-STORAGE-1](https://mas.owasp.org/MASVS/controls/MASVS-STORAGE-1/), [OWASP MASVS-AUTH-2](https://mas.owasp.org/MASVS/controls/MASVS-AUTH-2/), [OWASP MASWE-0017 / verrou OS](https://mas.owasp.org/MASWE/MASVS-CRYPTO/MASWE-0017/), [CNDP Maroc / conditions et données de santé](https://www.cndp.ma/conditions/). Les obligations applicables doivent être déterminées par le responsable conformité, pas inférées comme déjà satisfaites.

## Contrat et maquette cible — POUR REVUE, pas encore implémentés

**BEFORE :** IAmina affiche un écran d'enrôlement obligatoire après la connexion ; aucune commande de désactivation du verrou n'est disponible pour un vrai utilisateur.

**Goal UI :** choix compréhensible avec sécurité conservée et consentement à ce risque explicite.

**Mockup textuel cible, uniquement après capacité et sécurité démontrées** :

- Titre : « Protéger mon espace santé ».
- Option initiale : « Demander le déverrouillage IAmina (recommandé) ».
- Alternative : « Ne pas demander de verrouillage IAmina supplémentaire sur cet appareil ».
- Information claire : « Toute personne utilisant votre téléphone déjà déverrouillé pourrait voir vos données de santé. Le verrouillage de votre téléphone doit rester actif. »
- Validation indépendante de la case de prise de connaissance, puis **confirmation avec l'identité du propriétaire** ; pas de case précochée, pas d'activation silencieuse, pas de transfert à un autre compte ou appareil.
- Si garanties OS/stockage/session non vérifiables : option B indisponible avec explication, **jamais de bouton sans effet**.
- Paramètres : possibilité de réactiver le verrou avec vérification appropriée ; déconnexion efface la préférence volatile, pas les données d'un autre coffre.

**AFTER attendu** : captures du même écran/état aux viewports 390×844, 768×1024, 1280×900 (FR, EN, AR/RTL) ; test tactile, lecteur d'écran et mode sombre. **Aucun AFTER ni score visuel attribués à ce stade.**

## Contrat d'architecture à implémenter après revue

1. Isoler la *politique d'accès* de `AppLockService.isUnlocked` : distinguer `appLockRequired`, `ownerSessionVerified`, `localVaultAccessAuthorized` et `clinicalTransportAuthorized`. Ne jamais marquer une credential vérifiée fictivement.
2. Préférence versionnée **par couple propriétaire + coffre physique + appareil**, stockée de façon résistante à la falsification. Pas de « bool global skip-lock » ; ancienne credential manquante n'autorise pas B. Migration et retrait réversibles sans perte de données.
3. Certifier chiffrement au repos / classe de protection OS par plateforme, sauvegardes et suppression ; sur navigateur si protection non prouvable, B doit rester indisponible.
4. Conserver le refus de synchronisation clinique local-only, l'autorité du backend, `AuthEpoch`, les gates de consentement IA et l'isolation patient. Aucune donnée médicale réelle pendant la validation.
5. Toute opération sensible (export, partage, changement d'identité, récupération, réactivation de sync) demande un contrôle d'identité propre, même si l'écran de lecture a un app-lock facultatif.

## Matrice d'acceptation D10

- Nouvelle installation sans donnée / propriétaire vérifié / passcode OS conforme : option affichée seulement après vérification de la plateforme et du stockage.
- Coffre existant avec credential valide : désactivation uniquement après vérification du propriétaire, choix explicite, traçabilité et migration non destructive.
- Credential absente, abîmée, compteur rejeu, marqueur manquant : `recoveryRequired` ; aucune désactivation silencieuse, même hors ligne.
- A→déconnexion→B→A : option B du compte A ne déverrouille aucun coffre de B ; aucune fuite de contenu, consentement, historique ou token.
- OS sans verrou, contexte web incertain, IndexedDB non chiffrée/unknown, OS biométrique non supporté : **pas d'opt-out activable**, message utile ; contrôle alternatif seulement si une garantie équivalente est démontrée.
- Arrière-plan, retour après 60 s, navigateur fermé/réouvert : politique par session testée ; aucune fuite via snapshots, notifications ou cache.
- Export / upload / consentement IA / restauration : pas de permission supplémentaire dérivée de B ; opérations fortes exigent leur autorité indépendante.
- Tests Flutter, intégration mobile, migrations SQLite et sauvegarde, A→B→A, captures BEFORE/AFTER FR/EN/AR, audit réseau. Les deux téléphones physiques P01–P09 appartiennent à D31 [#1006](https://github.com/hraaaaf/IAMINA-MVP/issues/1006), non exécutée.

## Gate de sécurité et séquence restante

**Human gate indispensable :** expert sécurité indépendant + responsable confidentialité, sur cette analyse et une preuve vérifiable de protections locales (web/iOS/Android). Le choix produit B par le propriétaire est acté ; il **n'est pas** une signature de sécurité. Aucune activation runtime B, aucune fusion de bypass, aucun déploiement Vercel d'une variante B avant revue.

1. Faire vérifier cette menace et les compensations par responsables sécurité/privacy, préciser plateformes où B est admissible.
2. Implémenter sur branche isolée une politique versionnée et un opt-out explicite **uniquement pour les plateformes approuvées**, tests de fail-closed d'abord.
3. Maquette validée → UI → AFTER mêmes viewports → tests réels → score visuel.
4. CI exacte, revue indépendante, merge et post-merge, documentation Notion/roadmap ; garder certification physique D31 séparée.
5. Si garanties équivalentes impossibles, conserver la sécurité par défaut et bloquer B sur la plateforme concernée ; ne pas présenter D10 comme « livrée ».

**État vérifié au 14/10/2026 :** D10/B = décision métier actée, architecture évaluée, **aucun code d'opt-out activé ni vérifié**, revue humaine externe en attente. P5 historique = 50 %, non recalculé.

**FICHIER CANONIQUE :** `docs/handovers/2026-10-14-iamina-d10-option-b.md`.
