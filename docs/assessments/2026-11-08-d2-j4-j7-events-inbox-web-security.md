# IAMINA — D2 — Coordination J4→J7 : notifications Web (candidat)

**08/11/2026 | Base : PR Draft #1323, HEAD vérifié fca583c (13/13 GREEN)**
**Branche :** `feat/d2-j4-j7-notifications-stack-20261108` **empilée sur** `feat/d2-notification-center-web-20261108` ; **aucune fusion ni activation/déploiement**.

## Décision approuvée / Goal

Cloche haut droite exclusivement pour les notifications **événementielles + proactives** ; D3 rappels en bas de l'accueil **inchangés**. J4 = source réelle, J5 = inbox + consentement, J6 = Web, J7 = sécurité/FUE. **Pas de notifications médicales, données cliniques, diagnostics ou appels push**.

**SUCCESS candidature technique :** deux vrais événements de compte (acceptation/retrait d'un consentement AI) générés par les **lignes `AIConsentReceipt` réellement enregistrées**, plus une suggestion de langue **non clinique** lorsque la préférence de langue est effectivement non confirmée, et **après opt-in proactif distinct**. Aucun LLM. Le projet ne doit jamais générer de notifications fictives ni dupliquer D3. Les autres catégories sont des **idées**, non des producteurs existants.

## BEFORE — preuves des sources et du périmètre

- `main@0a096ac...` contient `core.api.v1.account.give_consent/withdraw_consent` persistant `AIConsentReceipt` comme preuve immuable ; pas d'inbox de notifications spontanées.
- `core.models.locale.PatientLocalePreference` expose `ui_language_provenance=user_confirmed|suggested|defaulted` : **source réelle** d'une suggestion non clinique, pas du contenu médical.
- PR historique #1135 contient un inbox de **sauvegardes volontaires** (`context`/`meal`) : interdit de le présenter comme une notification générée sans intervention patient. Migration #1135 a aussi un numéro 0020 **incompatible** : ne pas fusionner les deux branches sans consolidation de schéma.
- PR UI #1323, success 13/13 sur SHA `fca583c`, cloche vers `/notifications`, D3 inchangé ; pas encore d'API.

## AFTER — J4 sources effectivement attestées par backend

- `core.d2_notification_service.record_verified_event()` ne reçoit aucune entrée client : exige patient_id int, code allowlist, receipt DB avec **patient identique** et **état réel donné/retiré** ; clé HMAC source+patient+code idempotente ; aucun contenu libre ni clinique.
- Seuls `ai_consent_given` et `ai_consent_withdrawn` sont produits sur commit d'account, dans un **callback après transaction** qui ne peut pas bloquer l'action de consentement originale si D2 est indisponible. Une émission ratée n'est pas inventée ni affichée.
- `maybe_record_language_preference()` vérifie provenance `PatientLocalePreference` existante et non confirmée et opt-in courant ; source code `language_pref_available`. Évaluée après la confirmation de consentement proactif. **Ce n'est pas un scheduler ni une proactivité clinique autonome en continu.**

## J5 — modèle, API et consentement

- **Migration de code** `core/migrations/0020_d2_notification_center.py` **créée mais PAS appliquée à Neon**. `D2Notification` stocke patient, signature HMAC, kind, code allowlist, création, expiration, lu ; aucun chiffre médical ou texte libre. `D2NotificationPreference` one-to-one patient, OFF par défaut, preuve de notice acceptée (version/digest) et révocation.
- Endpoints sous l'auth existante (session sécurisée ou bearer) : `GET /api/v1/account/notifications`, `PUT/DELETE .../proactivity`, `PUT .../{id}/read`, `POST .../read-all`, `DELETE .../{id}`. Les mutations refusent cookie+bearer et exigent CSRF session valide. Le GET renvoie un token CSRF lié à session (pas d'information patient) pour le client. Toutes les lectures/mutations sont filtrées par `request.user` côté serveur. **Jamais de sélection patient libre envoyée par le navigateur.**
- Proactivité : ON après notice exacte + acknowledgment, OFF + effacement instantané des notices proactives ; limite candidate **1/24h et 2/7 jours glissants**, HMAC dédup, boîte limitée à 40. Factual account events hors quota proactif.
- Expiration affichage J+7 (pas de suppression physique garantie). Commande manuelle `purge_d2_notifications` : **dry-run par défaut**, `--apply --limit 100` optionnelle ; pas de cron, pas de claims de suppression J+7. Backups et demandes RGPD exigent revue.

