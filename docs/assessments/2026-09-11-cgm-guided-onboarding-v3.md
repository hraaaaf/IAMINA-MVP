# CGM-GUIDE-V3 — Guided CGM onboarding

**Date:** 2026-09-11  
**Status:** ACTIVE

## Goal

Make CGM onboarding understandable to a non-technical patient without changing the certified CGM transport boundary. The product must expose a dedicated CGM page and explain, truthfully and concretely, how Dexcom, FreeStyle Libre and LinX/AiDEX X reach IAMINA through Nightscout.

## Success

1. `/cgm` is a dedicated authenticated IAMINA page, reachable from Importer.
2. Dexcom, Libre and LinX each expose a source-specific path with concrete upstream app/service steps rather than generic “prepare a bridge” language.
3. Dexcom guidance reflects the supported Nightscout Dexcom Share/Connect path; Libre guidance names Juggluco/xDrip-compatible paths; LinX keeps Juggluco -> Nightscout provenance.
4. A novice understands what Nightscout is, what IAMINA does not do, and what to do if no Nightscout site exists yet.
5. Configuration remains URL + bearer token/API secret only. No manufacturer credential is ever entered into IAMINA.
6. After configuration, the UI makes success/failure legible: connected + latest reading age, or clear troubleshooting when no reading arrives.
7. FR / EN / AR parity is preserved.
8. No backend provider, persistence, credential, clinical-authority or release-gate change.
9. Responsive evidence is retained at 390x844, 768x1024 and 1280x900 with no overflow/regression.

## BEFORE

Baseline UX:

- CGM lives inside `Importer > Connexions directes`, not on a dedicated page.
- Each card has `Mode d’emploi` and a three-step dialog.
- LinX names Juggluco explicitly.
- Dexcom and Libre only say to send readings to a Nightscout-compatible bridge, without telling a novice which path/app to use or how to proceed when Nightscout does not yet exist.
- The configuration cards expose `VIA NIGHTSCOUT`, `Mode d’emploi` and `Configurer`, but the first screen does not explain the end-to-end path.

Exact retained BEFORE visual evidence:

- workflow: `UI browser screenshot certification`;
- run: `34537140657` / #370 — **SUCCESS**;
- exact head: `22baebdeb57e11be9bea362197ac4c54629dfd5a`;
- artifact: `iamina-ui-browser-cert-multi-viewport`;
- artifact id: `10176176127`;
- digest: `sha256:c2aa3026df9b4d13485013c046993a27059bdf91df8d97a4ab50297ce815c906`;
- manually inspected: `importer-390x844.png`, `importer-768x1024.png`, `importer-1280x900.png`.

Observed BEFORE at all three viewports: document import dominates the page; CGM appears as three technical connection cards below `Connexions directes`; there is no dedicated CGM onboarding surface, no visible explanation for users without Nightscout, and no end-to-end sensor -> source app -> Nightscout -> IAMINA model.

Baseline UX score from audit: **6.8/10**.

## Reference / factual boundary

Current primary references checked on 2026-09-11:

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

[Dexcom G6/G7]   [Mode d’emploi]
Chemin conseillé: Dexcom app + Share -> Nightscout Connect -> IAMINA
[Configurer]

[FreeStyle Libre] [Mode d’emploi]
Chemin conseillé Android: Juggluco -> Nightscout -> IAMINA
Alternative compatible: xDrip / xDrip4iOS selon capteur/région.
[Configurer]

[LinX / AiDEX X] [Mode d’emploi]
Chemin: Juggluco -> Nightscout -> IAMINA
[Configurer]

[Je n’ai pas encore Nightscout]
Nightscout est un relais indépendant. Créez/ouvrez votre site via la documentation officielle,
puis revenez avec son URL HTTPS et un token/API secret dédié.

CONNECTED state:
[✓ Connexion active] Dernière mesure reçue il y a X min
[Synchroniser] [Aucune donnée ?] [Déconnecter]
```

## Candidate implementation

- branch: `feat/cgm-guided-onboarding-v3`;
- PR: #567;
- dedicated route: `/cgm`;
- Importer now exposes one guided CGM entry card instead of embedding the three configuration cards directly;
- dedicated page contains a plain-language journey model, source-specific expandable guides, Nightscout prerequisite help, the existing real configuration component, and ordered troubleshooting;
- existing per-source `Mode d’emploi` copy is also made concrete so the old generic wording cannot reappear inside the new page;
- dedicated browser certification workflow captures 390x844, 768x1024 and 1280x900.

No backend CGM provider, persistence, credential or clinical-authority code is changed.

## AFTER requirements

Before closeout this document must retain:

- exact final branch/head/PR;
- test results;
- 390x844 / 768x1024 / 1280x900 AFTER evidence;
- manual before/after comparison;
- final visual/UX score;
- any remaining external limitation.
