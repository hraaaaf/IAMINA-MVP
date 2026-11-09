# V1 #5 — No implicit country selection before an explicit onboarding choice

**BEFORE inspected on main**: `OnboardingChatScreen` already presents Morocco/France/Other in FR/EN/AR and makes the final `_finish` require `_country != null`. However `_selectLanguage` uses `setExperience(language:value,country:_country ?? 'MA',tone:_tone ?? 'neutral')`, which writes `iamina.country=MA` before the person chooses a country. `LocalePreferenceService` already supports secure local country storage but silently receives that fallback. See [issue #955](https://github.com/hraaaaf/IAMINA-MVP/issues/955), written before patch.

**Goal:** language switches immediately on selection but **never** persists a country that wasn't chosen. Mockup/visual reference = **identical existing onboarding steps, no visual/layout changes**; the only change is stored state and its effect on interrupted onboarding. Keep selected country/tone until intentional `_finish`, no automatic unit rules (#8), no timezone inference or medical changes.

**AFTER candidate:** `LocalePreferenceService.setLanguageOnly` validates + persists ONLY UI language/explicit flag; `_selectLanguage` calls it; `_finish` retains `setExperience` with explicit `_country!`. Tests use mocked secure-storage API to prove first-language selection doesn't write country/tone, correct FR persists on completion, later language switches don't overwrite country, unsupported language fails closed. Static caller contract test checks no hidden 'MA' fallback.

**Proof still required:** new-HEAD Flutter full suite/CI, locale preference and onboarding contracts, mobile FR/EN/AR first-use regression. No clinical policy or new UI pixel claim. Do not merge or deploy without explicit approval; original CGM #1/#25 remain last.
