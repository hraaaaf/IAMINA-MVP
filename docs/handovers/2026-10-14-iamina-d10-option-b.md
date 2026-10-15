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
