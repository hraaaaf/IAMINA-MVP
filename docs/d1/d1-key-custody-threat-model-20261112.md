# IAMINA D1 — custody des clés : preuves et limites

**12 novembre 2026 — PR Draft de recherche — PATIENT NO-GO.**

## Décision utilisateur

La politique approuvée : une clé DEK aléatoire de 256 bits par coffre patient ; protection locale ; un secret de récupération distinct de 256 bits détenu par le patient ; aucun mécanisme d'escrow serveur capable de déchiffrer le dossier. Sans appareil accessible ni clé de récupération, les données peuvent être irrécupérables.

## Ce que fait le prototype

- Génération du DEK et du secret de récupération par WebCrypto cryptographique.
- Protection du DEK par une clé KEK AES-GCM non extractible (CryptoKey) stockée par IndexedDB et, séparément, par une enveloppe HKDF-SHA-256/AES-GCM dérivée du secret de récupération patient.
- AAD lié au propriétaire, à la version, au type d'enveloppe et à un identifiant aléatoire. Sel/nonce propres à chaque nouvelle enveloppe.
- Enrôlement initial en état pending_confirmation. Aucun déverrouillage tant que le secret patient n'a pas été utilisé pour confirmer la même clé que l'enveloppe appareil.
- Pas de remplacement implicite d'un coffre préexistant ; révision optimiste pour les écritures concurrentes. Réassociation d'un nouvel appareil uniquement avec le secret de récupération valide.
- Le coordinateur Dart D1WebVaultKeySessionCoordinator.forAuth(auth, appLock) exige session authentifiée, non-audit, époque stable, verrou déverrouillé, et révoque immédiatement son bail public lors d'un changement auth/verrou. Les workers réels SQLite3MC et la base générée Drift sont exercés en CI synthétique.
- Le code n'est PAS branché dans main.dart ni sur des patients. Aucun coffre legacy n'est migré ou effacé.

## Risque CRITIQUE — preuve adversariale

Une clé CryptoKey non extractible stockée dans IndexedDB n'est **pas protégée matériellement**. Un script malveillant exécuté sur la même origine peut appeler directement unlockDevice, ou utiliser le CryptoKey AES-GCM persisté, **sans réussir l'AppLock visuel**. Non-extractibilité interdit exportKey ; elle n'interdit pas decrypt.

Le test adversarial CI exécute intentionnellement ce scénario et signale la capacité comme **risque NO-GO**, jamais comme un contrôle patient validé. Le JavaScript de test utilise une clé synthétique, sans données médicales. Un vol de profil navigateur, une extension malveillante ou une injection XSS restent des scénarios graves. L'examen CSP, le chargement des scripts, la résistance aux extensions et un audit externe sont obligatoires.

## Bloquants de mise en service

1. **Protection liée à la présence utilisateur / matériel** : évaluer WebAuthn PRF ou une authentification équivalente sur vrai Safari iPhone/PWA. Si la capacité est absente, le choix sûr par défaut à faire valider est la saisie du secret de récupération à chaque nouvelle session plutôt qu'un repli automatique sur la KEK IndexedDB. Aucun fallback silencieux.
2. **UI de remise et confirmation du secret patient** : séquence affichage unique, challenge de confirmation, message clair sur les pertes irréversibles ; pas de mot de passe, PIN, email ou bearer considéré comme une clé aléatoire 256 bits.
3. **Opérations en vol et multi-onglets** : un ancien AppDatabase peut rester référencé par du code après révocation logique ; le contrôle doit imposer annulation/fermeture physique, barrières de concurrence et isolation A→B→A.
4. **Migration et rollback** : ne jamais interpréter automatiquement les données SQLite legacy en clair comme appartenant au prochain compte ; transfert chiffré avec identité et sauvegarde contrôlés. Les révisions dans IndexedDB ne constituent pas une protection anti-rollback contre la restauration de vieux fichiers.
5. **Vraie plateforme** : test physique iPhone Safari/PWA, stabilité IndexedDB, réinstallation, perte de clé, restauration chiffrée, offline et changement de session.
6. **Revue externe indépendante** : sécurité/privacy/crypto et rapport daté sur les commits exacts. Sans cette preuve, aucun merge production, aucun déploiement Vercel même preview, aucune activation des données patients.

## Critères de preuve

Chaque changement de la PR exige le lien du run GitHub complet, le SHA de HEAD réellement testé, les conclusions Chromium + WebKit et les digests des artefacts. Vert sur données fictives ne veut PAS dire GO clinique.
