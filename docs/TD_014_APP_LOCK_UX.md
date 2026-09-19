# TD-014 — Local app-lock UX proof contract

## Goal

Protect the already local-first IAMINA patient space with a strong device-local re-authentication step without reintroducing a remote runtime dependency.

## Success

A rendered patient flow shows, at the same `390×844`, `768×1024`, and `1280×900` viewports:

1. the retained P5-4A local enrollment reference;
2. a dedicated strong-lock setup screen;
3. a dedicated locked/re-authentication screen;
4. a fail-closed recovery screen with a verified-account recovery action;
5. no email/password/PIN fallback owned by IAMINA;
6. no patient-visible DEV/provider jargon;
7. no horizontal overflow or clipped primary CTA;
8. EN/FR/AR copy parity preserved by source contract tests.

## BEFORE reference

The exact-head P5-4A AUTH-LOCAL-FIRST candidate `f151702a2d80d2522e237b6c0e6d2bcad453e8d7` is the visual reference.

Retained proof before TD-014:

- auth-local-first visual workflow #18: SUCCESS;
- same viewports: `390×844`, `768×1024`, `1280×900`;
- local-enrollment screen uses the IAMINA logo, paper/teal backdrop, one centered clinical card, truthful offline copy, and one primary CTA;
- rendered predecessor visual review: 9.3/10.

## Written mockup / visual reference

TD-014 deliberately extends the existing local-enrollment language instead of introducing a new visual system.

### Setup state

`logo → SÉCURITÉ LOCALE pill → fingerprint/device-security icon → “Protéger IAmina” → offline truth row → device-authentication truth row → primary “Activer le verrou sécurisé” CTA`

### Locked state

`logo → fingerprint icon → “IAmina est verrouillée” → concise local verification explanation → primary “Déverrouiller IAmina” CTA`

### Recovery state

`logo → security-warning icon → “Récupération de sécurité requise” → explicit fail-closed explanation → primary “Se reconnecter pour récupérer” CTA before fresh remote verification → primary “Créer un nouveau verrou sécurisé” CTA only after fresh server-verified account authentication`

Recovery never opens clinical content directly: successful account verification only authorizes removal of unverifiable app-lock material, then strong WebAuthn/device-lock enrollment is required before the clinical space opens.

## Interaction reference

The browser/OS owns biometric or device-PIN collection through WebAuthn. IAMINA must never render a fake Face ID dialog, collect biometric material, or implement a weak app-specific PIN as a substitute for strong local user verification.

## AFTER proof

The TD-014 workflow must build BEFORE and AFTER independently, then capture:

- BEFORE local enrollment at the three canonical viewports;
- AFTER app-lock setup at the same three viewports;
- AFTER locked state at the same three viewports;
- AFTER recovery state at the same three viewports;
- horizontal overflow metrics for every AFTER capture;
- image digests proving distinct rendered states.

Final visual score is assigned only after inspecting the generated artifact. A green workflow status alone is not a visual review.


## Recovery amendment — 2026-09-19

Exact candidate: `a72a8d7f17f65ee980a09e6b82efe51e0a3d67aa`.

Verified CI: all six exact-head workflows succeeded, including TD-014 run `35430581283`.
Artifact: `10580592564`, digest `sha256:c15b570276a5e78a6d1327104255ce366f3abb74144b65bcf3705861f33693f9`.

Visual inspection of the recovery state passed at `390×844`, `768×1024`, and `1280×900`: primary CTA visible, no clipping, no horizontal overflow, no page errors, and distinct image digests at all three viewports. Retained visual score: **9.3/10**.

Browser security proof also passed: local public key, offline unlock, fail-closed user-verification check, fail-closed tampered-key check, and no application-network requirement for unlock. The browser proof records a locale-related console error; it did not invalidate the WebAuthn assertions and is retained here rather than silently omitted.
