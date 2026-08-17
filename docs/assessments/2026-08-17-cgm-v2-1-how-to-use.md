# CGM-GW-V2.1 — Premium “How to use”

## Goal
Add a premium, source-specific “How to use” action to each Dexcom, FreeStyle Libre and LinX/AiDEX X card without changing CGM transport authority or breaking the certified Importer layout.

## Baseline
- Current certified Importer 390×844 baseline is the CGM-GW-V2 Chrome artifact from runtime merge `8231be716e028b8e9cf2141fb49d3d3f77388549`.
- Artifact: `iamina-ui-browser-cert-390x844`, digest `sha256:5233930d8fb7729892a93c269871abf7b890b73ce9c6603035ff6851e27c1932`.
- Subsequent CGM V2 closeout commits are documentation-only, therefore baseline UI remains valid for main `1396909c812c9bc857b0ad5ec2c40daaf222b4cc`.

## Success criteria
1. Every CGM card has a visible, keyboard-accessible “How to use” action next to its identity/status region.
2. Action opens a bounded premium dialog with exactly three numbered steps, source-specific bridge guidance, a truthful Nightscout disclosure, and a primary “Configure” action.
3. Dexcom/Libre wording never claims a direct manufacturer login; LinX explicitly retains Juggluco → Nightscout provenance.
4. FR/EN/AR copy parity.
5. No CGM backend, persistence, credential or clinical-authority change.
6. No horizontal overflow at 390×844 and no regression at wider certified viewports.
7. Same-page Chrome after capture, visual comparison and score ≥9.0/10 before merge.

## Locked wireframe

```text
[CGM icon]  Dexcom G6/G7               [HOW TO USE] [VIA NIGHTSCOUT]
            Compatible through a Nightscout bridge.

Tap HOW TO USE →
┌─────────────────────────────────────────────┐
│ Connect Dexcom G6/G7                    [×] │
│                                             │
│  1  Prepare your bridge                    │
│     Send this CGM to a compatible           │
│     Nightscout bridge you control.          │
│                                             │
│  2  Get access                             │
│     Copy the HTTPS Nightscout URL and       │
│     bearer token / API secret.              │
│                                             │
│  3  Connect IAMINA                         │
│     Configure, save, then run Sync.          │
│                                             │
│  IAMINA reads Nightscout; it does not       │
│  sign in directly to the manufacturer.      │
│                           [Configure]        │
└─────────────────────────────────────────────┘
```

Same component and visual hierarchy for Libre and LinX; only source-specific step 1 / disclosure copy changes.

## Evidence ceiling
This feature explains the already-certified CGM bridge setup. It does not prove a live physical sensor path and must not imply that a vendor account or sensor has been tested.

## Certification trigger
A direct repository commit is intentionally used after the self-cleaning helper commit so GitHub Actions can materialize fresh exact-head jobs; this does not change runtime or visual behavior.

## Final certification / closeout
- Runtime PR: #294, squash merge `d6318790be505b80e21e1c7810c56d373ae64a49`.
- Exact-head gates: CI #2684 SUCCESS; migration drift #2496 SUCCESS; UI screenshot audit #289 SUCCESS; Chrome browser certification #254 SUCCESS.
- Post-merge evidence: CI #2685 SUCCESS; Chrome browser certification #255 SUCCESS.
- Final 390×844 dialog visual score: **9.6/10**. Three steps, safety disclosure and Configure CTA are fully visible without initial scrolling or overflow.
- Clinical authority: unchanged. No diagnosis, urgency, prediction, dose, prescription or treatment-change behavior was added.
- Security/privacy: unchanged. No backend, persistence, credential-storage or authentication boundary changed.
- Product truth: Dexcom/Libre do not claim direct manufacturer login; LinX retains Juggluco → Nightscout provenance.
- Live physical-sensor/provider proof remains a separate external gate and is not claimed by this closeout.
- Status: **CGM-GW-V2.1 CLOSED** after runtime merge and post-merge certification.
