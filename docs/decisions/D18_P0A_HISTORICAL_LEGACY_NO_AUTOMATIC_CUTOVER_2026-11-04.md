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
