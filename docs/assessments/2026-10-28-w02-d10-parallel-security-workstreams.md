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
