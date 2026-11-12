# IAMINA — D1 / WebAuthn PRF : Safari iPhone, étude de sécurité

12 novembre 2026. PR Draft, recherche exclusivement, PATIENT NO-GO.

## Faits vérifiés par documentation publique

- WebKit annonce WebAuthn PRF dès Safari 18 : https://webkit.org/blog/15865/webkit-features-in-safari-18-0/
- Apple l'inscrit dans ses notes Safari 18 : https://developer.apple.com/documentation/safari-release-notes/safari-18-release-notes
- Apple Safari 26.4 ajoute un support hmac-secret CTAP de clés externes : https://developer.apple.com/documentation/safari-release-notes/safari-26_4-release-notes
- La sortie PRF réellement exploitable doit être vérifiée sur chaque passkey. Un résultat getClientCapabilities favorable ne suffit pas : https://developer.mozilla.org/en-US/docs/Web/API/Web_Authentication_API/WebAuthn_extensions
- Yubico mentionne les limitations iOS des authentificateurs externes : https://developers.yubico.com/WebAuthn/Concepts/PRF_Extension/Developers_Guide_to_PRF.html
- Chromium permet l'émulation WebAuthn hasPrf et hasUserVerification, sans équivalence avec un appareil physique : https://chromedevtools.github.io/devtools-protocol/tot/WebAuthn/

## Choix technique candidat, non activé

- WebAuthn platform authenticator, résident, vérification utilisateur exigée, challenge renouvelé et comparaison locale de l'origine et des flags UP/UV. Création exige explicitement prf.enabled, authentification exige prf.results.first = 32 octets.
- Dérivation HKDF-SHA-256 puis enveloppe DEK AES-256-GCM avec propriétaire, version, credential ID et origine dans l'AAD. Aucun secret PRF ou DEK persistant en clair.
- Indisponibilité PRF, absence de geste ou UV, passkey étrangère, données falsifiées : refus fermé ; aucun fallback automatique sur la CryptoKey IndexedDB précédemment jugée insuffisante.
- Une clé de récupération patient hors-ligne de 256 bits restera une option explicite et séparée, jamais un contournement silencieux.
- Aucun service ni main.dart ne charge ce module, aucune clé patient ni identifiant médical réel.

## Preuve du banc (à compléter avec CI exacte)

- Chromium Playwright et authentificateur virtuel : vraie cérémonie navigator.credentials.create/get PRF, enveloppe AEAD, refus sans geste, refus UV, propriétaire étranger, chiffrement falsifié, persistance après reload.
- WebKit Linux : authentificateur PRF artificiellement déclaré non compatible ; vérification du refus fermé et absence de stockage d'enveloppe. CE TEST NE PROUVE PAS LA COMPATIBILITÉ SAFARI/IPHONE OU FACE ID.
- CI doit nommer son SHA, les deux résultats et les empreintes d'artefact ; aucun pourcentage de sécurité inventé.

## Risques toujours ouverts / Human gate

1. Safari iPhone physique (version iOS, Safari normal/PWA, passkey Face ID, présence de résultats PRF après get, annulation, offline, origine HTTPS IAMINA) : non testable dans cette CI Linux.
2. Une passkey PRF ne prouve pas à elle seule une connexion à l'identité Django ; il manque la liaison d'enrôlement vérifiée et le contrôle de la signature WebAuthn sur challenge côté serveur.
3. Les passkeys peuvent être synchronisées dans iCloud/autres gestionnaires ; disponibilité PRF et caractère matériel ne sont pas garantis après transfert.
4. Une attaque XSS de même origine peut toujours provoquer des invites de passkey et intercepter des valeurs dans la session déverrouillée. CSP, revue des scripts et audit indépendant obligatoires.
5. Le coordinateur AuthService/AppLock, les barrières d'opérations en vol et les multi-onglets ne sont pas intégrés au module PRF ; rester fail-closed pour tout patient.
6. Migration legacy, UX perte de clé, backup, anti-rollback : chantier clinique encore ouvert. Pas de merge, pas de Vercel, pas de données réelles, pas de GO patient.
