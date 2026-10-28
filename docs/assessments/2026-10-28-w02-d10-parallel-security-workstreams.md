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
