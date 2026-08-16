# CGM-GW-V2 — Product Wiring

## Goal

Make the already-certified Dexcom/Libre/LinX transport gateway usable by an authenticated IAMINA patient without widening clinical authority.

## Success

1. A patient can configure one qualified CGM bridge connection without plaintext credential storage.
2. IAMINA can sync normalized readings into patient-scoped, deduplicated CGM persistence.
3. Authenticated patient API exposes connection state, explicit sync and bounded reading history.
4. Flutter exposes a truthful connection/status/readings flow only after baseline capture + visual goal/mockup certification.
5. Synthetic E2E proves app/API/persistence wiring; a real provider account/sensor remains a separate external evidence gate.

## Safety / privacy ceiling

- CGM transport facts do not become diagnosis, urgency, prediction, prescription, dose or treatment authority.
- Manual `LogEntry` remains separate from continuous CGM transport persistence.
- Provider credentials are encrypted at rest with a dedicated `CGM_CREDENTIAL_KEY` and are never returned by patient APIs.
- Unknown providers, invalid connection configuration, missing encryption key and provider failures fail closed.
- No Vercel/deployment action is part of this LOT.

## Ordered execution

- V2-A — backend product wiring: connection model, encrypted credential boundary, deduplicated readings, authenticated API, explicit sync, migration/tests.
- V2-B — Flutter product wiring: baseline screenshot, written visual goal, mockup/reference, connection/status/readings UI, same-viewport after screenshots and scoring.
- V2-C — end-to-end certification: exact-head CI/drift/security/clinical review plus synthetic full-flow evidence.
- V2-D — real-device/provider proof: requires externally supplied valid Nightscout/Juggluco account/bridge and actual sensor data; cannot be claimed from repository tests.

## Current state

V2-A implementation is in progress on `agent/cgm-gateway-v2-product-wiring`. No completion credit is claimed yet.
