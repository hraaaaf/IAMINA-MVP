# D5 IP country proposal + searchable country selection — UI gate

**BEFORE real Chrome**: [3 viewports / old controls](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38376886271/artifacts/11801363479): selected language followed by 3 chips Maroc/France/Autre.

**Approved new Goal from user (13 Oct 2026)**: remove the 3 predefined country choices; instead display one localized country search field offering suggestions, optionally prefilled from visitor IP. It must remain editable and save only when the onboarding is finished.

**Mockup target prior to AFTER capture**: same layout and progress 5/5; replace the three chips with a full-width search field (magnifying glass, country name typed or selected from suggestions); below, a 12px subdued disclosure: “Proposé selon votre connexion Internet. Vérifiez ou modifiez le pays.” on successful IP guess, otherwise “Choisissez votre pays d’utilisation. La localisation IP est indicative.” Keep FR/EN/AR/RTL, settings/preferences route.

**Security/privacy**: existing IAMINA API only, public GET /api/v1/country/suggestion reads Vercel-supplied coarse geo header *only on Vercel*; emits ISO alpha-2 or null, raw IP never returned/stored, no third-party service, no clinical/regulatory logic driven by estimated IP. Null fallback is blank/manual. Catalog 249 ISO countries and territories, no “Other”. Existing selected country in preferences remains manually editable. Do not infer unit or timezone.

**Validation due before merge**: backend unit tests, Flutter tests/analyzer/PWA, actual Chrome AFTER captures 390×844, 768×1024, 1280×900 and comparison to BEFORE; positive suggestion needs Vercel-only validation (no Vercel deployment permitted without approval), manual fallback must work offline, locale/RTL and existing-account paths; approval of AFTER visual by owner. [D5 issue #983](https://github.com/hraaaaf/IAMINA-MVP/issues/983).
