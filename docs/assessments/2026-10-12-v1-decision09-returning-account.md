# V1 #9 — Existing patient onboarding non-repetition proof

**BEFORE code verified**: router shouldApplyOnboardingGate checks authenticated, non-anonymous, not hosted-remote-required, initialized and incomplete patient profile. ConsentService.hasCompletedOnboarding requires non-empty local diabetes type and treatment. main.dart seeds the local saved profile synchronously and subscribes to watchProfile, so restarting should not repeat first-use for a complete record.

**Goal**: cover returning vs incomplete local profile, anonymous/hosted/uninitialized guards and the separation of onboarding completion from AI consent, on real in-memory Drift synthetic data. A mere login or unverifiable remote account profile is not evidence of completed patient onboarding, and must not bypass missing medical profile/consent.

**Scope**: three test cases, no application runtime/UX change, no patient, cloud or provider calls. The profile identity hardening #7 and authenticated remote-profile hydration remain distinct gates. CI exact SHA required. Do not merge or deploy without express permission; CGM #1 and #25 last.
