# CGM-GUIDE-V3 — Guided CGM onboarding

**Date:** 2026-09-11  
**Status:** CLOSED

## Goal

Make CGM onboarding understandable to a non-technical patient without changing the certified CGM transport boundary. The product must expose a dedicated CGM page and explain, truthfully and concretely, how Dexcom, FreeStyle Libre and LinX/AiDEX X reach IAMINA through Nightscout.

## Success criteria

1. `/cgm` is a dedicated authenticated IAMINA page, reachable from Importer.
2. Dexcom, Libre and LinX expose source-specific setup paths.
3. Nightscout is explained before configuration.
4. Users without Nightscout get a concrete next step.
5. IAMINA only asks for Nightscout URL + token/API secret, never manufacturer credentials.
6. Configuration and troubleshooting remain governed by the existing CGM connector.
7. FR / EN / AR parity is preserved.
8. RTL is covered.
9. 390x844, 768x1024 and 1280x900 are retained without visible overflow/regression.

## Certified transport boundary

- Dexcom: supported Nightscout Share/Connect path; xDrip/xDrip4iOS remain upstream alternatives where applicable.
- FreeStyle Libre: Juggluco and compatible xDrip/xDrip4iOS paths depending on sensor/region.
- LinX / AiDEX X: Juggluco -> Nightscout -> IAMINA.
- IAMINA does not log in directly to Dexcom, Abbott or MicroTech.
- No backend CGM provider, persistence, credential or clinical-authority code changed in this lot.

## Implementation delivered

- dedicated `/cgm` page;
- Importer now exposes one guided CGM entry instead of embedding the three configuration cards directly;
- end-to-end mental model: `Capteur -> app/service source -> Nightscout -> IAMINA`;
- explicit manufacturer-specific guidance;
- `Je n’ai pas encore Nightscout` help;
- existing governed configure/sync/disconnect actions reused;
- ordered troubleshooting;
- FR / EN / AR guidance;
- `/cgm` registered in RTL contracts and directional paddings used;
- stale regression contracts migrated to the dedicated-page architecture rather than weakened.

## BEFORE evidence

Baseline UX score: **6.8/10**.

- workflow: `UI browser screenshot certification`;
- run: `34537140657` / #370 — **SUCCESS**;
- head: `22baebdeb57e11be9bea362197ac4c54629dfd5a`;
- artifact: `iamina-ui-browser-cert-multi-viewport`;
- artifact id: `10176176127`;
- digest: `sha256:c2aa3026df9b4d13485013c046993a27059bdf91df8d97a4ab50297ce815c906`;
- retained viewports: 390x844, 768x1024, 1280x900.

Observed BEFORE: CGM lived inside Importer as technical Nightscout connection cards, with no dedicated onboarding, no visible no-Nightscout path, and no sensor -> source app -> Nightscout -> IAMINA explanation.

## Certified code head

`a2993f7234d49281dffee5fc1181f9662e376e1a`

Pre-merge validation on that exact code head:

- CI #3932 / `34627297198` — **SUCCESS**;
- P5-5 #25 / `34627297499` — **SUCCESS**;
- UI geometry golden #385 / `34627297138` — **SUCCESS**;
- CGM onboarding browser #6 / `34627297406` — **SUCCESS**;
- UI browser screenshot #387 / `34627297385` — **SUCCESS**;
- Companion real chat #43 — **SUCCESS**;
- P7 responsive Dashboard #62 — **SUCCESS**.

## AFTER visual evidence

Dedicated CGM surface:

- run: `34627297406` / #6 — **SUCCESS**;
- head: `a2993f7234d49281dffee5fc1181f9662e376e1a`;
- artifact: `iamina-cgm-guided-onboarding-browser-cert`;
- artifact id: `10275575150`;
- digest: `sha256:326e808c5324a703564379d4f02c46131b5d80597ee6c3c5e77acc50726b9fc5`;
- retained captures: `cgm-guide-390x844.png`, `cgm-guide-768x1024.png`, `cgm-guide-1280x900.png`.

Global Importer entry:

- run: `34627297385` / #387 — **SUCCESS**;
- artifact: `iamina-ui-browser-cert-multi-viewport`;
- artifact id: `10275546415`;
- digest: `sha256:75601a93820de1030da9c730e0c18e0a81f0bd2773e4b81914e48640892c4190`;
- retained Importer captures: 390x844, 768x1024, 1280x900.

Manual same-viewport review found no visible overflow or clipping. The new information order is:

`Capteur -> source app/service -> Nightscout -> IAMINA -> configuration -> troubleshooting`.

Final UX/UI score: **9.2/10**.

## Merge

- PR: **#567** — merged;
- merge commit: `aa753f06a9b06a3ebe369169f17f0bf0f9c8083c`;
- target: `main`.

## Post-merge validation

All six retained push workflows on `main@aa753f06a9b06a3ebe369169f17f0bf0f9c8083c` completed successfully:

- P5-5 End-to-End Pilot Rehearsal #28 / `34629126665` — **SUCCESS**;
- CGM onboarding browser certification #8 / `34629126787` — **SUCCESS**;
- UI geometry golden audit #390 / `34629126628` — **SUCCESS**;
- Dashboard global certification v2 #22 / `34629126597` — **SUCCESS**;
- CI #3940 / `34629126574` — **SUCCESS**;
- UI browser screenshot certification #392 / `34629126600` — **SUCCESS**.

Post-merge result: **6/6 SUCCESS, 0 failed, 0 pending**.

## Remaining boundary

- No physical LinX sensor is available for live-device proof.
- This closeout certifies engineering/onboarding UX and retained synthetic/browser evidence only; it does **not** claim physical LinX device validation.
- No Vercel deployment was performed or authorized for this lot.

## Roadmap coherence

This CGM UX hardening lot does not create a new P5 closure or a new MENA critical-path task. Arithmetic remains unchanged:

- Pilot Readiness: **3/9 = 33.3%**;
- MENA retained critical path: **32/38 ≈ 84.2%**.

## Closeout decision

**CLOSED.**

Goal met with retained evidence. PR #567 is merged, all six post-merge workflows are green, the dedicated guided CGM surface scores **9.2/10**, and no known engineering action remains in CGM-GUIDE-V3.