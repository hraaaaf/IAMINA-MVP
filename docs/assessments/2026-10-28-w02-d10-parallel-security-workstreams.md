# IAMINA W02/D10 — lots parallélisables et garde clinique (28/10/2026)

## Résultat visé et preuves

**Décision principale D10-B** : app-lock secondaire facultatif sur Web *seulement* si les données patient sont chiffrées au repos, liées au propriétaire vérifié et récupérables sans régression. **Ce document et le coordinateur synthétique ne rendent pas D10-B opérationnelle.**

| Axe indépendant | Implémentation / preuve locale au lot | Gate restante |
|---|---|---|
| A — Protocole JS / mémoire Flutter | `frontend/web/iamina_w02_synthetic_session.mjs` ; contrat `restore→memoryFactory.open→exportSnapshot→revision CAS externe→AES-GCM/IndexedDB CAS→receipt` ; 10 tests synthétiques Node | Implémenter le vrai pont JS↔Dart/Flutter, auth réelle et tests Chrome multi-comptes ; ne pas activer `AppDatabase` |
| B — Anti-rollback & recovery | Interface injectée `revisionAuthority.getFloor / compareAndAdvance` ; rejet des révisions non fiables et des snapshots manquants ; absence de compensation du floor après crash | Choisir et auditer une autorité monotone durable indépendante du stockage navigateur ; politique offline et récupération après quota/panne |
| C — Quota/crash et séparation des comptes | Tests de refus / poison session, révocation de session, conflit à deux rédacteurs, A/B, disparition locale, ciphertext-only | Refaire les mêmes attaques dans Chrome réel et à travers BFF/auth sans patient réel ; signoff sécurité indépendant |
| D — Migration legacy | **Aucune migration automatique ni suppression** ; ancien stockage local patient potentiellement non chiffré : garder le garde fail-closed | Spécification versionnée, inventaire physique, import consentant, sauvegarde chiffrée, rollback sans perte, tests data-fidelity et effacement prouvé |
| E — UI app-lock facultatif | **Aucun changement visuel / route runtime** pour ne pas permettre de contourner la protection | AFTER preuve backend/vault, BEFORE → mockup → implémentation → AFTER mêmes viewports + FUE FR/EN/AR |

## Modèle de panne — choix « sécurité d'abord »

* Le floor **doit** être stocké hors de la même base IndexedDB contrôlée par le navigateur et ancré à la bonne identité vérifiée ; un simple `localStorage` ou `envelope.revision` ne prouve rien.
* Le contrat synthétique avance le floor *avant* de confirmer l'écriture chiffrée. Si quota, fermeture, panne réseau, crash ou perte de disque interrompt ensuite le commit, la récupération ordinaire est bloquée plutôt que de rejouer silencieusement une ancienne révision. **Disponibilité et récupération non résolues.** Prévoir une procédure externe de réconciliation autorisée, jamais un « floor=0 » automatique.
* Les octets exportés et importés sont effacés par `fill(0)` sur les buffers accessibles ; cela ne garantit pas l'effacement de toutes les copies en RAM/GC et n'est pas une preuve de protection contre XSS.
* `ownerSession.assertCurrent` et `revisionAuthority` sont des interfaces **à fournir et à auditer** ; leur injection par un appelant malveillant est possible dans le banc synthétique. Le module n'authentifie ni un Bearer, ni un utilisateur clinique, ni une identité Neon.
* Le module n'est référencé par aucune route patient, ni par `database.dart`. Pas de déploiement Vercel, mutation Neon, migration réelle, merge, activation app-lock optionnelle ni donnée clinique.

