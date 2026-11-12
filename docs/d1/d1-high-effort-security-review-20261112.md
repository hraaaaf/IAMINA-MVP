# D1 — revue interne contradictoire, 2026-11-12 (NON INDÉPENDANTE)

**Décision : PATIENT NO-GO.** Cette revue est interne, pas une certification indépendante. Elle couvre le snapshot de recherche basé sur #1356, pas un déploiement. Aucune donnée patient réelle ne sert aux expériences.

## Critiques bloquantes, priorité sécurité

| Rang | Élément et preuve source | Risque concret | Preuve qui lèverait le blocage |
| --- | --- | --- | --- |
| CRITIQUE | `AppDatabase.forPatientVault` : `sqlite3.wasm` et `drift_worker.js` sans admission de clé | données patient Web écrites en SQLite ordinaire ; un test de moteur synthétique ne protège pas ce parcours | Injecter vrai `QueryExecutor` alimenté par worker SQLite3MC, test sur octets réels du coffre du parcours auth, mauvaise clé, zéro fallback, ancien coffre clair protégé |
| CRITIQUE | `LocalBackup.exportVaultJson` retourne `jsonEncode(envelope)` clair | toute copie/export peut exposer données médicales | export exclusivement scellé via crypto vérifiée, refus du JSON clair, KAT cryptographiques, backup/restauration de bout en bout en transaction |
| CRITIQUE | `main.dart` construit et réconcilie `PatientVaultSessionController.forAuth` après initialisation app-lock, mais sans vérifier `isUnlocked` avant ouverture | fermeture visuelle ne suffit pas à protéger une clé/connexion mémoire ; une ouverture de DB avant déverrouillage reste possible | admission de clé post-déverrouillage avec événement de lock provoquant fermeture/zeroization et preuve session A/B |
| HAUT | La clé de test worker est une constante publique CI ; `D1EncryptedWorkerPort.verifyEncryptedConnection` peut être simulée | un fake passerait les tests de contrat alors que runtime non chiffré | clé haute entropie transférée via canal revocable réel, attestation physique, revue indépendante du protocole |
| HAUT | Aucun stockage/enveloppe/recovery user-proof de la clé de coffre et aucune migration chiffrée des vaults existants | données inaccessibles ou copies résiduelles non chiffrées | décision humaine recovery, stratégie d'escrow si voulue, anti-rollback, réplication, tests destruction volontaire sur données synthétiques seulement |
| HAUT | Multi-tab/leak tests uniquement synthétiques et WebKit Linux | Safari iOS PWA physique et limitations IndexedDB/OPFS non prouvées | iPhone réel, PWA offline, deux onglets, changement réseau et réinstallation avec captures/identifiants d'appareil |
| HAUT | Auth epoch + fence logique ne bloquent pas une opération SQLite déjà déclenchée | opération A peut se terminer après logout et toucher stockage physique | cancellation/leasing sur worker réel + test concurrent mutation puis logout ; aucun write post-révocation |
| HAUT | Absence de revue extérieure des primitives crypto/architecture et de test de restauration lors d'un crash | fail-open, perte de données, atteinte confidentialité/intégrité | audit externe indépendant, rapport daté signé, replay/tamper/rollback/recovery testés |

## Décisions qu'il est dangereux de simuler

- Il est **interdit** d'utiliser la clé fixe du banc, un token d'API, un mot de passe humain brut, un UUID ou un WebAuthn assertion comme clé de DB.
- La récupération peut prendre deux directions, à arbitrer avec le responsable produit et le spécialiste sécurité : (a) secret de récupération haute entropie remis à l'utilisateur ; (b) solution escrow serveur, avec risques et responsabilité accrus. Un simple « mot de passe oublié » ne garantit **pas** une récupération sans architecture supplémentaire.
- Une CI WebKit Linux ne certifie **jamais** Safari iOS réel.
- Une revue écrite par le même développeur, même contradictoire, n'est **pas** un audit indépendant.
- Les commits de recherche restent Draft : **aucun merge, Vercel Preview/Production ou activation clinique** sans human gate.

## Critères de sortie D1

1. Clinique Web = worker chiffrant correctement relié à `AppDatabase`, admission de clé après unlock et authentification réelle.
2. Mauvaise clé et clé absente refusées ; démonstration stockage physique IndexedDB/OPFS + auxiliaires sans marqueurs fictifs.
3. A→logout→B→A, multi-tab et révocation d'opérations et de clés sous concurrence, preuve E2E.
4. Backup authentifié, propriétaires liés, restauration transactionnelle et récupération malgré crash ou mauvaise clé.
5. Safari réel iPhone/PWA avec provenance/captures et tests hors ligne.
6. Rapport d'audit indépendant et revue privacy ; décision GO/NO-GO enregistrée.
7. Migrations/restauration des coffres antérieurs planifiées sans inventer de propriété et sans effacer de données.
