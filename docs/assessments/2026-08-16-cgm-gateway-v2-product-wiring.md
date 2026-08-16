# CGM-GW-V2 — Product Wiring

## Goal

Make the already-certified Dexcom/Libre/LinX transport gateway usable by an authenticated IAMINA patient without widening clinical authority.

## Success

1. A patient can configure one qualified CGM bridge connection without plaintext credential storage.
2. IAMINA can sync normalized readings into patient-scoped, deduplicated CGM persistence.
3. Authenticated patient API exposes connection state, explicit sync and bounded reading history.
4. Flutter exposes a truthful connection/status/readings flow only after baseline capture + visual goal/reference certification.
5. Synthetic E2E proves app/API/persistence wiring; a real provider account/sensor remains a separate external evidence gate.

## Safety / privacy ceiling

- CGM transport facts do not become diagnosis, urgency, prediction, prescription, dose or treatment authority.
- Manual `LogEntry` remains separate from continuous CGM transport persistence.
- Provider credentials are encrypted at rest with a dedicated `CGM_CREDENTIAL_KEY` and are never returned by patient APIs.
- Patient-configured bridge URLs require HTTPS, an explicit server-side `CGM_ALLOWED_BRIDGE_HOSTS` allowlist entry, and globally routable DNS results. Local/private/reserved/unapproved targets fail closed; the policy is rechecked at sync time.
- The remote provider call occurs outside the database row-lock transaction; the patient connection is re-locked and compared before any fetched reading is persisted, so a concurrent reconfiguration cannot commit stale-provider data.
- Unknown providers, invalid connection configuration, missing encryption key and provider failures fail closed.
- Nightscout raw API secrets are transformed into the protocol-required SHA-1 header value before encrypted persistence; raw API-secret plaintext is not retained. Bearer tokens are encrypted because they must remain reversible for upstream authentication.
- No Vercel/deployment action is part of this LOT.

## V2-B mandatory visual baseline — locked before implementation

Affected production surface: Flutter `ImportScreen`, mobile viewport 390×844.

Baseline evidence:
- certified Importer exact head `d392d208983c6c18fc86c75296c0f318f134ace0`;
- UI browser screenshot certification run #92: SUCCESS;
- artifact `iamina-ui-browser-cert-390x844`, id `9257168023`;
- artifact digest `sha256:fa49342a71c01e4985bcdc9d553b7c248322f3770587971c2ea6872274edd7cb`;
- inspected baseline file `importer-390x844.png`;
- canonical historical score: 9.5/10.

Baseline visual truth: Document Import is the primary acquisition card; beneath it, `Connexions directes` shows Dexcom G6/G7 and Abbott LibreLink as `BIENTÔT` / `Non disponible`. There is no LinX card.

### Written visual goal

Preserve the certified Importer hierarchy, spacing, card language, header rhythm and Document Import prominence while converting direct CGM cards into truthful product controls.

Acceptance criteria:
1. Document Import remains visually primary and in the same position.
2. Direct CGM cards use the existing `ClinicalCard` language; no new visual island.
3. Dexcom, Libre and LinX are shown as qualified **via Nightscout-compatible bridge**, never as direct manufacturer login claims.
4. Only one configured source may appear connected at a time, matching backend truth.
5. Disconnected state offers one clear `Configurer` action; connected state exposes factual source, last successful sync and explicit `Synchroniser` / `Déconnecter` actions.
6. Latest glucose display is factual only: value, unit, trend if supplied, timestamp, source. No red/green clinical interpretation, target assessment, urgency or treatment language.
7. Credential input is obscured; stored secret is never redisplayed.
8. Loading/error/empty states remain explicit and non-alarming. A saved connection remains visibly connected if its first or later sync fails.
9. 390×844 remains overflow-free and touch-safe; desktop retains responsive composition.
10. Final visual score must be evidence-backed from same-viewport before/mockup/after comparison.

### Pre-implementation reference / wireframe

The existing certified screenshot is the visual-style reference. The functional delta is constrained to the direct-connections block:

```text
[ DOCUMENT IMPORT — unchanged primary card ]

Connexions directes

┌ Dexcom G6/G7 ───────────── [VIA NIGHTSCOUT] ┐
│ Bridge compatible • aucune connexion         │
│                                  [Configurer] │
└──────────────────────────────────────────────┘

┌ FreeStyle Libre ────────── [VIA NIGHTSCOUT] ┐
│ Bridge compatible • aucune connexion         │
│                                  [Configurer] │
└──────────────────────────────────────────────┘

┌ LinX / AiDEX X ─────────── [VIA NIGHTSCOUT] ┐
│ Via Juggluco → Nightscout                    │
│                                  [Configurer] │
└──────────────────────────────────────────────┘

Connected variant for the single active source:
┌ Dexcom G6/G7 ───────────────── [CONNECTÉ] ┐
│ 123 mg/dL  →   il y a 5 min              │
│ Dernière synchro : …                      │
│          [Synchroniser]  [Déconnecter]    │
└───────────────────────────────────────────┘
```

Configuration modal/reference:

```text
Configurer Dexcom
Nightscout URL       [https://…]
Authentification     [Token | API secret]
Identifiant secret   [••••••••••]

IAMINA lit votre bridge Nightscout compatible ;
elle ne se connecte pas directement au capteur.

[Annuler]                         [Enregistrer]
```

This reference is intentionally evolutionary rather than a redesign: preserve a certified 9.5/10 acquisition page and change only the now-functional connector state.

## Ordered execution

- V2-A — backend product wiring: connection model, encrypted credential boundary, deduplicated readings, authenticated API, explicit sync, migration/tests.
- V2-B — Flutter product wiring: baseline screenshot, written visual goal/reference, connection/status/readings UI, same-viewport after screenshots and scoring.
- V2-C — end-to-end certification: exact-head CI/drift/security/clinical review plus synthetic full-flow evidence.
- V2-D — real-device/provider proof: requires externally supplied valid Nightscout/Juggluco account/bridge and actual sensor data; cannot be claimed from repository tests.

## Current state

V2-A and V2-B implementation are present on `agent/cgm-gateway-v2-product-wiring` / PR #285. Backend includes patient-scoped connection/readings persistence, encrypted credentials, public-HTTPS + server allowlist egress policy, explicit sync and authenticated API. Flutter replaces the obsolete unavailable Dexcom/Libre cards with truthful Dexcom/Libre/LinX Nightscout-bridge controls while preserving the certified Importer hierarchy. Focused backend/API/service/UI contract tests and an authenticated HTTP synthetic `configure → sync → persist → read → disconnect` test are present. Canonical OpenAPI has been regenerated. No completion credit is claimed until final exact-head CI, migration drift, visual screenshots, independent security/clinical review and release certification pass.
