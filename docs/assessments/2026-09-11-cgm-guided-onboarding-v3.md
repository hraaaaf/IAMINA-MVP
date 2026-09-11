# CGM-GUIDE-V3 — Guided CGM onboarding

**Date:** 2026-09-11  
**Status:** ENGINEERING_CLOSED / READY_TO_MERGE

## Goal

Make CGM onboarding understandable to a non-technical patient without changing the certified CGM transport boundary. The product must expose a dedicated CGM page and explain, truthfully and concretely, how Dexcom, FreeStyle Libre and LinX/AiDEX X reach IAMINA through Nightscout.

## Success

1. `/cgm` is a dedicated authenticated IAMINA page, reachable from Importer.
2. Dexcom, Libre and LinX each expose a source-specific path with concrete upstream app/service steps rather than generic bridge language.
3. Dexcom guidance reflects the supported Nightscout Dexcom Share/Connect path; Libre guidance names Juggluco/xDrip-compatible paths; LinX keeps Juggluco -> Nightscout provenance.
4. A novice understands what Nightscout is, what IAMINA does not do, and what to do if no Nightscout site exists yet.
5. Configuration remains URL + bearer token/API secret only. No manufacturer credential is ever entered into IAMINA.
6. After configuration, the UI makes success/failure legible: connected + latest reading age, or clear troubleshooting when no reading arrives.
7. FR / EN / AR parity is preserved.
8. No backend provider, persistence, credential, clinical-authority or release-gate change.
9. Responsive evidence is retained at 390x844, 768x1024 and 1280x900 with no overflow/regression.

## BEFORE

Baseline UX:

- CGM lived inside `Importer > Connexions directes`, not on a dedicated page.
- Each card had `Mode d’emploi` and a three-step dialog.
- LinX named Juggluco explicitly.
- Dexcom and Libre only said to send readings to a Nightscout-compatible bridge, without telling a novice which path/app to use or how to proceed when Nightscout did not yet exist.
- The configuration cards exposed `VIA NIGHTSCOUT`, `Mode d’emploi` and `Configurer`, but the first screen did not explain the end-to-end path.

Exact retained BEFORE visual evidence:

- workflow: `UI browser screenshot certification`;
- run: `34537140657` / #370 — **SUCCESS**;
- exact head: `22baebdeb57e11be9bea362197ac4c54629dfd5a`;
- artifact: `iamina-ui-browser-cert-multi-viewport`;
- artifact id: `10176176127`;
- digest: `sha256:c2aa3026df9b4d13485013c046993a27059bdf91df8d97a4ab50297ce815c906`;
- manually inspected: `importer-390x844.png`, `importer-768x1024.png`, `importer-1280x900.png`.

Observed BEFORE at all three viewports: document import dominated the page; CGM appeared as three technical connection cards below `Connexions directes`; there was no dedicated CGM onboarding surface, no visible explanation for users without Nightscout, and no end-to-end sensor -> source app -> Nightscout -> IAMINA model.

Baseline UX score from audit: **6.8/10**.

## Reference / factual boundary

Primary references checked on 2026-09-11:

- Nightscout Supported Uploaders: Dexcom can use Dexcom Share/Connect; xDrip/xDrip4iOS are alternatives. Libre 2/2+/3/3+ can use Juggluco and, depending on sensor/region, xDrip/xDrip4iOS.
- Nightscout Setup Uploaders: secure HTTPS Nightscout URL; Dexcom Share requires sharing/follower configuration; Nightscout remains the independent relay.
- Juggluco Uploader help: Nightscout upload is explicitly configured with URL + API secret/access token.

No claim is made that IAMINA logs in directly to Dexcom, Abbott or MicroTech.

## Locked mockup

```text
[Header] Connecter mon CGM
Vos mesures restent lues via un relais Nightscout sécurisé.

[Comprendre le parcours]
Capteur -> app/service source -> Nightscout -> IAMINA
IAMINA ne demande jamais le mot de passe du fabricant.

[Dexcom G6/G7]
Dexcom app + Share -> Nightscout Connect -> IAMINA

[FreeStyle Libre]
Juggluco / compatible xDrip -> Nightscout -> IAMINA

[LinX / AiDEX X]
Juggluco -> Nightscout -> IAMINA

[Je n’ai pas encore Nightscout]
Documentation officielle Nightscout -> HTTPS URL + dedicated token/API secret.

[Connecter IAMINA]
Configurer -> Synchroniser -> latest reading / last sync
```

## Implementation delivered

