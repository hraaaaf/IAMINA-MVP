# CGM-GUIDE-V3.1 — Desktop polish

**Date:** 2026-09-11  
**Status:** ACTIVE

## Goal

Polish the CGM onboarding desktop surface at 1280x900 so it reads as a desktop-first composition while preserving the already-certified CGM behavior, mobile/tablet information architecture and Nightscout safety boundary.

## Success

1. Header content aligns with the same 1080px desktop content grid as the body.
2. Desktop intro uses space intentionally instead of stacking full-width bands.
3. The sensor guide and IAMINA connection actions remain immediately legible.
4. Mobile 390x844 and tablet 768x1024 preserve their current information order and do not overflow.
5. No CGM backend/service/persistence/credential/clinical-authority change.
6. Real Chrome AFTER evidence exists at 390x844, 768x1024 and 1280x900.

## BEFORE

Retained evidence from post-merge CGM browser certification:

- workflow: `CGM onboarding browser certification`;
- run: `34629126787` / #8 — **SUCCESS**;
- head: `aa753f06a9b06a3ebe369169f17f0bf0f9c8083c`;
- artifact: `iamina-cgm-guided-onboarding-browser-cert`;
- artifact id: `10275348927`;
- digest: `sha256:12890145eea4ebc5ad5ef75281006a978a359098a289678bc39de585391c10a1`;
- inspected desktop capture: `cgm-guide-1280x900.png`.

Observed desktop polish defects:

- route header starts near the viewport edge while the body starts on the centered content grid;
- journey, Nightscout help and the next section stack as separate full-width horizontal bands, wasting desktop width;
- the visual rhythm is clean but still resembles a mobile/tablet composition expanded to desktop.

Desktop baseline polish score: **8.8/10**. Functional/clinical score remains unchanged from CGM-GUIDE-V3.

## Locked desktop mockup

For width >= 900px:

```text
[Header aligned to centered 1080 content grid]

[ Journey / data path  ~2/3 width ][ Nightscout help ~1/3 width ]

[ Choose sensor ]
[ Dexcom ][ Libre ][ LinX ]

[ Connect IAMINA + intro ]
[ Dexcom ][ Libre ][ LinX ]

[ Troubleshooting ]
```

For width < 900px: retain the current vertical composition.

## Constraints

- presentation-only changes in the CGM screen unless a test contract needs alignment;
- do not change source-specific clinical/product copy;
- do not weaken existing tests;
- no Vercel deployment.
