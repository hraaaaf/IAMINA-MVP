## 27/10/2026 — D2 Web : centre de préférences relié à un consentement réel (candidate)

**Goal écrit / BEFORE** : sur PR #1135, écran Rappels seulement ; preuve Chrome FR BEFORE et AFTER du remplacement des icônes aux 390×844 / 768×1024 / 1280×900 dans la section ci-dessous. Aucun écran patient accessible de consentement D2 ; seuls GET/PUT/DELETE backend existaient. **Référence de maquette** : une carte séparée dans Rappels intitulée « Notifications IAmina » qui mène à une page « Notifications IAmina », deux blocs : état honnête « Aucune notification reçue / envois désactivés », puis texte d'accord intégral issu du serveur, confirmation volontaire et révocation. Même hiérarchie typographique, fond menthe et cartes arrondies que Rappels.

**Candidat ajouté** : `frontend/lib/features/notifications/d2_notification_center_screen.dart` écran Web FR/EN/AR, états loading/offline, notice serveur, case de confirmation (aucun opt-in par défaut), retrait ; `frontend/lib/services/d2_consent_gateway.dart` transport API protégé, lecture exacte `purpose`, `delivery_enabled=false`, `browser_push_enabled=false`, contrat notice, blocage des réponses stale après `AuthEpoch` A→B ; `/notifications` route protégée et lien dans Rappels. Pas de fake inbox, pas de message calculé/stoké, aucun push, aucune notification automatique. Les mêmes API patient-scopées restent source d'autorité ; permissions serveur préexistantes, refus 409 sans consentement global et CSRF sans contournement.

**Proof requis** : CI Flutter analyze/test/browser, nouveau widget test de consentement ack/revocation/default OFF/erreur offline, serveur SQLite+PostgreSQL ; captures AFTER Rappels + nouvel écran FR/EN/AR (390/768/1280), score visuel avant closeout. Ne pas prétendre D2 globale complète : une **vraie** inbox nécessiterait sources gouvernées, stockage/purge patient par identité, contrôles sécurité, sécurité clinique, consentement et règles d'envoi ; aucune autorisation de push ou d'egress clinique. Ne pas remplacer le constat clinique par une simulation qui invente des notifications.

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
AFTER (FR Chrome, inspected at the exact 3a60b84e code SHA): [390x844](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/39469380726/artifacts/12285843474), [768x1024](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/39469380726/artifacts/12287231028) and [1280x900](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/39469380726/artifacts/12287580106). Same-size BEFORE/AFTER PNGs visually inspected: the bell-plus glyph becomes a simple plus, with the card, labels, disclaimer, empty state and CTA geometry visually unchanged. Demo clock values also differ; no whole-screen pixel-perfect claim. Threshold >12 per RGB channel finds 244 changed pixels (390), 244 (768), 249 (1280), restricted to the small icon/time regions. This is **FR-only visual proof**. EN/AR RTL and keyboard/screen-reader audit remain unverified.

## D2 Web consent-only backend sublot (candidate, 20 Oct 2026)

**Goal**: own non-urgent in-app preview preference OFF by default, revocable and patient-scoped, distinct from global AI consent. **NOT permission to notify.**
**Implementation**: `D2PreviewConsentReceipt` append-by-grant evidence, unique active receipt per patient with hashed FR/EN/AR notice, bound to exact valid global AI consent epoch; core migration `0020`; protected `GET/PUT/DELETE /api/v1/account/notification-preview-consent`; global AI withdrawal or renewal revokes D2. Returned `delivery_enabled=false` and `browser_push_enabled=false` always, even if opted_in. No UI, browser push, inbox, messaging producer, dispatch or medication decision.
**Proof targets**: Django tests `backend/core/tests/test_d2_preview_consent.py` cover anonymous deny, missing consent, wrong notice/hash, unknown caller fields, idempotency, A/B isolation, revocation, global reconsent and locale aliases. Exact-head Django SQLite/PostgreSQL/drift/Flutter CI required. Clinical + privacy human gates, W01 session safety and true user-facing rendered notice remain OPEN.


## 2026-10-20 — D2 security: cookie CSRF regression on exact CI HEAD

**Goal** : un patient connecté par cookie Django ne peut pas activer/révoquer le consentement D2 Preview avec une mutation `PUT/DELETE` sans jeton CSRF Django valide ; les requêtes cross-origin et les requêtes mixtes cookie+Bearer doivent échouer sans écrire de reçu. Aucun browser push ni livraison de notification.

**Échec BEFORE reproduit CI exact `7b1fc0b96d0b74f47506a58604cf00738d8b0676` :** workflow CI #39460086330, jobs Backend SQLite `118768168771` (2874 tests PASS, un FAIL) et PostgreSQL `118768168694` (2878 PASS, un FAIL) : `D2PreviewConsentTests.test_cookie_session_mutations_enforce_csrf_token_and_origin`, attendu 403, reçu **200** dès premier `PUT` avec cookie/session valide et **sans CSRF**. **Impact candidat important :** opt-in D2 involontaire possible sur ce parcours tant que les préconditions globales sont réunies ; pas de preuve d'exploitation réelle ni de notification externe. La route Django-Ninja peut ignorer le middleware Django CSRF standard sur ses vues `csrf_exempt`. Ne jamais supprimer le test.

