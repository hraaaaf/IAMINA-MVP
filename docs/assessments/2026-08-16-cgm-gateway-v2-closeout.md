# CGM-GW-V2 — Product Wiring closeout

## Goal

Close CGM-GW-V2 only after the patient-facing Dexcom/Libre/LinX Nightscout product wiring is merged to `main`, exact-head and post-merge gates are green, and canonical tracker state matches the verified implementation.

## Verified runtime evidence

- Runtime PR: #285.
- Final recertified PR head: `bb4eb2736c618a526ead9a84bd56e73d952c7b64`.
- Exact-head CI #2652: SUCCESS.
- Exact-head migration drift #2464: SUCCESS.
- Exact-head UI screenshot audit #265: SUCCESS.
- Exact-head UI browser screenshot certification #230: SUCCESS.
- Security/Privacy review record: PASS at the recertified head; patient-configured bridge URLs remain HTTPS + server allowlist + globally routable DNS fail-closed, credentials remain encrypted and never returned to the patient API.
- Clinical Safety review record: PASS; CGM remains transport/factual data only with no diagnosis, urgency, prediction, dose, prescription or treatment authority.
- Visual after evidence: Importer 390×844, overflow-free, score 9.4/10 against the locked baseline/reference.
- Runtime squash merge: `8231be716e028b8e9cf2141fb49d3d3f77388549`.
- Runtime post-merge CI #2653: SUCCESS.
- Runtime post-merge migration drift #2465: SUCCESS.
- Runtime post-merge UI screenshot audit #266: SUCCESS.
- Runtime post-merge UI browser screenshot certification #231: SUCCESS.

## Product result

IAMINA now contains authenticated patient-facing CGM product wiring for the qualified Nightscout-compatible boundary:

`Dexcom / Libre / LinX -> qualified external bridge -> Nightscout-compatible API -> IAMINA sync -> patient-scoped deduplicated CGM persistence -> authenticated patient API -> Flutter Importer connection/status/readings controls`

The app stores CGM readings separately from manual `LogEntry`, obscures credentials, preserves a saved connection when a sync fails, and exposes only factual reading transport fields.

## Evidence ceiling

Repository certification proves the synthetic app/API/persistence path. It does **not** prove a real Dexcom, Libre or LinX sensor path until a real allowlisted Nightscout/Juggluco bridge with actual sensor data is exercised. That live-provider/device proof remains a separate external gate and is not silently inferred from CI.

## Closeout state

Runtime engineering/product wiring is certified and merged. CGM-GW-V2 may be marked **100% / Closed** as a repository product-wiring lane, while real-device/provider proof remains explicitly outside that percentage and must be tracked separately before claiming live sensor interoperability.
