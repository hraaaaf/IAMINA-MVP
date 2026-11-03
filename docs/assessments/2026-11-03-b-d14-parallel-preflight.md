# IAMINA B / D14 — Préflight consentement photo 2026-11-03

Base: main@6adf3fbeecb0f6645f9c7a9e3934177ef9eca6c7. No clinical/patient activation.

Verified code finding: AddLogSheet passed `profile.aiConsentGivenAt != null` to the photo recognizer, which accepts legacy/unverified timestamps despite existing ConsentService requiring verified evidence. Candidate changes this to the current opt-in state from an optional ConsentService Provider (missing provider = denied); revocation also invalidates in-flight recognition results and already-shown proposals.

Three new synthetic Flutter widget cases: consent absent -> zero recognition invocations, revocation during pending request -> zero proposals, revocation after result -> proposal cleared. Other existing human-confirmation UI is unchanged. Backend D24 consent/media egress is still authoritative. No new image provider or automatic meal write.

Static source assertions passed; **Flutter analyze, unit/widget tests, real Chrome QA and BEFORE/AFTER were not run** in this environment. This is a separate **unreferenced Git commit** because a GitHub branch ref push could automatically deploy the connected Vercel projects without explicit deployment permission. Never merge without CI, UX evidence, D24 and privacy gates.

Next: compile widget tests, inspect real Web FR/AR/RTL at 390/768/1280, verify UI before/after and scores, then D24 integration gate and review.