**Preuve préalable indépendante :** run GitHub [#40713118370](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/40713118370) : 46/46 Node, 3/3 Flutter Chrome SQLite WASM, 0 diagnostic Dart, HEAD `e3b8d60a`. Les tests de ce nouveau lot demandent leur **propre run exact SHA**, non déductible du précédent.

## Séquence gate

A+B+C peuvent être testés indépendamment en synthétique ; D spécification sans mutation ; E **après** certification du coffre et W01 GO. Prochaine implémentation critique : vrai bridge Dart ↔ JS isolé ; authentification propriétaire et floor durable avec recovery sûre ; tests Chrome E2E + revue indépendante ; W01 closeout ; seulement alors décision de livraison D10.

## Revue adversariale interne — ouverture/fermeture

Contrôle supplémentaire : le premier candidat comparait seulement `revision` entre le ciphertext authentifié restauré et le record relu après `memoryFactory.open`. Or un attaquant qui substitue un autre ciphertext valide **de même révision** pendant cette fenêtre pourrait produire un exécuteur mémoire divergent avec un jeton CAS étranger. Le correctif compare désormais les cinq champs intégraux de l'enveloppe et ferme la mémoire si la relecture échoue. Trois tests injectent substitution, erreur de lecture et révocation entre les deux opérations. Un quatrième teste une fermeture pendant une réservation monotone asynchrone. **Seul un nouveau run sur le SHA corrigé** vaut preuve ; revue de sécurité indépendante toujours absente.

Limitation : un IDB commit déjà engagé n'est pas annulable arbitrairement par `close` ; app-lock facultatif interdit avant conception finale d'un protocole de session/logout et tests hébergés.

## Deuxième contrôle de course : floor externe changé pendant l'ouverture

Après lecture du ciphertext et vérification de son empreinte complète, relecture de l'autorité monotone indépendante **avant** d'exposer l'exécuteur mémoire. Si une autre session a réservé la révision suivante avant que la transaction IndexedDB soit visible, l'ouverture est refusée et la connexion mémoire fermée. Deux tests simulent ancre incrémentée et ancre indisponible. Cette double vérification **n'est pas une transaction atomique inter-systèmes** : une révocation plus tardive exige les contrôles d'identité et de floor côté autorité dans le futur runtime Web.


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


## Closeout du sous-lot Option A — 28/10/2026

**Goal exact :** obtenir une autorité monotone **serveur** Preview-only (Django + PostgreSQL sous BFF OIDC existant) et un client JS synthétique qui refuse rollback/clé/compte erroné sans prétendre activer des patients. **Succès observé :** [CI #40725428391](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/40725428391) **SUCCESS** sur exact code SHA [3e9da8b2](https://github.com/hraaaaf/IAMINA-MVP/commit/3e9da8b295cfed896a59ed03c3c47fd87293c328), job `122947437111` ; logs **8/8 Node PASS**, **10/10 PostgreSQL 16 Python PASS** sans avertissement, `manage.py makemigrations --check --dry-run` = « No changes detected », `core.0020_w02_vault_revision_anchor` appliquée au DB de la CI uniquement. Dernière étape vérifie **User.objects.count() == 0** et **W02VaultRevisionAnchor.objects.count() == 0** dans la DB principale éphémère après les tests. La suite teste réservation CAS SQL sous concurrence, Native Bearer/revocation, A/B, reprise après échec, invalid checksum, nouveau scope dérivé de `request.auth.pk`, pas de réutilisation du slot, et suppression cascade.

**Historique de correction, sans effacer les preuves :** run [#40724103699](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/40724103699) SUCCESS pour le serveur ; [#40724612028](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/40724612028) SUCCESS avec 7 Node et 10 Python mais avertissement teardown PostgreSQL dû aux connexions workers de concurrence ; [#40724983493](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/40724983493) SUCCESS 7/7 et 10/10 **sans avertissement** après `connections.close_all()` ; [#40725428391](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/40725428391) SUCCESS 8/8 + 10/10 avec vérification exacte du Django PK dans le namespace.

**Scope vérifié :** diff depuis base W02 `007a213c` n'altère ni `frontend/lib/data/drift/database.dart`, ni `frontend/web/index.html`, ni `frontend/api/preview-proxy.js`. Le BFF existant peut forwarder les routes nouvelles **mais rien n'est actif** : flag `IAMINA_W02_REVISION_ANCHOR_ENABLED` par défaut OFF, Preview-only, production explicitement refusée. Le module JS de protocole est sous `scripts/fixtures`, **pas** dans le bundle patient. Vercel renvoie **zéro déploiement** pour cette branche ; aucune modification Neon/Production, aucune migration cloud, aucun merge.

**Portée strictement atteinte :** protocole serveur et interface JavaScript test-only ; **non** un coffre clinique certifié ni un flux Web hébergé réel. Ne pas activer D10-B facultative, ne pas conclure à une garantie de reprise sans pertes : une réservation validée alors que le navigateur n'a pas écrit laisse le compte en `pending` jusqu'à intervention externe auditable ; l'API ne peut pas prouver l'écriture IndexedDB, et l'ancre exige serveur pour toute écriture (offline read-only). Reste vrai bridge Flutter→API auth epoch, recovery durable (backup), migration legacy `amina`, E2E Web BFF/API/Neon Preview autorisé + destruction SQL indépendante, revue sécurité/privacy indépendante et W01 GO avant merge.

**Next exact :** connecter côté test Flutter Web le protocole JS au véritable client de révision sur Preview après GO explicite Vercel, puis prouver A→logout→B→A/crash/multi-onglets et récupération. Avant cela, tout travail de documentation/tests isolés reste permis. Pas de valeur % D10 prétendument certifiée.


## 2026-10-28 — Flutter Web isolated native session/anchor bridge (post Option A server)

**Goal:** verify actual `AuthService.authEpoch`, `isRemoteCredentialVerified`, persisted/native Django ID, browser token and exact physical vault namespace before **and after** every HTTPS Preview BFF metadata operation; then demonstrate a combined synthetic Chrome transaction through encrypted IndexedDB and volatile SQLite WASM. The new adapter is `frontend/lib/data/drift/w02_native_revision_client.dart`, used only by tests and **never** imported by patient routes or AppDatabase.

**Proof stage 1 (complete):** code [30c84fb1](https://github.com/hraaaaf/IAMINA-MVP/commit/30c84fb1c275a2a0a9c3a88f5d90ae7667ceb0bb), [CI #40728794787](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/40728794787) **SUCCESS**: 63/63 Node; 14/14 Flutter Chrome; 0 analyzer issue. Chrome tested A→logout→B, stale response after logout, Firebase refused, audit/refreshed scope denied, network and invalid Preview host refused. The "syntheticTestOnly" fixture is locked to `https://test-only.invalid`; the real adapter requires the compile-time Preview flag and exact IAMINA Web Preview host.

**Stage 2 (awaiting exact-SHA CI):** code [e1b338a8](https://github.com/hraaaaf/IAMINA-MVP/commit/e1b338a88baa87db20828be3fa7fe345260f6807), [CI #40729430613](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/40729430613) queued at initial observation. New synthetic Chrome test does **not** contact deployed BFF/API/Neon: a `MockClient` models Django state/reserve/finalize while real Flutter Drift SQLite WASM bytes are AES-GCM sealed into real browser IndexedDB by JS, then reopened and compared with the **committed ciphertext envelope SHA-256** before SELECT. The result must not be called PASS until its GitHub run completes.

**Traceable boundaries:** GitHub comparison from W02 baseline `5a705712` to `e1b338a8`: seven files in the isolated fixture and test code, **no change** to `frontend/lib/data/drift/database.dart`, `frontend/web/index.html`, `frontend/api/preview-proxy.js` or backend production code. No Vercel Preview deployed, no Neon mutation and no patient data accessed.

**External blockers, not quietly solved:** (a) no full hosted Vercel Preview BFF→API→isolated Neon E2E without explicit deployment authorization; (b) cloud API feature flag remains OFF by default, W01 GO needed before W02 merge; (c) enrollment/recovery key lifecycle, backup and no-loss data migration of historical `amina` DB require separate user/security decision; (d) AppLock optional policy and real clinical vault opening are not authorized; (e) offline **read-only** is an unimplemented product goal, not a certified behavior: the prototype contacts the authority on each opening and rejects missing network. Option A **forbids offline writes**.

**Next exact:** complete and inspect CI #40729430613; if red, patch and rerun exact SHA; then final evidence/doc consistency, HEAD/CI/branch/Vercel recheck. Next gated step is deployment to isolated Preview and real cross-service E2E only after explicit GO; independent security/privacy review and W01 closeout remain necessary before patient D10 GO.