**Correctif code candidat, non certifié :** `backend/core/api/v1/d2_preview_consent.py` appelle explicitement `check_iamina_csrf` avant `PUT` et `DELETE` **pour toute requête contenant des cookies**, en conservant le modèle existing API Bearer-only sans cookies. La combinaison Cookie+Authorization est rejetée avant toute écriture. Test HTTP Django complémentaire : requête avec Bearer forgé + cookie A et jeton CSRF valide ou non → **401/403**, aucun reçu créé ; un cookie normal avec jeton CSRF correct peut consentir ; une révocation avec cookie+Bearer forgé n'efface pas le reçu. Authentification/cookie globales et garde CSRF W01 sont inchangées ; scope de correction réduit à D2 Preview. Aucun contournement de CSRF, aucune concession de politique clinique ni livraison push.

**Autre échec CI même HEAD, indépendant :** workflow `Offline demo UI certification` #39460086709 (job `118756974400`) interrompu sur navigateur mobile `WebAssembly compilation aborted: Network error: Response body loading was aborted`. Il n'est pas démontré que ce problème provienne du code D2; verdict à recontrôler sur CI du nouveau SHA **sans ajouter de retries aveugles**. Les sept autres workflows de `7b1fc0b` ont SUCCESS; ces succès ne prouvent pas le code corrigé.

**Preuve attendue pour nouvelle candidate :** Django SQLite + PostgreSQL tests CSRF passés ; test anti-mixte passé ; 9/9 workflows et browser visual/offline sur SHA final ; aucune notification réelle ; audit indépendance et preuve BEFORE/AFTER réellement comparables sur les trois viewports avant certification UI. **W01 NO-GO, W02 GELÉ**, arbitrages finaux Production repoussés par le propriétaire, aucun changement Neon/Vercel. D2 reste candidat PARTIEL, PR DRAFT. 


## CI corrective vérifiée — 20/10/2026

