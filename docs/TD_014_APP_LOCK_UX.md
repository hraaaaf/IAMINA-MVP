# TD-014 — Local app-lock UX proof contract

## Goal

Protect the already local-first IAMINA patient space with a strong device-local re-authentication step without reintroducing a remote runtime dependency.

## Success

A rendered patient flow shows, at the same `390×844`, `768×1024`, and `1280×900` viewports:

1. the retained P5-4A local enrollment reference;
2. a dedicated strong-lock setup screen;
3. a dedicated locked/re-authentication screen;
4. no email/password/PIN fallback owned by IAMINA;
5. no patient-visible DEV/provider jargon;
6. no horizontal overflow or clipped primary CTA;
7. EN/FR/AR copy parity preserved by source contract tests.

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

`logo → security-warning icon → “Récupération de sécurité requise” → explicit fail-closed explanation → no bypass CTA`

## Interaction reference

The browser/OS owns biometric or device-PIN collection through WebAuthn. IAMINA must never render a fake Face ID dialog, collect biometric material, or implement a weak app-specific PIN as a substitute for strong local user verification.

## AFTER proof

The TD-014 workflow must build BEFORE and AFTER independently, then capture:

- BEFORE local enrollment at the three canonical viewports;
- AFTER app-lock setup at the same three viewports;
- AFTER locked state at the same three viewports;
- horizontal overflow metrics for every AFTER capture;
- image digests proving distinct rendered states.

Final visual score is assigned only after inspecting the generated artifact. A green workflow status alone is not a visual review.
