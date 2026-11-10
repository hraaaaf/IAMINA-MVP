# V1 #14 — Meal-photo uncertainty, consent and explicit confirmation

BEFORE and scope documented in GitHub issue #975. Existing MealCapturePanel requires manual photo picking, honors canUsePhotoRecognition, returns manual fallback and never updates meal selections until a person selects a proposed catalog item and presses Confirm. UI copy FR/EN/AR calls it a proposal for review.

Goal: with fake recognition and no network, prove permission denied never invokes recognition; low-confidence suggestions never add automatically; fallback leaves text search available. Three widget tests on real in-memory Drift.

Open privacy risk: AddLogSheet passes canUsePhotoRecognition based only on profile.aiConsentGivenAt non-null, while ConsentService.hasConsent requires current verified notice evidence as well. Server-side patient_ai_egress_scope is separate, but client affordance should be reconciled before patient activation. Confidence low has no separate badge; multilingual UX and nutritional reviewer must decide whether to mark or suppress these suggestions. No real patient images or AI egress were used in this test.

Product UI runtime unchanged, so no visual AFTER asserted. Future client change requires BEFORE/mockup/AFTER identical viewports and privacy signoff. PR DRAFT and no merge or Vercel absent express authorization; CGM decisions #1 and #25 last.