**HEAD code `7b9434b3438eceaf6f1b0439f5074e2c18eb5eb8` — 9/9 workflows GitHub Actions SUCCESS, 0 rouge, 0 queued/pending/in_progress.** [CI principale #39467921641](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/39467921641) tous ses jobs SUCCESS : Backend SQLite/Ruff **2876 PASS / 5 SKIP / 3 XFAIL**, PostgreSQL **2880 PASS / 1 SKIP / 3 XFAIL** (+ 129 subtests), Frontend Flutter analyze/tests/PWA build SUCCESS. Tests `test_cookie_session_mutations_enforce_csrf_token_and_origin` et `test_mixed_cookie_and_bearer_cannot_bypass_d2_consent_csrf` compris dans les suites PASS (aucune désactivation de leurs assertions). [Offline demo UI #39467920318](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/39467920318) **SUCCESS** après le défaut transitoire WebAssembly précédent ; [Chrome screenshot #39467920229](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/39467920229) **SUCCESS** sur les trois viewports. Migration drift et les autres contrôles SUCCESS.

**Conclusion exacte :** le défaut de consentement D2 par session cookie sans CSRF, reproduit auparavant en SQLite et PostgreSQL (`200` à tort), est résolu **dans les tests synthétiques de la candidate** par le contrôle explicite sur `PUT/DELETE` et le refus de credentials mixtes, sans autoriser des notifications. Pas de test hébergé ni de vrai compte Web patient, pas de prétention de correction générale du CSRF des autres routes. Les screenshots Chrome sont disponibles mais la comparaison visuelle BEFORE/AFTER multilingue n'a pas encore été certifiée ; l'artefact à lui seul ne prouve pas l'UX D2 en FR/EN/AR.

**Score matérialisé (révision adverse interne) :** Execution **8,6/10**, Adversarial **8,3/10** (écart 0,3), retenu provisoire plafonné **7,9/10** (preuves visuelles multilingues et revue indépendante insuffisantes ; sécurité réelle Web W01 différée par propriétaire). **D2 PARTIEL / PR DRAFT / NON MERGÉE / aucun déploiement**. Aucun flux push/browser/OS/inbox n'existe au runtime de cette candidate ; `delivery_enabled=false`, `browser_push_enabled=false`. Next = validation UX D2 avant/après, revue indépendante, et décision claire sur attente W01 avant tout branchement patient effectif. La présente mise à jour documentaire change le SHA : CI exacte à revalider ; les preuves 9/9 ci-dessus concernent le SHA **code** `7b9434b3`.

## 2026-10-20 — Adversarial read-back and candidate NO-GO (PR #1135)

**Review independence:** one isolated critical pass by the same executor, not an external independent security/clinical/privacy reviewer. Neither clinical-human nor owner approval is implied. This cannot certify real-patient notification delivery.

**Exact verified code SHA:** `3a60b84eebad8a92134150d0c4d315cb342134d3` — 9/9 GitHub workflows SUCCESS: [CI #39469380613](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/39469380613), [migration drift #39469380509](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/39469380509), [Offline UI #39469380526](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/39469380526), [Chrome #39469380726](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/39469380726) and the five remaining UI/E2E workflows. Exact CI logs: **SQLite 2,876 passed, 5 skipped, 3 xfailed, 129 subtests**; **PostgreSQL 2,880 passed, 1 skipped, 3 xfailed, 129 subtests**. Ruff, import-linter, AI anti-bypass, Bandit, OpenAPI drift, Flutter analyze/tests and PWA build also green. No disabling of checks.

**Confirmed scoped architecture:** authenticated D2 GET/PUT/DELETE uses only `request.user`; grants require valid global AI consent, current hashed FR/EN/AR D2 notice, server-side patient scope and epoch. Database-level partial unique constraint permits one active receipt; revocation timestamps and new global consent epoch invalidate prior D2 grants. Historical 200-without-CSRF regression was reproduced on both DBs, followed by successful negative CSRF, foreign-origin, mixed cookie+Bearer and A→B→A *server receipt* regression tests. Dart evaluator rejects browser push, unknown source, wrong patient/epoch, emergency/treatment authority, stale evidence, cooldown and repeats; even eligible preview cannot send. `delivery_enabled=false` and `browser_push_enabled=false` are hard coded; no runtime inbox, producer, dispatch or new clinical threshold.

**Adversarial findings and limits:**
1. BLOCKING for real-patient D2: no authenticated consent UI shows the exact D2 notice to a patient and captures the actual user's informed opt-in; synthetic requests and notice hashes alone do not prove informed choice.
2. BLOCKING for real-patient D2: W01 remains NO-GO and W02 frozen; server-side receipt A→B→A tests do not prove hosted Web/API authentication, browser vault A→B→A, encryption, key recovery or security of every other cookie-authenticated route.
3. Audit evidence caveat: `core.audit.record_audit()` silently no-ops without a registered sink and catches sink errors. The database receipt (grant/revocation) is durable in tested PostgreSQL, but an operational audit-event stream is **not** guaranteed. Tamper evidence and per-purpose retention/erasure policy are unproven.
4. Scope caveat: no real notification inbox, egress, live patient record, browser/OS push or clinical delivery has been tested or authorized. Clinical-human, privacy/CNDP and independent security reviews remain mandatory before such capabilities.
5. UI caveat: visual Target-to-Render comparison is valid only for the FR reminders CTA at the three recorded sizes, not for EN/AR RTL, keyboard navigation, screen readers or a future consent/inbox UX.

**Required scoring (docs/QUALITY_SCORING_POLICY.md):**
- Consent backend + session CSRF: Goal = revocable consent fail closed per patient; success = passing positive/negative SQLite+PostgreSQL, migration and OpenAPI gates; evidence = CI above. EXECUTION_SCORE **8.6/10**, ADVERSARIAL_SCORE **8.3/10**, gap **0.3**, capped RETAINED **7.9/10** due unverified hosted identity and independent privacy review.
- Pure preview policy: Goal = scoped deterministic preview with no dispatch authority; success = Flutter tests and no producer in final diff; evidence = Flutter test/build + source. EXECUTION_SCORE **8.6/10**, ADVERSARIAL_SCORE **8.1/10**, gap **0.5**, capped RETAINED **7.9/10** due absent clinical independent approval/integration.
- Reminders CTA: Goal = honest plus icon without geometry regression; success = same-size FR Chrome before/after and static contract; evidence = artifact links above + pixel inspection. EXECUTION_SCORE **8.5/10**, ADVERSARIAL_SCORE **8.0/10**, gap **0.5**, capped RETAINED **7.5/10** due missing required EN/AR RTL and a11y Target-to-Render proof.
- **LOT retained = min = 7.5/10 — NOT_VERIFIED, full D2 NO_GO**. All code CI binary gates are green on the cited code SHA, but real-patient UX/identity, independent review, clinical approval and Perfection Pass are incomplete. Do not treat 9/9 CI as D2 complete.

**Reviewer verdict (same-executor isolated pass):** CHANGES_REQUIRED for full D2, candidate preview-only boundaries retained without activation. **Next exact:** independent specialists (security/privacy, DB, clinical, UX), then W01 hosted auth + DB integration/gates and W02 vault; only afterward implement category-specific consent UI and genuine source-bound inbox. No patient use, no push, no merge, no Vercel.

**Freshness note:** committing this review changes HEAD; CI proof cited above attaches to `3a60b84e...` only. Re-validate exact new HEAD before any merge-readiness statement.
