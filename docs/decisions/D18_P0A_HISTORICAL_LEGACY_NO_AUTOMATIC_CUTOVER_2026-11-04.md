# D18 P0-A — ancienne version offline : refus de bascule automatique

**État : proposition technique, non autorisation clinique — 2026-11-04.**  
**Décision mère : D18, chiffrement des coffres patients IAMINA Web.**  
**Goal exact :** ne perdre ni ignorer silencieusement aucune écriture créée par un client antérieur/offline lors d'une transition plaintext → sqlite3mc.  
**Succès :** aucun pointeur clinique actif ni abandon de source historique sans preuve indépendante et durable de conservation et réconciliation.  
**Preuve disponible :** PR Draft [#1265](https://github.com/hraaaaf/IAMINA-MVP/pull/1265), tests négatifs Chromium/WebKit (16/16), garde CI sur le graphe d'imports de l'application.

## Constat technique vérifié

Une version historique n'invoque pas les nouveaux Web Locks ni le nouveau protocole. Une transaction IndexedDB `readwrite` peut donc être commitée **après** une copie candidate et **après** une nouvelle lecture de la source, alors que le migrateur détient deux verrous Web exclusifs. Les tests reproduisent aussi une reconnexion de l'onglet après coupure réseau. Le fait qu'aucun verrou ne soit sollicité, ou qu'aucun onglet ne soit visible, n'atteste **pas** l'absence d'anciens écrivains présents ou futurs.

* Sources externes (norme et documentation) : [W3C Web Locks API](https://www.w3.org/TR/web-locks/), coordination entre scripts qui demandent ces verrous ; [MDN IndexedDB transactions](https://developer.mozilla.org/en-US/docs/Web/API/IndexedDB_API/Using_IndexedDB), modèle distinct de transactions et mode `readwrite`.
* Preuve interne : `tools/d18_stale_tab_write_bypass_probe.js` ; CI Chromium [#41815331493](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41815331493) et WebKit [#41815331666](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41815331666), **SUCCESS** au HEAD `17611ea51...`.

## Choix recommandé (pas encore un GO)

**D18-P0A-SAFE-HOLD :** interdire **par défaut toute promotion automatique** d'un coffre historique plaintext, y compris si : (i) un Web Lock exclusif est libre ; (ii) un snapshot et son digest sont identiques à l'instant T ; (iii) une archive et un coffre sqlite3mc paraissent intègres ; (iv) le patient a confirmé une mise à jour ; (v) un service worker a installé un nouveau bundle ; (vi) une absence d'écriture a été observée pendant un délai arbitraire.

- Conserver intacte la source physique historique et son accès de récupération pendant le développement ; aucune suppression, réinitialisation, substitution silencieuse ni garantie implicite de reprise.
- Ne pas utiliser un marqueur `prepared` ou `ciphertextActive` d'un essai synthétique pour déterminer la base clinique autoritaire.
- Continuer l'enregistrement clinique dans le parcours existant tant qu'une transition a été explicitement refusée. **Ceci prolonge la présence de plaintext local : risque résiduel de confidentialité, à traiter séparément.**
- Réserver l'enrôlement « chiffrement dès la création » aux coffres **réellement neufs** après preuve de non-existence préalable, auth/scope, stockage et récupération ; aucun chemin d'activation produit n'est autorisé aujourd'hui.
- Pour les coffres existants, étudier une **migration assistée avec réconciliation reproductible et lisible** (export complet, restauration indépendante, comparaison logique exhaustive, validation des divergences, historique intact). Une comparaison ponctuelle n'exclut pas une écriture future : l'absence de silent data loss doit être démontrée pour **chaque reprise** ou l'application doit maintenir un refus de changement d'autorité. L'ancienne base ne doit pas être supprimée avant une stratégie de rétention approuvée.

### Options écartées comme preuve suffisante

| Option seule | Pourquoi insuffisante |
| --- | --- |
| Web Locks + BroadcastChannel | Ancien bundle n'écoute ni n'acquiert la barrière |
| Service Worker update / rechargement | Un onglet préchargé et offline peut continuer à exécuter l'ancien code |
| Relecture du digest juste avant CAS | Une ancienne transaction peut s'engager **après** le dernier contrôle |
| Nouvelle origine Web | Protège l'origine cible mais n'empêche pas de nouvelles écritures dans l'ancienne |
| Un clic « j'ai fermé tous les onglets » | Déclaration utilisateur non opposable au cache offline et futurs onglets |

## Invariants d'exécution et gates

1. **Ancienne source détectée ou existence incertaine → NO-CUTOVER**. Aucun `AppDatabase.forPatientVault` clinique n'est remplacé par le worker candidate sur cette base.
2. La promotion synthétique reste inaccessible depuis le graphe d'imports de `main.dart`, `database.dart`, `patient_vault_session_controller.dart` et `patient_vault_app_host.dart`. `tools/d18_source_sqlite_entrypoint_inventory.py` impose le gate et échoue si des modules expérimentaux sont atteignables, même par import conditionnel/transitif.
3. Si un test positif montre une écriture tardive, **le résultat correct est le maintien du refus** ; ne jamais déclarer « protection réussie » à partir de cette seule sonde.
4. Aucun rollback ne supprime la source ancienne, aucune donnée patient n'entre dans les fixtures, aucun secret ne se trouve dans les rapports CI.
5. **Activation clinique : 0 autorisation.** Revue indépendante sécurité et intégrité médicale, tests reproductibles de crash/reprise/réconciliation dans Chromium et WebKit, preuve complète du parcours patient, décision humaine explicite requise.
6. Aucune fusion des PR D18, activation de crypto clinique ou déploiement Vercel par ce chantier.

## Matrice de tests / preuve restante

| Risque | Preuve disponible | À démontrer |
| --- | --- | --- |
| Écriture après copie et après recheck | Chromium/WebKit 16/16, donnée synthétique | Solution empêchant *ou* conciliant toutes les écritures futures |
| Offline/reopen sous verrou | Chromium/WebKit CI | Reprise après crash processus/éviction et plusieurs profils |
| Connexion accidentelle du cutover au runtime | Inventaire statique transitive CI (ajouté, à vérifier sur HEAD final) | Revue indépendante + test d'intégration réelle |
| Divergence de données/table/trigger/FK/BLOB | Pas de preuve complète de réconciliation | Modèle déterministe par entité, conflits et suppressions |
| Rupture courant/quota/auth epoch | Tests pré-cutover partiels P0-C/D | Crash matrix et décision autoritaire durable, vraie base Web |

**Verdict : P0-A NON RÉSOLU en clinique.** Le présent document fixe un refus sûr et un plan de validation ; ce n'est ni un algorithme de réconciliation, ni une preuve de transition sûre.

**Reprise :** `docs/handovers/2026-10-31-iamina-d18-web-ux-implementation.md` ; issue [#1261](https://github.com/hraaaaf/IAMINA-MVP/issues/1261), PR [#1265](https://github.com/hraaaaf/IAMINA-MVP/pull/1265).

## Addendum — 2026-11-04 : faisabilité de fencing par upgrade IndexedDB (hors Drift)

La [spécification IndexedDB 3.0](https://www.w3.org/TR/IndexedDB/) définit une transaction `versionchange` **exclusive**, qui attend la fermeture des connexions déjà ouvertes avant de renommer un object store ; [MDN explique les événements `blocked` et `VersionError`](https://developer.mozilla.org/en-US/docs/Web/API/IndexedDB_API/Using_IndexedDB). C'est une barrière physique potentiellement plus forte que les Web Locks, uniquement pour **la base et le schéma explicitement ciblés**.

**Expérience TEST-ONLY :** `tools/d18_stale_tab_write_bypass_probe.js` contient maintenant huit assertions supplémentaires sur une **base IndexedDB synthétique distincte** : upgrade bloqué tant qu'un ancien handle reste ouvert, écriture tardive conservée avant la fermeture, renommage transactionnel du store, refus des anciens clients avec version pinée ou implicite y compris hors ligne, et archive source conservée dans un nouvel onglet. [WebKit #41823567078](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41823567078) a loggé **24/24 assertions PASS** (16 négatives Web Locks + 8 positives versionchange), sur le HEAD de code `9f7af5eeccfc94f84c185396b16bb60097d31619`. [Chromium #41823567049](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41823567049) était toujours en cours au premier contrôle. Ce test ne change ni ne touche aucune vraie base clinique.

**Limite déterminante :** le VFS Drift réel n'est PAS notre fixture `rows`. IAMINA verrouille Drift `2.31.0`, `drift_flutter 0.2.8`, `sqlite3 2.9.4` (`frontend/pubspec.lock`). Le stockage navigateur peut être basé sur IndexedDB ou OPFS ; une transformation sauvage d'object stores internes est **interdite** car elle pourrait empêcher la récupération physique et affecter d'autres coffres. L'upgrade bloqué doit laisser toute source intacte et NO-GO, jamais tuer/supprimer les anciennes connexions. Avant toute proposition de production, démontrer sur les versions verrouillées et sur des coffres jetables : inventaire exact des backends/identifiants, absence d'impact sur autres coffres, transaction/rollback/crash, export des bytes SQLite après fencing, intégrité globale v12+FK+BLOB et refus d'écritures des anciennes versions. Si un backend n'offre aucune barrière sûre, **SAFE-HOLD reste obligatoire**.

Cette hypothèse ne transforme pas le statut : **P0-A clinique NON CERTIFIÉ ; aucune autorisation de bascule automatique**.

## Option de réduction de périmètre — invité éphémère et compte requis (04/11/2026)

**Proposition de décision produit :** réduire le parcours Web **non enrôlé** à une découverte sans saisie de données médicales personnelles, puis inviter à se connecter après une durée indicative de **5 minutes** ou immédiatement à l'entrée d'une fonction clinique. Ce chrono est un **signal UX**, pas une autorisation ni une frontière de sécurité, et ne doit ni supprimer des données ni interrompre un acte de soin en cours.

**Goal :** minimiser les **nouveaux** coffres plaintext/anonymous créés sur le Web tout en préservant intégralement les coffres historiques et la confiance des utilisateurs existants.

**État réel observé dans le code (PR #1265) :** `main.dart` crée une base persistante `AppDatabase.forPatientVault(PatientVaultScope.auditOnly())` pour la branche invitée ; `PatientVaultAppHost` lui injecte un routeur d'application ; `AuthService.isAuthenticated` peut valoir vrai pour une session `_localSessionEnrolled`, `_auditSession` ou une connexion Firebase anonyme ; `resolvePatientVaultScope()` peut attribuer un scope `deviceLocal` à une session locale. Le routeur `hostedRemoteLoginRequired()` retourne `false` et indique que le compte distant n'est pas obligatoire. **Il faut donc définir explicitement une identité clinique authentifiée**, sans s'appuyer sur `isAuthenticated` ou un simple minuteur.

**Frontière produit envisagée pour les nouvelles installations seulement :**
1. **Invité :** explications, simulateurs utilisant des cas fictifs, pages publiques ; état en mémoire volatile uniquement, **aucune donnée glycémique individuelle, prescription, profil ni historique** persistés dans IndexedDB, SQLite, OPFS, localStorage ou backend. Ne pas ouvrir une DB clinique `auditOnly` persistante pour le vrai mode visiteur. Maintenir séparés les outils d'audit synthétiques loopback.
2. **Première action clinique :** exiger un **compte stable vérifié et lié à un seul scope de patient** et le déverrouillage du coffre selon la politique d'authentification et de clé D18. Un compte n'implique pas à lui seul chiffrement au repos : la création d'un coffre chiffré doit disposer d'une certification indépendante.
3. **Timer :** proposer après cinq minutes un CTA de connexion non destructif, avec blocage immédiat des fonctions cliniques déjà protégées indépendamment du temps écoulé ; ne pas utiliser le décompte côté navigateur comme contrôle de sécurité.
4. **Utilisateurs existants :** ne pas transformer automatiquement leur coffre local, ne pas redéfinir `auditOnly` ou `deviceLocal` comme appartenant au prochain compte, et ne pas les couper brutalement de leurs informations de santé. Prévoir une voie d'accès/récupération protégée et la migration/reconciliation séparée sous SAFE-HOLD.

**Ce qui reste non résolu :** ce modèle **n'empêche aucun ancien onglet Web offline déjà mis en cache de continuer à écrire dans une base historique**. La preuve Chromium du HEAD `d0389b7658f309d962266cdb687cb9f78039ac79`, [Worker #41839588272](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41839588272) et [WebKit #41839588203](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41839588203) SUCCESS, a confirmé que le simple `versionchange` v1→v2 sur **vraie VFS Drift de coffre jetable** permet toujours un `indexedDB.open(name)` sans version en `readwrite` et empêche ensuite la factory Drift de rouvrir ce coffre malgré `blocks:18` et `files:1` préservés. **Le PASS est un résultat négatif de sécurité, pas une migration réussie.**

**Critères de réussite de l'éventuelle évolution produit :** scénario visiteur sans création de vault/DB ni écriture de données cliniques ; route de suivi/traitement refusée sans identité clinique valide indépendamment du timer ; seconde session, rafraîchissement, offline, retour arrière, deux onglets et inscription ; identité A→logout→B sans exposition croisée ; séparation du stockage d'audit ; anciennes données jamais effacées ni appropriées ; accessibilité mobile à 200 %, tests de copie et mockup avant/après aux mêmes viewports. Contrôle serveur impératif pour tout appel API clinique (OWASP).

**Sources :** [MDN Service Worker et PWA offline](https://developer.mozilla.org/en-US/docs/Web/Progressive_web_apps/Guides/Offline_and_background_operation), [OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html), [Firebase anonymous auth](https://firebase.google.com/docs/auth/flutter/anonymous-auth), [W3C IndexedDB](https://www.w3.org/TR/IndexedDB/).

**Statut :** cadrage **PROPOSÉ**, sans implémentation, pas un P0-A GO. Aucun changement de comportement clinique, aucune bascule des anciennes bases, aucun merge ni déploiement Vercel. Avant toute activation de la restriction : audit d'impact sur les utilisateurs locaux existants et validation UX/cabinets pour les situations hors ligne.
