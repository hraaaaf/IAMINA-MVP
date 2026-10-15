# IAMINA — W02 coffre Web, preuves de code (audit statique)

Date : 2026-10-15. Statut **GATE HUMAIN / NON CERTIFIÉ**. Lecture source de `main@f69e0e3178fbd3d66c9d2682b3e42f0244ee27ea`. Pas de données patient, accès navigateur ou mutation runtime dans cet audit.

## Faits observés

1. **Séparation physique préparée :** `frontend/lib/data/drift/patient_vault_scope.dart` crée des noms de bases distincts pour utilisateur Django et appareil local UUIDv4. `frontend/lib/data/drift/database.dart` appelle `driftDatabase(name: scope.databaseName, web: DriftWebOptions(sqlite3Wasm: ..., driftWorker: ...))`. Cette construction prépare des namespaces isolés, **sans valider l'isolation applicative A→logout→B→A**.
2. **Transition de session :** `frontend/lib/services/patient_vault_session_controller.dart` retire `activeDatabase` lors d'un changement d'identité, attend la fermeture de l'ancienne base, invalide les opérations par génération et `AuthEpoch`. Le commentaire source explicite qu'il **ne s'agit pas d'une certification de tous les providers**.
3. **Stockage médical :** la table `LogEntries` stocke `bloodSugar` en `RealColumn` et `ChatMessages` stocke `message` en `TextColumn` dans une base Drift Web SQLite/IndexedDB. L'appel de création Drift visible n'expose **aucune configuration de chiffrement des données au repos**. Cela **n'est pas une preuve que toute la chaîne est en clair**, mais **aucune garantie de chiffrement au repos ne peut être attribuée à ce constructeur**.
4. **App-lock :** `frontend/lib/services/app_lock_authenticator_web.dart` délègue au JS `frontend/web/iamina_app_lock.js`, qui vérifie des assertions WebAuthn, empreintes et signatures. **Vérifier une assertion WebAuthn ne prouve pas le chiffrement de SQLite/IndexedDB.** Les deux gates doivent être distincts.
5. **Frontière produit :** `docs/LOCAL_FIRST_RUNTIME_BOUNDARY.md` exige une autonomie patient locale et interdit de traiter la stack Vercel/Neon de certification comme runtime patient. `docs/ROADMAP.md` W02 et W14 demandent explicitement un arbitrage santé/clé/récupération et une certification avant toute distribution patient.

## Gate observable W02 (non passé)

- **A→logout→B→A** : aucun écran, provider, cache, requête en vol, service worker ou historique A accessible à B, y compris reload/hard reload et comptes neufs.
- **Confidentialité au repos** : démontrer concrètement chiffrement et clé locale de coffre pour la cible navigateur, rotation, récupération/revocation, effacement, migration legacy. Capturer la preuve en navigateur (artefacts exclusivement synthétiques), sans journaliser données/clé.
- **Offline** : après première initialisation, usage clinique local et changements d'utilisateur sans réseau, sans réactivation silencieuse d'une session externe.
- **Comportements défavorables** : stockage désactivé/quota plein, navigateur privé, plusieurs onglets, panne navigateur, perte de clé, indisponibilité API/Neon ; jamais attribution du legacy unscoped à un nouvel utilisateur.
- **Sécurité et processus** : revue crypto et architecture indépendante, consentement, obligations CNDP et sous-traitance/transferts, clinique/privacy/adversarial W14.

## Décision humaine requise

Arbitrer **comment** le coffre local Web est chiffré et récupéré (modèle des clés, perte d'appareil, sauvegarde, synchronisation facultative, classification/durées de conservation), puis test de migration et de retour arrière. Aucun algorithme, mot de passe, service tiers ni synchronisation médicale ne sont présumés approuvés par le seul feu vert CI.

**Verdict : W02 BLOQUÉ ; production patient NO-GO.** À ne pas confondre avec une réussite d'un smoke Flutter→Django→PostgreSQL sur données synthétiques.
