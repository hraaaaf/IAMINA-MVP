# IAMINA D2 Web/PWA — safe notification boundaries (candidate)

Date: 2026-10-20
PR: #1135 (DRAFT). Base: main@31380a7f4c8f61a3ec886ec9d2d66d26c2bf222b.
Status: **CONTRACT-ONLY / NO NOTIFICATION DELIVERY / NOT CERTIFIED**.

## Goal, success and proof

- **Goal**: keep reminders, IAmina conversation and governed proactive in-app observations separate. Do not simulate push delivery or allow unsolicited medical notifications.
- **Success for this sublot**: typed, fail-closed preview eligibility decisions; missing consent and patient-scope mismatch deny; browser push always disabled.
- **Proof required**: focused Flutter tests + complete exact-HEAD CI and browser regressions. A green CI does **not** prove a patient notification feature.

## Existing verified state

- `frontend/lib/features/reminders/reminders_screen.dart` stores user-authored reminders with Drift. OS notifications are explicitly unavailable.
- `backend/diabetes/api/v1/proactive.py` provides a read-only GET preview and state-changing POST evaluation. Neither provides browser/OS push.
- `backend/diabetes/services/clinical/proactive_intelligence.py` owns the existing **one non-urgent observation per 24 hours** budget. This is **not** an emergency threshold or a right to contact the patient.
- `frontend/lib/services/consent_service.dart` governs existing AI consent. It is **not** a verified D2 category-specific notification consent.
- Web patient/consent persistence and real-patient W01 Preview are not certified. W01 NO-GO / W02 frozen.

## New candidate technical boundary

`frontend/lib/services/d2_notification_policy.dart` separates:
1. **Reminder** — user-authored and stored locally. Never inferred as push delivery.
2. **In-app notification preview** — only a sourced, non-urgent proactive candidate can pass the dry-run gate.
3. **Companion conversation** — not a system notification or reminder.

Every candidate must have stable patient identity/epoch, unlocked state, explicit proactive opt-in **and** independently confirmed server consent, evidence ID and exact governed source version, nonexpired evidence, no treatment/emergency authority, no duplicate signature and the existing 24-hour attention rule. Missing/unknown inputs fail closed.

**Even a preview-eligible result is not a dispatch authorization.** `browserPushAvailable` is hard-disabled. The engine has **no runtime consumer**, storage schema, OS permission request, service worker, network action, scheduling, inbox state, clinical threshold, or LLM call. Test fixtures simulate consent only to prove reject/accept logic; they **do not** constitute real patient approval.

## Remaining sequence / human gates

1. Obtain W01-compliant authenticated Web identity and patient-scoped persistence with proven A→B→A isolation and revocation.
2. Implement server-authoritative D2 preferences default OFF: category-specific opt-in/out, auditable consent receipt, no cross-patient reads/writes, no PHI on lock-screen notifications.
3. Create a genuine inbox only for authenticated source-bound events; honor metadata retention, deletion, replay/idempotency, offline and stale-data constraints. Do not create a decorative inbox.
4. Produce BEFORE → goal → mockup → AFTER at the same FR/EN/AR and RTL mobile/tablet/desktop viewports, including empty, disabled and opted-out states.
5. Independent UX, clinical safety, privacy/security reviews and exact-HEAD CI. Qualified regulatory/clinical human authorization is a gate for actual medical push.
6. No merge or Vercel deployment without project release gates and explicit deployment authorization.

D1 remains deferred; D3 starts only after the D2 scope is genuinely concluded or transparently blocked.

## Visual D2 CTA correction — BEFORE / Goal / reference (written pre-implementation)

BEFORE: real Chrome artifacts [390×844](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/39436913086/artifacts/12271632356), [768×1024](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/39436913086/artifacts/12271557631), [1280×900](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/39436913086/artifacts/12272382552) from run #39436913086 and source-equivalent `6fc5375c`. Actual mobile + tablet PNGs inspected. The 'Ajouter le rappel' CTA still used `Icons.add_alert_outlined` (bell).
Goal: stop implying OS alert delivery while preserving the real user-authored local save flow.
Reference/mockup: keep existing 48px dark green `FilledButton.icon`, text, accessible layout, timing and handler; replace only bell glyph with `Icons.add_rounded` (simple plus).
AFTER: **not yet visually inspected** on the new HEAD. Require Chrome screenshots at identical 390/768/1280 viewports, compare CTA region, contrast, text, RTL and keyboard behavior before claiming UX certification. Different fixture values and clocks must not be misinterpreted as UI regressions.

## D2 Web consent-only backend sublot (candidate, 20 Oct 2026)

**Goal**: own non-urgent in-app preview preference OFF by default, revocable and patient-scoped, distinct from global AI consent. **NOT permission to notify.**
**Implementation**: `D2PreviewConsentReceipt` append-by-grant evidence, unique active receipt per patient with hashed FR/EN/AR notice, bound to exact valid global AI consent epoch; core migration `0020`; protected `GET/PUT/DELETE /api/v1/account/notification-preview-consent`; global AI withdrawal or renewal revokes D2. Returned `delivery_enabled=false` and `browser_push_enabled=false` always, even if opted_in. No UI, browser push, inbox, messaging producer, dispatch or medication decision.
**Proof targets**: Django tests `backend/core/tests/test_d2_preview_consent.py` cover anonymous deny, missing consent, wrong notice/hash, unknown caller fields, idempotency, A/B isolation, revocation, global reconsent and locale aliases. Exact-head Django SQLite/PostgreSQL/drift/Flutter CI required. Clinical + privacy human gates, W01 session safety and true user-facing rendered notice remain OPEN.
