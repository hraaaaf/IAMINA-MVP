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
