# D1 — contrat partagé de sécurité Web (proposé, non certifié)

**Portée stricte :** nouvelles installations Web/PWA uniquement. Zéro migration de patients historiques, zéro compte réel dans les bancs, aucune donnée de développement détruite. État actuel : **PATIENT NO-GO**. La PR #1350 vérifie le vrai schéma Drift sur un banc synthétique chiffré, PAS le runtime `AppDatabase.forPatientVault`.

## Sémantique imposée à A / B / C

1. **Identité :** un principal authentifié est lié à un `PatientVaultScope.databaseName` immuable et à un `AuthEpoch` capturé. Une chaîne de nom de DB seule ne constitue jamais une autorisation. L'espace `auditOnly` et le legacy `amina` ne doivent jamais servir à l'enrôlement clinique.
2. **Admission :** aucune ouverture de vault patient avant vérification d'identité, admission du matériau cryptographique et validation du nom de coffre + epoch. L'absence de clé, l'échec d'API, la perte de lock ou une mauvaise clé doivent refuser l'accès, sans fallback vers le `sqlite3.wasm` clair ni in-memory. Sur changement de compte, révoquer l'ancienne capacité avant toute nouvelle publication UI/sync ; ignorer les opérations asynchrones périmées.
3. **Clés :** racine forte, générée par CSPRNG ou déverrouillée via un mécanisme contrôlé ; clés de DB, backup et éventuelle authentification dérivées séparément avec contexte de propriétaire et identifiant de version. Ne pas dériver de l'email, ID, jeton bearer, UUID, secret statique, ni de la clé de démo. Jamais dans URL, localStorage, log, nom du coffre, messages d'erreur ou artefacts de CI. Le transport vers le worker doit être explicite, éphémère et limité au port/session autorisé, avec gestion des messages retardés.
4. **DB physique :** SQLite3MC VFS chiffrant nommé `multipleciphers-${vfs.name}` ; `PRAGMA key` avant **toute** lecture SQL ; contrôle positif de chiffrement + mauvaise clé rejetée. Sur chaque écriture, considérer WAL, fichiers auxiliaires, export, stockage IndexedDB/OPFS et persistence réelle ; aucune assertion PASS sans inspection d'octets de contrôle clair et chiffré.
5. **Backup :** format versionné exclusivement chiffré avec authentification cryptographique (AES-256-GCM ou variante validée), IV/nonce frais par export, clé de backup indépendante du coffre, métadonnées AAD liées au propriétaire/vault/version. Rejeter altération, mauvaise clé, ancien format clair, A→B, version inconnue **avant toute opération destructive**. Restaurer dans une transaction et vérifier la récupération + rollback sans fuite de copies claires.
6. **Session :** transitions A → déconnexion → B → A et deux onglets, expirations/révocations, switch pendant ouverture, absence d'identité et fail-open simulé. Ne jamais publier de Provider d'un ancien compte après nouvelle epoch.
7. **Preuve :** tests synthétiques unitaires + CI navigateur Chromium/WebKit sur le même HEAD ; Safari physique iPhone/PWA, simulation perte réseau/recovery/rollback et audit indépendant nécessaires pour GO patient. Ne jamais assimiler compilation ou CI verte sur banc à mise en sécurité du runtime patient.

## Interfaces de lot, verrou de fusion

- **A — worker + clés :** fournit `EncryptedVaultOpener` (API future à finaliser après audit) acceptant seulement une capacité liée à owner/epoch ; ne touche ni auth ni backup. Interdiction de modifier `AppDatabase.forPatientVault` avant preuve E2E fail-closed.
- **B — backup :** fournit un codec chiffré authentifié et un adaptateur d'export/restore lié à owner/epoch, sans intégrer un flux de JSON clair en production tant que l'API est préexistante. Aucun restore destructif avant authentification du backup et vérification owner.
- **C — isolation :** fournit fencing, annulation et tests concurrents avec fausses clés; ne choisit pas les paramètres crypto de A/B. Éviter l'identité stockée seulement par nom de DB.
- **D — intégration :** compare contrat, commits, tests et artefacts au **même SHA**, effectue E2E réel synthétique, Safari physique et revue sécurité/privacy. L'intégration attend les dépendances A/B/C ; aucun merge, déploiement Vercel Preview ou Production sans décision distincte.

## Blocage / next

Ce contrat est **proposé et testable**, pas une certification de conception cryptographique. La politique de récupération de la clé maîtresse et de son enveloppe (appareil, passphrase, secret de récupération, révocation multi-devices) devra être examinée explicitement avant toute activation patient. L'utilisateur a autorisé le travail en branches Draft uniquement.
