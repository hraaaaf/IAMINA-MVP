# CGM-GW-V1.1 — LinX closeout evidence

## Scope

Provider expansion of the already-certified read-only CGM gateway to explicit LinX provenance through an external Juggluco-to-Nightscout bridge. No direct BLE/vendor implementation is embedded in IAMINA.

## Runtime closure evidence

- Runtime PR #281 exact head: `da7b2079908a22f4b143daf637a4ce6b2bec93b2`.
- Exact-head CI #2589: SUCCESS.
- Exact-head migration drift #2401: SUCCESS.
- Security/Privacy review: PASS.
- Clinical Safety review: PASS.
- Release Certifier: GO on the final diff.
- Expected-head squash merge: `8eaadc36ece7ed332897568f347f8d05f5ea7198`.
- `main` verified at the merge SHA.
- Post-merge migration drift #2402: SUCCESS.
- Post-merge CI #2590: SUCCESS.

## As-built provider path

`LinX/AiDEX X -> external Juggluco Android bridge -> Nightscout-compatible API -> backend/integrations/cgm -> CGMReading(source=linx)`

Juggluco remains external GPL-3.0 software. IAMINA does not copy, link, vendor or bundle Juggluco code or binaries. The upstream qualification was pinned to Juggluco commit `11d016eb3aeffe77e86d9522f5192e83790b5a21` from 2026-08-13.

## Safety / authority ceiling

V1.1 only extends explicit transport provenance. It adds no diagnosis, urgency classification, threshold, prediction, treatment recommendation, dose calculation, treatment optimization/change, persistence into patient clinical tables, patient-facing endpoint/UI or generative clinical authority.

## Medtronic decision

Medtronic remains HOLD. A modern CareLink path is not considered sufficiently canonical/stable for IAMINA to claim supported Medtronic ingestion in this LOT.

## Canonical closeout

- `docs/ROADMAP.md` records CGM-GW-V1.1 LinX as 100% / Closed without changing the 32/41 MENA critical-path numerator.
- `docs/architecture/ARCHITECTURE.md` extends the governed CGM boundary to Dexcom/Libre/LinX and records the external Juggluco bridge/license boundary.
- The documentation-only closeout must pass exact-head CI + migration drift, merge with expected-head locking, and pass post-merge checks before the closeout PR itself is considered complete.
