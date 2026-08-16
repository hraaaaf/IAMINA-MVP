# CGM-GW-V1.1 — LinX provider qualification

## Goal

Extend the existing read-only CGM gateway with explicit LinX provenance without embedding third-party BLE/vendor code in IAMINA and without increasing clinical authority.

## Qualified path

`LinX/AiDEX X sensor -> external Juggluco Android bridge -> Nightscout-compatible API -> backend/integrations/cgm -> CGMReading(source=linx)`

Juggluco is kept fully outside IAMINA. Its repository explicitly lists LinX/AiDEX X sensor support, Nightscout upload capability, GPL-3.0 licensing, and active repository pushes in August 2026. IAMINA consumes only the already-governed Nightscout HTTP boundary.

Evidence:

- https://github.com/j-kaltes/Juggluco
- https://www.juggluco.nl/
- https://www.microtechmd.com/support/download/664/666

## Runtime authority ceiling

This LOT changes source provenance only. It adds no diagnosis, urgency classification, threshold, prediction, treatment recommendation, dose calculation, treatment optimization/change, persistence into patient clinical tables, patient-facing endpoint/UI, or generative clinical authority.

The upstream bridge is not trusted to identify source provenance from arbitrary device text. LinX provenance is configured explicitly in IAMINA exactly as Dexcom/Libre provenance is configured in V1.

## Security / licensing boundary

- No Juggluco GPL source or binary is copied, linked, bundled, or vendored into IAMINA.
- BLE/vendor credentials remain in the external bridge/device environment.
- IAMINA retains HTTPS-only remote transport, exact loopback HTTP exception, no URL-embedded credentials, single Nightscout authentication mechanism, timezone-aware cursor, malformed-payload rejection, and collapsed provider errors.

## Medtronic decision

Medtronic remains HOLD for this LOT. The Nightscout CareLink path is publicly documented, but current open-source CareLink implementations remain fragile/experimental and modern authentication support is not sufficiently canonical for IAMINA to claim a working Medtronic provider. No Medtronic runtime provenance is added in V1.1.

## Acceptance gates

- [x] Add explicit `CGMSource.LINX` provenance.
- [x] Allow LinX only through the existing Nightscout-compatible provider boundary.
- [x] Add regression coverage proving LinX source is configured rather than inferred from bridge/device text.
- [x] Keep unknown/unqualified providers fail-closed.
- [ ] Synchronize canonical roadmap with CGM-GW-V1.1.
- [ ] Pass exact-head CI, security/privacy review, clinical-safety review and migration drift.
- [ ] Merge with expected-head locking and verify post-merge CI/drift before closure.

## Non-scope

Direct BLE in IAMINA, reverse-engineering LinX protocol inside IAMINA, MicroTech credential storage, patient UI, background sync, Medtronic, treatment logic, and any automated interpretation of CGM readings.
