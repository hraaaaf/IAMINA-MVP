# IAMINA W02/D10 — Web Dart ↔ JS AES-GCM IndexedDB Browser Proof (28/10/2026)

## Goal
In real Chrome test only, pass actual Drift SQLite WASM bytes Dart→JS Uint8Array, encrypt with AES-256-GCM, persist ciphertext-only in IndexedDB through atomic CAS, reopen via WebCrypto, and rehydrate a second volatile Drift executor. Deny wrong secret, wrong synthetic owner and stale revision. Never touch patient runtime/legacy data.

## Strict perimeter
- `iamina_w02_browser_bridge_probe.mjs` permits only synthetic `amina_vault_v1_native_734`/`812` fixtures. The user-held secret, slot and trusted revision supplied by tests are NOT a clinically sound recovery/authorization mechanism. No external trusted monotonic floor.
- `w02_synthetic_browser_bridge.dart` uses typed-array JS interop from an imported ES module, pinning the URL to `http://127.0.0.1:7399/iamina_w02_browser_bridge_probe.mjs`; no arbitrary source, no production path import. Buffer clearing is best effort.
- Fixture HTTP server serves the bridge fixture from scripts/fixtures, never from frontend/web packaged application assets, and exposes only WASM plus the audited dependency modules; no patient secrets, data, or arbitrary directories.
- Garde `database.dart` remains `encrypted_web_patient_vault_unavailable`; no Vercel/Neon/Production/merge.
- A green JS test and a green Chrome SQLite test do not substitute for **this** actual Dart↔JS round-trip. Only exact-SHA CI is proof.

## Remaining gates
Authenticated owner and auth-epoch contract with verified principal, reliable monotonic revision authority OUTSIDE browser/local storage, recovery UX following crash/quota, permanent key/backup lifecycle, migration legacy with verified owner and no-loss, E2E A→B→A hosted, independent security/privacy audit, W01 closeout, then user-approved Preview and UI BEFORE/AFTER. No D10-B Web patient enablement.

## Accessible in-memory VFS byte arrays — best-effort scrub

On closing or aborting initialization, the candidate overwrites reachable VFS file data buffers with zeros before dropping the entries. This is not a verified wipe of all SQLite/WASM/JS/GC memory copies and does NOT eliminate XSS or debugger exposure. New Chrome CI must confirm unchanged SQL restore behavior and analyzer status. Patient Web guard unchanged.


## 28 octobre 2026 — Closeout exact-SHA : navigateur réel et durcissement VFS PASS

**Preuve finale :** HEAD code [5d534e04d4fa](https://github.com/hraaaaf/IAMINA-MVP/commit/5d534e04d4fa5ac954e742f1c814e5be4c2f2630), [GitHub Actions run #40721633619](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/40721633619), job `122933807084`, **SUCCESS**, logs : **63/63 Node PASS**, **5/5 Flutter Chrome PASS**, **0 Flutter analyzer issue** (`--fatal-infos`). Chrome a testé le flux complet SQLite WASM/Drift → JS Uint8Array → AES-256-GCM WebCrypto → CAS IndexedDB ciphertext-only → déchiffrement → second exécuteur Drift SELECT, plus mauvais secret, scope B et floor supérieur. Le VFS mémoire écrase avec `fillRange` les buffers atteignables avant `clear`, sans garantir l'effacement complet en RAM/GC.

**Historique des échecs préfinal :** runs 40721290007, 40721377823, 40721481773 FAIL sur assertion source Node liée à l'ancien `clear()` / `buffer?.fillRange` après refactor ; aucun de ces trois runs n'a exécuté Chrome. Contrat corrigé après lecture du log et test exact des regex contre le Dart courant, puis CI entièrement verte sur nouveau SHA. Ne jamais présenter les anciennes CI FAIL comme PASS. Runs 40720479457 et 40720733757 ont été annulés pendant corrections, et run #40720861475 SUCCESS sur ancien code **sans** le scrub VFS.

**Portée vérifiée :** diff GitHub entre `ac8b682f` et `5d534e04` limité à huit fichiers dans le banc W02, aucun changement à `frontend/lib/data/drift/database.dart` ni `frontend/web/index.html`. Fixture ES module exclusivement sous `scripts/fixtures`, servie sur loopback par whitelist GET/HEAD, non livrée dans les assets Web. Vercel `list_deployments(branch=W02)` renvoie **0 déploiement**. Aucune fusion, mutation Neon, consultation de données patient ou activation clinique.

**Décision D10-B patient : NO-GO.** L'autorité de révision est injectée/mock dans les tests ; un floor navigateur n'est pas une ancre sûre. La gestion des clés/récupération offline, le protocole atomique externe et BFF auth-epoch, le schéma clinique réel, la migration legacy no-loss, l'E2E A→logout→B→A et l'audit sécurité/privacy indépendants ne sont pas achevés. W01 reste préalable au merge W02 ; Vercel exige autorisation explicite séparée.

**Next exact :** valider le choix d'ancre durable côté identité BFF avec politique de cohérence hors-ligne et récupération de crash (enjeu produit : local-first vs anti-rollback strict), puis implémenter en isolation la vérification d'auth-epoch et le commit/récupération sans activer les patients. Tests multi-navigateurs et audit indépendant après établissement du protocole.