- branch: `feat/cgm-guided-onboarding-v3`;
- PR: #567;
- certified code head: `a2993f7234d49281dffee5fc1181f9662e376e1a`;
- dedicated route: `/cgm`;
- Importer exposes one guided CGM entry card instead of embedding the three configuration cards directly;
- dedicated page contains a plain-language journey model, source-specific expandable guides, Nightscout prerequisite help, the existing real configuration component, and ordered troubleshooting;
- existing per-source `Mode d’emploi` copy was made concrete so the old generic wording cannot reappear inside the new page;
- RTL contract includes `/cgm`; physical paddings on the new page were converted to directional paddings;
- stale regression contracts were migrated to the dedicated `/cgm` architecture rather than weakened or deleted.

No backend CGM provider, persistence, credential or clinical-authority code changed.

## Validation

Exact certified code head: `a2993f7234d49281dffee5fc1181f9662e376e1a`.

Machine gates on that head:

- CI #3932 / run `34627297198` — **SUCCESS**;
  - secret hygiene — SUCCESS;
  - PR scope — SUCCESS;
  - Flutter analyze — SUCCESS;
  - Flutter tests — SUCCESS;
  - self-contained PWA release build — SUCCESS;
  - PWA build verification — SUCCESS.
- P5-5 End-to-End Pilot Rehearsal #25 / run `34627297499` — **SUCCESS**.
- UI geometry golden #385 / run `34627297138` — **SUCCESS**.
- CGM onboarding browser certification #6 / run `34627297406` — **SUCCESS**.
- UI browser screenshot certification #387 / run `34627297385` — **SUCCESS**.
- Companion real chat screenshots #43 — **SUCCESS**.
- P7 responsive Dashboard certification #62 — **SUCCESS**.

## AFTER visual evidence

Dedicated CGM evidence:

- workflow: `CGM onboarding browser certification`;
- run: `34627297406` / #6 — **SUCCESS**;
- exact head: `a2993f7234d49281dffee5fc1181f9662e376e1a`;
- artifact: `iamina-cgm-guided-onboarding-browser-cert`;
- artifact id: `10275575150`;
- digest: `sha256:326e808c5324a703564379d4f02c46131b5d80597ee6c3c5e77acc50726b9fc5`;
- retained captures: `cgm-guide-390x844.png`, `cgm-guide-768x1024.png`, `cgm-guide-1280x900.png`.

Global Importer evidence:

- workflow: `UI browser screenshot certification`;
- run: `34627297385` / #387 — **SUCCESS**;
- exact head: `a2993f7234d49281dffee5fc1181f9662e376e1a`;
- artifact: `iamina-ui-browser-cert-multi-viewport`;
- artifact id: `10275546415`;
- digest: `sha256:75601a93820de1030da9c730e0c18e0a81f0bd2773e4b81914e48640892c4190`;
- retained Importer captures: `importer-390x844.png`, `importer-768x1024.png`, `importer-1280x900.png`.

Manual inspection at 390x844, 768x1024 and 1280x900 found no visible overflow or clipping. Mobile keeps the end-to-end path and `Je n’ai pas encore Nightscout` before the actual configuration surface. Desktop uses the available width for the three source-guide columns. The global Importer screenshots confirm the entry point `Capteur CGM -> Ouvrir le guide CGM`.

## BEFORE / AFTER comparison

BEFORE required a user to understand `VIA NIGHTSCOUT` before the product explained what Nightscout was or how each manufacturer path reached it. AFTER changes the information order to:

`Capteur -> source app/service -> Nightscout -> IAMINA -> configuration -> troubleshooting`.

This removes the principal novice-comprehension defect while preserving the already-qualified Nightscout transport boundary and existing governed CGM actions.

Final model UX/UI score after same-viewport manual review: **9.2/10**.

## Remaining boundary

- No physical LinX sensor is currently available for live-device proof.
- Therefore this closeout certifies the engineering/onboarding UX and retained synthetic/browser evidence only; it does **not** claim physical LinX device validation.
- No Vercel deployment was performed or authorized as part of this lot.

## Roadmap coherence

This is a CGM product-UX hardening lot, not a new P5 closure and not a new MENA critical-path task. Canonical arithmetic therefore remains unchanged and was verified before merge:

- Pilot Readiness: **3/9 = 33.3%**;
- MENA retained critical path: **32/38 ≈ 84.2%**.

## Closeout decision

**ENGINEERING_CLOSED / READY_TO_MERGE.**

Goal met with retained evidence: dedicated guided CGM onboarding exists, source paths are explicit, real configuration remains governed, FR/EN/AR contracts pass, RTL is registered, the global Importer entry is visible, and the dedicated CGM surface scores **9.2/10** after same-viewport visual review.
