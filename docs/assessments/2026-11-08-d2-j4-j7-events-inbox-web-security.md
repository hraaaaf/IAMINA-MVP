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