## J6 — UI protégée et Web

- `D2NotificationsScreen` conserve état « réception non activée » lorsque aucun ApiClient n'est fourni (captures Chrome synthétiques). Si `ApiClient` existe, elle instancie `D2LiveNotificationsScreen` utilisant `D2ApiNotificationGateway` : chargement API patient, strictes vérifications schéma/code/date/unread, changement d'epoch auth avant application de résultats, consultation, lu, suppression, activation **avec boîte de dialogue et consentement affiché**, désactivation sans faux succès. Texte FR/EN/AR non clinique. D3 rappel non modifié.
- `requirePilotClinicalTransport` ouvre **uniquement** l'API D2 compte (non clinique), sans ouvrir logs/profil médical. Les autres contrôles auth epoch/app lock restent applicables. Le client transmet le token CSRF reçu du GET pour les mutations Web.
- **Important :** un vrai test d'identité A→B→A sur environnement hébergé et Vercel PWA nécessite une autorisation distincte ; aucun déploiement n'a été effectué ici.

## J7 — tests adversariaux et gates restants

Tests :
- Backend `test_d2_notifications.py` : zéro notification initiale, vrais receipts et refus de forge, révocation/consentement, quotas, CSRF mixte, mauvaise identité A/B, lu/delete, expiration et purge manuelle, continuité des consentements si le producteur D2 est KO.
- Frontend `d2_notification_gateway_test.dart` : parser fail closed pour code médical inconnu, id dupliqué, pseudo-unread, push et dates invalides ; `d2_live_notifications_screen_test.dart` : FR/AR/EN, événement réel synthétisé en test, consentement explicite, erreur API = aucun faux item.
- CI exact SHA, migration drift PostgreSQL, FUE Chrome, analyse de code, egress contrôles et revue indépendante **NON encore acquis** lors de ce document (ne pas attribuer de note sans lecture des résultats).

**Gates de sortie NO-GO patient :**
1. Auth réelle Web/API isolée A→B→A, CSRF avec session cookie, consentement OFF/ON/OFF persistant, concurrence et quota atomique testés sur PostgreSQL.
2. Rétention/purge et sauvegardes documentées/programmées avec approbation sécurité et privacy ; la commande seule n'est pas un scheduler.
3. Revue indépendante sécurité, UX, clinique et RGPD ; cas hors-ligne, clavier, RTL, 390/430/768/1280 avec vrais états et captures BEFORE/AFTER. **Ni badge 13/13 du lot UI précédent ni CI de ce lot n'équivalent à ces validations.**
4. La fonction « proactive » actuelle ne produit qu'une suggestion non clinique lors de l'opt-in si une source existe ; elle n'est pas encore une assistance clinique autonome planifiée. Toute extension nécessite consentement et revue dédiés.

**Déploiement : AUCUN Vercel même preview sans GO explicite du propriétaire. Aucune mutation Neon/C7, aucune donnée patient réelle, aucune fusion.** Le sous-lot est **candidat et doit rester Draft**.

**NEXT exact :** vérifier le nouveau SHA de la PR et les tests/migration drift ; diagnostiquer/corriger tout FAIL. Puis renforcer auth session A/B sans activer patient ; avancer vers review indépendante avant toute fusion/déploiement.

