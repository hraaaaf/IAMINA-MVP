# IAMINA V1 #7 — Safeguard patient owner when editing medical profile

**BEFORE verified in issue #962**: PatientProfiles.userId is primary key. Onboarding uses Firebase UID hash or offline 1, while ProfileScreen._saveProfile previously wrote a hardcoded userId=1. The profile edits UI exists but this can produce two local rows instead of updating the existing row. This is a code-level risk, not a proven real patient data leak.

**Goal**: preserve existing local primary key, reject multiple local profiles and mismatched signed-in identity before any write, use offline 1 only on fresh local-first DB, and change no medical calculation, treatment or consent. A pure identity guard and real in-memory Drift tests cover those cases. ProfileScreen load refuses ambiguous two-row state, save displays a localized failure without mutation.

**Caveat**: the local database and AppDatabase.watchProfile() across multi-account sessions are not certified by this patch. Existing old duplicate data may still need a patient-safe remediation policy. UI snackbar error-path needs a targeted accessibility/visual review. No server sync, CGM or AI. Keep PR DRAFT and do not merge/deploy without independent security/privacy approval and exact-head CI.
