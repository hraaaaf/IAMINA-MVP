# IAMINA D18 Web — 6/6 Pré-audit sécurité Web (03/11/2026)

**Décision : D18, chiffrement au repos de l'intégralité du coffre clinique SQLite Web.**

**Goal exact :** établir les preuves de non-régression, repérer les risques liés au build normal et formaliser les critères bloquants avant toute activation clinique. Cette analyse ne constitue **ni un audit de sécurité indépendant ni une autorisation de release**.

## Périmètre de l'inventaire automatique

Le workflow `.github/workflows/d18-stage6-web-security-inventory.yml` construit **la vraie application Flutter Web** depuis `frontend/lib/main.dart`, avec les dépendances verrouillées, en mode démo local hors Vercel. Il lance `tools/d18_stage6_bundle_inventory.js` contre `frontend/build/web`.

**Succès du contrôle de fuite :**
- aucun worker expérimental de chiffrement, restauration, ancien test ou contournement de Web Locks n'est publié comme asset dans le dossier du build ordinaire ;
- aucune chaîne de secret ou commande synthétique explicitement interdite n'est retrouvée dans les actifs JavaScript/HTML/JSON de ce même build ;
- les points d'entrée ordinaires `index.html` et `main.dart.js` sont réellement produits ;
- un rapport JSON manifeste les constats, **même si le test de fuite passe**.

Une analyse de chaînes **ne prouve pas** l'absence de toutes les données sensibles ni la résistance à un attaquant. Elle est une barrière de packaging, limitée aux identifiants testés.

## Constats dans les fichiers du dépôt

| Sujet | Constat vérifié dans le code | État release |
|---|---|---|
| SQLite du patient actif | `frontend/lib/data/drift/database.dart` : `AppDatabase.forPatientVault` emploie `sqlite3.wasm` et `drift_worker.js`, non sqlite3mc | **NO-GO** : les vrais coffres patients persistent toujours en clair |
| Worker sqlite3mc | Expérimenté en CI seulement ; dépend du transport à deux `MessagePort`, de Web Locks et d'une version WASM contrôlée par SHA256 | Revue cryptographique/transport indépendante requise |
| Confidentialité à l'exécution | La clé réside en mémoire déverrouillée pendant la session ; un script same-origin/XSS peut agir avec les privilèges de la page | **NO-GO tant que défense XSS/CSP non démontrée** |
| Protection CSP | `vercel.json`, `frontend/vercel.json`, `frontend/web/index.html` ne configurent pas de `Content-Security-Policy` | Politique **report-only** compatible Flutter/WebAssembly à concevoir puis CSP imposée et en-têtes de la Preview **mesurés réellement** ; absence de configuration n'atteste PAS absence d'en-tête au CDN |
| Sauvegarde intégrale | Codec `d18_full_cipher_archive.dart` AES-256-GCM avec PBKDF2 600000, enveloppe publique DEK, namespace authentifié ; tests de round-trip synthétique | Plafond pilote **16 Mio**, format JSON/base64 en mémoire ; streaming et test de grandes bases non prouvés |
| Restauration physique | CI navigateur Chromium et WebKit sur données fictives : 10/10 chacun, refus mauvaise archive, mauvaise clé, écrasement, crash partiel et double ouverture | Import partiel laissé en quarantaine ; procédure contrôlée de nettoyage/reprise idempotente **non implémentée** |
| Durabilité/quotas | IndexedDB VFS avec flush, redémarrages Chromium/WebKit passés pour petits jeux synthétiques | Expiration/éviction, quota saturé, onglet en arrière-plan et coupure appareil réel non certifiés |
| Safari réel | WebKit Playwright Linux en mode tactile 390px a passé 10/10 | iPhone Safari **physique** pas testé, gate distinct |
| Migration historique | Test source→cible intégrale v12 avec rollback/crash et verrou coopératif dans banc | TOUS les vrais writers du runtime legacy, transaction de cutover, preservation du backup et états de reprise non démontrés |
| UX et consentement | Aucun écran de bascule clinique autorisée sur ce sous-lot | Textes FR/AR, gestion du code perdu, fichier hors device et preuve BEFORE/AFTER à approuver |
| Revue externe | Aucun rapport de revue sécurité clinique indépendant présent dans ce sous-lot | **NO-GO** |

## Références techniques et garde-fous

- Le stockage chiffré n'est pas une protection contre une injection de script same-origin. Il faut une revue des chemins DOM/URL, des dépendances Flutter/JS, de la configuration des workers et des sources chargées. OWASP : https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html
- CSP doit être défini avec mesure préalable de compatibilité, sans autoriser de sources arbitraires pour « faire passer les tests ». OWASP : https://cheatsheetseries.owasp.org/cheatsheets/Content_Security_Policy_Cheat_Sheet.html ; MDN : https://developer.mozilla.org/en-US/docs/Web/Security/Practical_implementation_guides/CSP
- Sauvegarde, rotation et clé enveloppée (DEK/KEK) sont des risques distincts. OWASP : https://cheatsheetseries.owasp.org/cheatsheets/Key_Management_Cheat_Sheet.html
- Moteur WebKit CI Linux ≠ iOS Safari physique. Tests à exécuter conformément à `docs/security/d18-webkit-mobile-qa-20261103.md`.
- Quarantaine d'une restauration interrompue doit rester **fail-closed** tant que la politique de récupération contrôlée n'est pas revue. Le protocole ne doit jamais supprimer un coffre existant au motif qu'une réouverture a échoué.

## Critères de sortie 6/6 — stricts

1. Le résultat compilé du patient ne contient pas les workers/constantes de test ; inventaire enregistré avec SHA exact.
2. Le cycle source→coffre chiffré a une procédure réellement atomique/idempotente, conservant la source et une sauvegarde indépendante jusqu'à parité démontrée.
3. Code patient activé seulement après preuve de chiffrement physique du vrai runtime, évaluation d'absence de repli en clair et AuthEpoch sur sessions.
4. Safaris réel et Chrome, gros volumes, éviction, crash, gestion de clés et restauration par fichier valident le plan de non-perte.
5. CSP et XSS ont des preuves par observation HTTP et tests d'attaque pertinents, pas seulement des déclarations dans les sources.
6. Code review indépendante sécurité/clinique, politique de rollback, consentement et UX accessibles acceptés.
7. **Autorisation explicite** avant preview/deploy Vercel, merge ou activation clinique ; aucune inférence du message « go » sur ces gates.

**État de cette note :** inventaire et critères définis ; validation de leur nouveau workflow à vérifier sur SHA exact. Les étapes de conformité et de bascule clinique restent **ouvertes**.