**Canonique Notion :** [01 — ROADMAP IAMINA](https://app.notion.com/p/3df77c66336281f5b308ec17f7f0a63b).

## 09/11/2026 — D2 J7 FUE HTTP locale, décision de validation actualisée

**Décision utilisateur du 09/11 :** retirer la *revue indépendante supplémentaire* de la checklist D2 ; la remplacer par des FUE et des CI à HEAD exact. Les anciennes occurrences du gate de revue sont des archives de décisions précédentes, non le gate J7 courant. Les invariants de sécurité, consentement, confidentialité, données et les approbations humaines légalement nécessaires ne disparaissent pas.

**GOAL / SUCCESS :** prouver des parcours HTTP intégrés sur utilisateurs synthétiques avec sessions réelles Django Client et contrôles middleware/CSRF, puis obtenir sur le nouveau SHA des jobs SQLite, PostgreSQL, Flutter et Chrome. Pas de données patients ni d'écriture Neon réelle.

**PREUVE locale initiale** sur le clone séparé `DESKTOP-3MAJEEH` au `bc5fd9f4e0dc5aaf52349c69c4db765de7058f89` : `19 passed in 2.90s` sur `test_d2_fue_http.py` (3 nouveaux parcours) + `test_d2_notifications.py` + `test_d2_http_session_a_b_a.py` (16 précédents). Cas fonctionnels : compte A→B→A, GET inbox, badge lu/non-lu, refus anonyme, CSRF absent, credential bearer concurrent, mauvais propriétaire 404, marquer lu/supprimer, préférence FR/EN/AR, consentement D2 version/hash exact, ON→OFF→ON sans réémission malgré reconnexion, vrai consentement global via HTTP POST/DELETE avec `on_commit` et `AIConsentReceipt`. Database SQLite temporaire synthétique. Après modification des fichiers, cette preuve doit être rejouée sur le **nouveau** HEAD et confirmée sur CI, sans héritage abusif du 19/19 historique.

**TRACE:** `backend/core/tests/test_d2_fue_http.py` ajouté ; workflow `.github/workflows/d2-j4-j7-candidate.yml` inclut désormais FUE HTTP explicitement dans les jobs SQLite et PostgreSQL. État à vérifier après push : nouveau SHA, 2 CI D2 et workflow Chrome, toutes les collections et skips. Aucun déploiement Vercel permis ; manifests root et frontend ont `git.deploymentEnabled=false` dans la copie locale.

**LIMITES :** tests HTTP Django internes ≠ FUE Flutter Web navigateur authentifié ; Chrome historique teste des écrans avec fixtures, pas de parcours hébergé A→B→A. Pas de Flutter SDK ni navigateur prouvé sur le PC, donc ne pas revendiquer de validation UI réelle par Desktop Commander. Reste à traiter : FUE Web utilisateur avec état session authentifié, cas réseau offline/retour, contrôle visuel 390/430/768/1280 FR/EN/AR, conflit migration `0020` avec PR #1135, purge/rétention/backup/erasure vérifiable, autorisation expresse pour tout Vercel preview/prod. **D2 PATIENT : NO-GO, PR DRAFT**, pas de merge.

**Notion canonique :** https://app.notion.com/p/3df77c66336281f5b308ec17f7f0a63b

### 09/11/2026 — FUE UI Flutter complémentaires (avant CI)

Extension ciblée du test widget de production `frontend/test/features/notifications/d2_live_notifications_screen_test.dart` : FR/EN/AR × 390×844, après acceptation explicite du consentement, désactivation OFF, suppression d'un avis et état inbox vide ; nouveau scénario de panne temporaire gateway puis bouton Retry garantissant zéro avis fictif avant reconnexion. **Ce sont des tests d'interface Flutter avec gateway synthétique et non de navigation PWA hébergée.** Flutter SDK non disponible sur le PC Remote Desktop Commander : résultat local non prétendu PASS. Le workflow D2 (Flutter tests complets + PWA) doit établir l'exécution et les éventuelles régressions au nouveau SHA après push. Aucun code de l'application modifié.

## 09/11/2026 — D2 J7 migration arbitration and retention FUE (DESKTOP-3MAJEEH)

### Decision: one active D2 migration lineage; legacy PR archived without merge

- Verified [#1135](https://github.com/hraaaaf/IAMINA-MVP/pull/1135) head `ac72f9669164144940576d4cb3cce1326e0d3bdc` is a legacy preview/context/meal-notice candidate with migrations `0020_d2_preview_consent_receipt` → `0021_d2_in_app_notice` after `0019_auth_abuse_bucket`. It is semantically different from the narrowed November D2 verified account-event inbox `0020_d2_notification_center` (current [#1324](https://github.com/hraaaaf/IAMINA-MVP/pull/1324), head at start of audit `4ad9c607712d7d4ec0785eb0e24802f8382ec45a`).
- On isolated audit clone, fetched `refs/pull/1135/head`, temporarily added its exact old migration files beside current new `0020` and ran `python manage.py makemigrations --check --dry-run` (synthetic `DATABASE_URL=sqlite:///d2-migration-audit.db`). **RED reproducible, exit 1:** `CommandError: Conflicting migrations detected; multiple leaf nodes in the migration graph: (0020_d2_notification_center, 0021_d2_in_app_notice in core)`. Do not auto-merge these unrelated models.
- After removing ONLY the two temporary old migration files, clean clone; `python manage.py migrate --noinput` on fresh `d2-retention-audit-only.db` produced `Applying core.0020_d2_notification_center... OK` and remaining system migrations OK; `python manage.py makemigrations --check --dry-run` → `No changes detected`, exit 0; `showmigrations core` confirmed `[X] 0020_d2_notification_center`. **No Neon migrations or live patient data.**
- [#1135](https://github.com/hraaaaf/IAMINA-MVP/pull/1135) deliberately **CLOSED / NOT MERGED** to remove the obsolete schema from the active D2 merge path; branch and discussion retained. Closure is **NOT proof that both historical migration lineages can be combined**, and reopening/cherry-picking #1135 without a new schema decision would recreate the conflict. Distinct reminder/D3 icon fixes not in #1324 are explicitly preserved under [issue #947](https://github.com/hraaaaf/IAMINA-MVP/issues/947#issuecomment-6735594092) for a separate future decision. No Vercel, Neon, patient deployment, or merge.

### Retention FUE: real command against synthetic Django DB, no production schedule

- New test `backend/core/tests/test_d2_retention_fue.py` exercises `purge_d2_notifications`: dry-run **preserves** rows and reports 3 expired notices + 2 expired receipts; shared `--limit=2` enforces successive applied batches `deleted=2/receipts_deleted=0`, then `deleted=1/receipts_deleted=1`, then `deleted=0/receipts_deleted=1`. Post-drain reports `expired=0 receipts_expired=0`. Unexpired other-patient notice and anti-repeat receipt 6 days old remain untouched. Invalid limits 0 and 201 are rejected; account ORM cascade deletes own preference, notice and emission receipt while preserving another patient's notice.
- **Local proof:** `ruff check backend/core/tests/test_d2_retention_fue.py` → PASS; `pytest -v -q core/tests/test_d2_retention_fue.py core/tests/test_d2_notifications.py core/tests/test_d2_fue_http.py core/tests/test_d2_http_session_a_b_a.py` → **21 passed in 2.67s, exit 0**. CI workflow D2 explicit FUE commands extended to include retention in ephemeral SQLite and PostgreSQL (new SHA and new CI must be verified after push). These tests do not exercise Firebase deletion hooks or any production account data.
- **Operational gap explicitly OPEN:** `purge_d2_notifications` is MANUAL, dry-run by default and deletes **at most 200 records per invocation, jointly across two tables**; no cron, scheduler, production log receipt, alerts or backup erasure evidence is active in this PR. A single daily batch may leave expired rows when backlog exceeds its cap. Enforcing physical TTL requires an approved external daily scheduler that drains batches until both expired counters reach zero, records job ID/timestamp/row counts/errors, and alarms on incomplete drain. A separately approved recovery/backup policy must document snapshot retention, encryption/access, backup deletion/expiry, and **post-restore immediate purge before exposing restored user data**. Do not claim end-to-end physical erasure or 7-day backup expiry without observed production evidence.
- **Runbook proposal only, NOT activated**: in an authorized deployment with a least-privilege role, run `python manage.py purge_d2_notifications --limit 200` to inspect counts; run `python manage.py purge_d2_notifications --apply --limit 200` repeatedly until a final dry-run reports `expired=0 receipts_expired=0`; monitor and alert on any residual or failure. No new automatic deployment/scheduling changes without explicit owner approval. The HTTP inbox hides expired rows even before physical purge; this is a different property from storage deletion.

**D2 J7 overall remains OPEN / PATIENT NO-GO:** no hosted authenticated Flutter Web A→B→A proof, no scheduler/backup/restore proof. FUE+CI replace the removed independent-review gate under owner decision. Canonical Notion: https://app.notion.com/p/3df77c66336281f5b308ec17f7f0a63b.

## 09/11/2026 — D2 J7 — retention job / post-restore gate candidate (NOT ACTIVATED)

**Decision:** keep the legacy `purge_d2_notifications` manual dry-run behavior backwards compatible, while making an explicit *opt-in* operator sequence capable of bounded draining and fail-closed post-restore verification. **No scheduler is activated and no production database is accessed by this PR.**

### Command contract (only after an approved deployment, with the approved runtime and secrets)

1. **Observe (no writes):** `python manage.py purge_d2_notifications --limit 200` emits `D2 DRY_RUN expired=N receipts_expired=M max_batch=200`. Do not log patient IDs or content. Notice expiration is 7 days from record; anti-repeat receipts expire after 7 days.
2. **Operator/singleton scheduler run (writes, separate authorization):** `python manage.py purge_d2_notifications --apply --drain --limit 200 --max-batches 50`. Each transaction deletes at most **200 combined rows** from both D2 notice and D2 proactive-emission receipt tables. Total max per invocation **10,000** rows at these arguments (hard bounds: `--limit` 1..200, `--max-batches` 1..100). Emits `D2 DRAIN batches=... deleted=... receipts_deleted=... expired_remaining=... receipts_remaining=... max_batch=... max_batches=... COMPLETE` only if zero expired remain at its fixed start cutoff; otherwise exits **nonzero** with `CommandError ... INCOMPLETE`. A capped run can already have deleted some rows: schedule retry and measure residual; never treat an exception as rollback of prior batches.
3. **Post-restore pre-traffic gate (READ-ONLY):** `python manage.py purge_d2_notifications --require-empty`: emits `D2 RETENTION_CHECK PASS expired=0 receipts_expired=0` only if no expired D2 rows remain *at its fresh cutoff*, otherwise **nonzero** `D2 RETENTION_CHECK FAIL expired=N receipts_expired=M`. Requires DB migrations applied and connectivity. After restoring an older snapshot, operator **must** run and verify bounded drain first, then run `--require-empty` and obtain exit 0 **before enabling patient traffic**.
4. **Fail-closed controls:** `--drain` without explicit `--apply` errors; `--require-empty` combined with any write flag errors; invalid caps fail before any mutation; no clinical content or patient identifier is output. Dry-run remains the default. No frontend feature toggle or live notification delivery is enabled.

### Scheduling and backup policy decisions (NOT implemented or approved yet)

- Select the actual hosting environment, approved service identity/least-privilege DB role, and a **single-run lock** (external scheduler singleton / distributed coordination) before activation; the Django command does **not** claim to supply a cross-instance PostgreSQL advisory lock. A busy concurrent scheduler without a lock is **not** certified. Record execution time UTC, release SHA, scheduler job ID, exit status, total deleted/residual counts, errors and retries; alarm if nonzero exit, residual expired rows or missed scheduled execution. Operator/scheduler cadence is to be approved according to clinical/privacy policy; no production schedule has been configured.
- Explicitly approve backup scope (PostgreSQL and any connected storage), encryption/key ownership, access controls, snapshot retention/deletion and restore permissions. A live DB purge does **not** erase existing backups: previous synthetic snapshot experiment demonstrated **active 0 expired rows, old backup still 1**. Document restore isolation, apply migrations, drain, require-empty check, then enable traffic; define a measurable retention SLA and an evidence log. Avoid promising seven-day physical deletion in snapshots unless the backup policy actually enforces it.
- **Human gate:** activation of scheduler against the real DB, backup policy, migrations on Neon and any Vercel deployment require explicit environment-level approval. This candidate does not automate any of these operations, does not interact with patients, and remains D2 PATIENT NO-GO.

### Tests / evidence

- `backend/core/tests/test_d2_retention_fue.py`: existing three-pass bounded manual purge + cascade, plus new FUE for **--apply --drain**, max-batches cap and honest partial deletion on nonzero exit, immutable owner B/live rows, read-only `--require-empty` post-restore guard when stale synthetic row returns, invalid combinations never deleting.
- Remote Desktop Commander clone `DESKTOP-3MAJEEH` at input SHA `1da13b2d94cc70020eec1df1611585c588ac6cc9`, local SQLite synthetic: `ruff check` PASS, `24 passed in 2.76s`, `makemigrations --check --dry-run` No changes detected. CI must re-run on new HEAD (SQLite/PostgreSQL), with old 7/7 success no longer used as the exact-head proof until completion. Retention scheduler and backup recovery remain **unverified operationally**.

**Notion canonical:** https://app.notion.com/p/3df77c66336281f5b308ec17f7f0a63b
