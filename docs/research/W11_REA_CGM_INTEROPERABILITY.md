# W11 — REA CGM interoperability research (Web-only, synthetic)

Status: research tooling only. No vendor APK was analyzed, no patient data or vendor credential is allowed. This document does not authorize patient CGM cloud ingestion, Vercel deployment, or a change to W01/W02 gates.

## Goal / acceptance / evidence

Goal: use [REA](https://github.com/morluto/rea) to understand *where* CGM apps expose data, then design one vendor-neutral IAMINA Django → Flutter Web interface.

Acceptance: (1) pin each artifact version and SHA-256, (2) identify source → transport → schema → timestamp/units → error/retry semantics, (3) cross-check static findings with controlled synthetic traffic, (4) distinguish Android capabilities from iOS limitations, (5) do not claim a working connector without reproducible end-to-end tests.

## Source-first baseline (verified by GitHub source inspection)

- xDrip+ [`UiBasedCollector.java`](https://github.com/NightscoutFoundation/xDrip/blob/master/app/src/main/java/com/eveningoutpost/dexdrip/services/UiBasedCollector.java): Android `NotificationListenerService`, `onNotificationPosted` hook. Study per-app parsing and user consent; notifications are not guaranteed on iOS or for every app/version.
- xDrip+ [`NightscoutUploader.java`](https://github.com/NightscoutFoundation/xDrip/blob/master/app/src/main/java/com/eveningoutpost/dexdrip/utilitymodels/NightscoutUploader.java): Nightscout upload and `api-secret` header. Extract the actual REST paths, payload shapes, auth variants and retry handling from code before implementing any compatibility layer.
- [Nightscout server](https://github.com/nightscout/cgm-remote-monitor): protocol reference; keep a narrowly scoped *synthetic-only* Nightscout test service distinct from production medical ingestion.
- IAMINA [`backend/integrations/cgm/nightscout.py`](../../backend/integrations/cgm/nightscout.py): existing **GET reader**, not a POST receiver. Reuse the normalized `CGMReading` contract and patient isolation. Preserve CGM local-only guard until independent safety/privacy gate.
- LinX app release notes advertise Nightscout support on iOS/Android, but actual export direction, authentication, cadence and reliability remain **unverified**. Dexcom and Libre cloud bridges have unofficial-API and regional reliability risks.

## REA integration: optional local analyst tool

REA is **not a production IAMINA dependency**. The optional analyst installation runs on a dedicated sandbox workstation. Review its source and lock a vetted `rea-agents` version and package integrity before installation; never execute unreviewed `npx ...@latest` in CI. Official instructions: https://github.com/morluto/rea/blob/main/docs/installation.md and https://github.com/morluto/rea/blob/main/docs/android-analysis.md .

Prerequisites per REA docs: Node.js >=22.19 (or supported 24.x/26.x), JDK >=17, a verified/pinned `jadx-headless-mcp` JAR for APK static inspection. A binary-analysis engine is optional and separately installed. **Node 22.16 is insufficient**.

On an authorized local workstation, after reviewing and installing pinned REA and its pinned JADX engine:

```bash
rea inspect-android-package /absolute/path/to/authorized-app.apk
rea search-android-classes /absolute/path/to/authorized-app.apk Nightscout
rea search-android-classes /absolute/path/to/authorized-app.apk Libre
rea search-android-classes /absolute/path/to/authorized-app.apk Health
```

Never put APKs, screenshots with patient identifiers, tokens, credentials, decrypted app stores, TLS private keys or proprietary code in IAMINA Git/CI/Notion. Do not bypass certificate pinning, login, permissions, DRM, or device isolation. APK analysis alone does not prove live network behavior; Apple app sandbox does not expose other apps' internal data to Flutter Web.

## Vendor research matrix — required evidence

| Source | Open-source inspection | Optional REA target | Web delivery candidate | Status |
|---|---|---|---|---|
| Dexcom | xDrip collector/uploader; Nightscout Connect | Authorized Android APK, metadata only | Nightscout-compatible authorized bridge | Unproven end-to-end |
| FreeStyle Libre | xDrip collector/uploader; Nightscout Connect | Authorized Android APK, metadata only | LibreLinkUp bridge or permitted export | Unproven end-to-end |
| LinX | Nightscout protocol and published app support | Authorized Android APK, metadata only | Native app Nightscout export **if verified** | Unproven end-to-end |

## Tests before any integration claim

1. Feed synthetic, isolated Dexcom/Libre/LinX fixtures through the existing IAMINA GET adapter; assert timestamps, mg/dL, provenance, sorting and stale handling.
2. Fuzz malformed entries, duplicates, out-of-order timestamps, impossible glucose values, wrong account and auth failures; require fail-closed isolation.
3. Only after W01 and privacy/security gates, design any POST ingestion and consent workflow; no clinical alerts, dose advice or unsupported real-time claims.
4. For UI, mandatory BEFORE → goal → reference/mockup → AFTER same browser viewports → accessibility/RTL and visual comparison.

**Next:** install and run pinned REA in an authorized environment with an authorized sample APK (no patient data), capture evidence IDs and hashes, and compare source-derived Nightscout semantics with the synthetic lab. No production deployment.

## 18 octobre 2026 — découvertes et préparation d'une exécution REA isolée

**xDrip+ inspecté en source** : `UiBasedCollector.java` déclare des notifications Android de `com.dexcom.g7` et `com.microtech.aidexx.mgdl` (LinX). `onNotificationPosted` filtre les notifications ; `handleNewValue` accepte uniquement 40–405 mg/dL et applique une déduplication. Ceci ne prouve ni la compatibilité d'une app réelle ni une récupération sur iOS. La prise en charge de Libre 3 n'a pas été établie par cet inventaire.

**Nightscout** : `NightscoutUploader.java` de xDrip+ utilise `@POST("entries")` et l'en-tête `api-secret`. La documentation [Local Web Services](https://github.com/NightscoutFoundation/xDrip/blob/master/Documentation/technical/Local_Web_Services.md) expose `127.0.0.1:17580/sgv.json` avec des valeurs **toujours en mg/dL**. Ce localhost est celui du téléphone Android ; le navigateur Web et le backend IAMINA n'y accèdent pas automatiquement, et CORS doit être vérifié.

**Sources** : [UiBasedCollector](https://github.com/NightscoutFoundation/xDrip/blob/master/app/src/main/java/com/eveningoutpost/dexdrip/services/UiBasedCollector.java), [NightscoutUploader](https://github.com/NightscoutFoundation/xDrip/blob/master/app/src/main/java/com/eveningoutpost/dexdrip/utilitymodels/NightscoutUploader.java).

**Banc REA préparé** : `.github/workflows/rea-android-synthetic-lab.yml` doit installer la version fixe REA 6.7.0 (tag officiel commit `27dc42d10249f0410904a75c0997842eb03b931c`) sur Node 24.11 + JDK 21, puis analyser l'APK open source Appium ApiDemos v6.0.18. Empreinte APK `a9eecf37b26cd084855c530db81c2bb1b91f4c1b095a04f47aa7c20e2791f686` ; JADX 0.7.1 `6e5eacf500b64292bfb73c49797c1958f6ee44646e43e868039ae7feb573ff75`. Vérifier les deux SHA avant l'exécution ; aucune donnée patient ou application propriétaire, aucun deploy. **REA n'a pas encore été exécuté ; le futur run CI seul en établira l'issue.** Un APK de démonstration ne certifie pas la compatibilité Dexcom/Libre/LinX.

**Next** : vérifier une fois la CI de la PR #1129, diagnostiquer les échecs éventuels, comparer les résultats à la source xDrip/Nightscout, revue indépendante/certification et maintien du gate W01 NO-GO avant intégration clinique.

## 18 octobre 2026 — preuve d'exécution REA 6.7.0 RÉELLE sur APK public

GitHub run [#39153022150](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/39153022150) **SUCCESS** (HEAD `8e1c89f4e6209e439451a0ce31afb6da3cfce94d`). Journal : REA 6.7.0 s'installe, SHA256 de l'APK Appium et de JADX validés ; `rea inspect-android-package` et `rea search-android-classes` se terminent avec code 0. Archive [#12145743184](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/39153022150/artifacts/12145743184) téléchargée, décompressée et JSON inspectés : `inspect.json` 323994 octets, `classes.json` 3556 octets, `doctor.json` 6536 octets, `evidence-summary.json` 327 octets. Moteur `jadx-headless-mcp 0.7.1`, paquet `io.appium.android.apis`, version `6.0.18`, **2876 classes**, noms `io.appium.android.apis.ApiDemos` et `...ApiDemosApplication`, coverage des recherches `complete` (sur l'inventaire JADX uniquement). Voir [rapport canonique](evidence/W11_REA_APIDEMOS_2026-10-18.md).

Ce run établit que **REA/JADX fonctionne dans GitHub Actions pour une APK de démonstration**, pas l'accès à une application réelle Dexcom/Libre/LinX, ni le comportement réseau à l'exécution, ni une permission fabricant. `rea doctor` reste globalement unhealthy pour les moteurs optionnels absents, mais ses contrôles `node` et `jadx` sont OK et obligatoires. Aucun échantillon patient, aucune donnée clinique ni déploiement.

Suivi post-rapport : un commit documentaire ajoute la preuve à la branche et étend le filtre CI pour relancer REA sur l'exact HEAD final. La preuve initiale reste sur l'exact commit indiqué tant que le run suivant n'est pas observé. Révision indépendante/Release Certifier encore nécessaires avant MERGE ; W01 NO-GO, W02 gelé.