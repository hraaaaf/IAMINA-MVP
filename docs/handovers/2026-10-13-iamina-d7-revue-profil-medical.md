## 14 octobre 2026 — décisions #7 et #9 : deux émulateurs Ubuntu VALIDÉS, human gate ouvert

**Goal atteint sur le sous-lot virtuel :** [PR #1004](https://github.com/hraaaaf/IAMINA-MVP/pull/1004) test-only MERGED dans la branche D7 au commit `0039b1c4a1be71a89a77f7857fdf6097d4895145`, PAS dans main. Preuve sur SHA exact prémerge `cbbdb0ec4bbe9e4b36f65f0c4381fdfecc7b8d15` : [workflow Ubuntu #38639307598](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38639307598) SUCCESS et [D9×D7 #38639307463](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38639307463) SUCCESS. [Artifact #11930131647](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38639307598/artifacts/11930131647) **téléchargé, inspecté** : Android 15 `emulator-5554` et `emulator-5556` simultanément connectés au MÊME hub synthétique Ubuntu, 1 test PASS sur chaque appareil. Device 1 A→B→A isolé avec sauvegarde SQLite locale/pending ; Device 2 installation neuve A sans profil clinique restauré, sans consentement emprunté. Attestations exactes dans `shared-hub.json`. Les émulateurs NE SONT PAS des appareils physiques, le hub n'est pas une synchronisation clinique.

**Post-merge D7 SHA `0039b1c4` :** les workflows ont révélé une ancienne dépendance Python indisponible `google-genai==0.3.*` lors de l'installation (`Django migration drift #38642685256`, `Dashboard responsive #38642685447`), avant d'exécuter les tests produit. Ce commit de correction remplace le pin par `google-genai==2.30.1` et restaure un test **offline** d'interface SDK, sans aucun appel IA/HTTP. Le résultat de la CI sur le **nouveau HEAD documentaire/de dépendance** doit être vérifié, sans reporter les succès antérieurs.

**Human gate et décisions :** [issue #999](https://github.com/hraaaaf/IAMINA-MVP/issues/999) P01–P09 sur 2 vrais appareils + avis indépendants clinique, confidentialité, sécurité, UX **NON EXÉCUTÉS**. #7 et #9 NE SONT PAS cochées livrées ; aucun merge main, pas de patient réel, pas de déploiement Vercel. P5 historique 50 %.

---

## 14 octobre 2026 — recentrage exclusif décisions #7 et #9 (NON CLÔTURÉES)

**Périmètre** : #7 profil médical facultatif et traitements modifiables, coffre patient local cloisonné ; #9 compte existant : éviter onboarding répété sur la MÊME installation et ne jamais hériter du consentement ni du profil d'un autre compte. Pilotage conforme à la décision propriétaire : pilote A 100 % local, pas de restauration du profil sur nouvel appareil, pas de synchronisation clinique ni de faux ACK. État vérifié : PR #985 tests #9 MERGED dans main ; PR #991 test A→B→A MERGED dans la branche #986 ; PR #986 DRAFT. Preuve automatisée sur code `a2b481e7` : 20/20 workflows GitHub SUCCESS, dont sauvegarde et réouverture SQLite synthétique D9 ; pas d'observation sur deux téléphones.

**Rectification de périmètre** : retirer des différences finales de #986 les modifications ultérieures relatives à l'adaptateur Groq, au SDK Gemini et à la qualification Pulper, sans supprimer leur historique Git ; le défaut Pulper reste suivi séparément en issue #1002 et n'est pas une décision #7/#9. Le retour de `backend/requirements.txt` à sa version initiale peut laisser un risque externe de résolution pip ; tout nouveau run exact HEAD doit être lu, aucune réussite transposée. N'effectuer aucune nouvelle boucle Pulper sur ce lot.

**Gates de clôture #7/#9 :** preuves P01–P09 sur deux appareils avec comptes fictifs et traces réseau anonymisées, revue clinique/sécurité/confidentialité/UX indépendante (issue #999) et validation explicite du périmètre « même installation seulement » ; pas d'affirmation de restauration cross-device. Puis verdict CI sur HEAD exact, merge contrôlé vers main seulement si approbations médicales et protection patient vérifiées, post-merge, actualisation du tracker. Ne jamais cocher ces décisions uniquement pour satisfaire un statut. Aucun déploiement Vercel, aucun patient réel. P5 historique 50 %.

---

# IAMINA D7 / D30 — PILOT A LOCAL ONLY — 14 Oct 2026 — CANDIDATE NOT CERTIFIED

USER DECISION: pilot A saves clinical data on-device only. No medical transport until patient-bound, purpose-specific, versioned and independently reviewed consent exists. This is NOT an authorization to merge or deploy to Vercel production.

GOAL: no /api/v1/ non-auth transport from standard runtime; zero raw SSE/chat/image/audio/document egress; no auth token resolution or CurlInterceptor logs for blocked clinical calls; never consume or ACK pending Drift outbox while disabled; display honest local-only sync status FR/EN/AR without a fake Retry action.

BEFORE code review: ApiClient PATCH profile/treatments, journal and AI direct HTTP could run with only bearer/device-unlock; SyncService retried data and showed upToDate when no queue. Native bearer is not clinical-sync consent. D30 drafts #988, #989, #990 all overlap in api_client.dart and are not integrated or clinically approved.

VISUAL BEFORE: pre-change dashboard status is cloud checking/pending/upToDate (44x44 icon button); no directly comparable screenshot of this exact status was captured, so there is no supported pre-change pixel visual score.
VISUAL MOCKUP TARGET: preserve 44x44 topbar geometry but use device icon and tooltip/status 'Offline pilot · saved on this device, not synchronized' / FR 'Pilote local · enregistré sur cet appareil, non synchronisé' / AR 'الوضع المحلي · محفوظ على هذا الجهاز، غير متزامن'. Disable tap/retry and show truthful local-only save feedback. Compare 390x844, 768x1024, 1280x900 in follow-up screenshots and human UI review before assigning score.

CANDIDATE IMPLEMENTATION: ApiClient defaults to canSyncClinicalData=false and passes explicit local-only gate into AuthInterceptor and RetryInterceptor before token reads, sends, retries. All raw/direct media transports return prior to building a request or reading document stream; getProfile/mirrorTreatmentDeclaration/patchProfile/log sync return unavailable. CurlInterceptor removed. Public /api/v1/auth/ remains reachable for account functions. An explicit synthetic-test-only constructor capability allows controlled existing network contract tests to continue. SyncService prevents reads/restores/ACK/retries, emits SyncUiState.localOnly even when internet is available; pending/conflicts remain stored locally. UI uses localized ARB/generated messages and removes remote-conflict resolve CTA in pilot A. Django server code unchanged.

EXPECTED PROOF, NOT YET CLAIMED: 17 GitHub workflows exact latest SHA success (SQLite, PostgreSQL, Flutter, browser, packaging), targeted negative tests pre-token/HTTP and outbox preservation; compare visual BEFORE/AFTER on same viewports. Earlier 17 green status belonged to an older head. If CI fails, fix then restart. No clinical data used.

HUMAN GATES: an independent privacy/clinical review, actual device offline/restart behavior, versioned consent and owner/vault binding, direct Chrome authenticated 409 dialog screenshots if sync ever reenabled, explicit UX acceptance. Pilot A intentionally defers remote restoration and cross-device synchronization, not a bug to paper over.

STATUS: PR #986 OPEN/DRAFT; NO MERGE, NO VERCEL PROD, NO REAL PATIENT ACTIVATION. P5 historic baseline 6/12=50% unchanged.

---
# IAMINA D7 — 14 octobre 2026 — VRAI HTTP SUR DJANGO LOCAL, DEUX CLIENTS SYNTHÉTIQUES — E2E ISOLÉ

**Goal** : prouver à travers un véritable serveur Django TCP le contrat d'isolation des comptes et de résolution CAS sur deux clients HTTP indépendants, avec uniquement des identités synthétiques et une DB éphémère. Ce test reste distinct d'un test Flutter/Drift sur deux appareils physiques.

**Preuve indépendante avant intégration** : branche audit `audit/d7-live-http-e2e-20261014@76236f3414c18b96e3417d23720436be7817d290`, [GitHub Actions #38582759703](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38582759703) **SUCCESS, 2 tests passed in 2.54s**, vrai `LiveServerTestCase` Django + HTTP réel via `urllib.request` et vrai parseur `HttpBearer`. Aucune communication avec Vercel ni backend certifié.

**Assertions** : deux clients HTTP distincts et bearer A/B ; A et B n'accèdent qu'à leur profil ; second client A lit les valeurs serveur ; première création CAS `none` acceptée (200), modification concurrente depuis deuxième client acceptée avec révision exacte ; rejeu de l'intention périmée par premier client `409`, même intention sans en-tête `428` sans écrasement ; A→B→A sur un même client conserve l'identité explicite ; nouvelle révision choisie validée en 200 ; bearer absent ou falsifié refuse l'accès 401/403.

**Limitations non négociables** : « offline intent » est une simple structure de test en mémoire, **PAS** une file Drift persistante ou un redémarrage hors ligne. Il s'agit de clients HTTP, **PAS** de deux sessions Flutter authentifiées ni d'appareils physiques. Consentement de synchronisation versionné, egress D30, contrôle de sécurité indépendant, captures de vraie modal 409 et validation clinique/UI demeurent nécessaires.

**Action** : intégrer le test `backend/diabetes/tests/test_d7_live_http_e2e.py` à la branche D7 PR #986 pour l'inclure dans la **CI complète SQLite+PostgreSQL**, sans changement de code runtime ni déploiement. La nouvelle suite à HEAD final doit repasser tous les workflows ; les 17/17 verts précédents concernent `c9577c8e…`, pas le nouveau commit.

**Vercel** : Preview DEV isolée https://iamina-review-la39twh0a-achraf-benmoussa-s-projects.vercel.app toujours dédiée au navigateur local-only ; preuve de deux contexts Chromium limitée, jamais utilisée pour les requêtes médicales. Backend certifié et production non modifiés.

**GO/NO GO** : PR #986 DRAFT, D7 produit OPEN, PAS DE MERGE, PAS DE VERCEL PROD, PAS DE DONNÉE PATIENT RÉELLE. P5 historique 50 %, non modifié. Next exact = 17 verdicts GitHub exact HEAD, puis arbitrage privacy D30 #988/#989/#990, environnement de test physique et sign-off indépendant.

---

# IAMINA D7 — 14 octobre 2026 — CERTIFICATION TECHNIQUE AUTOMATISÉE VERTE (exact HEAD)
 
**Goal** : profil médical progressif facultatif, multi-traitements déclarés sans inférence, isolement strict patient, outbox offline/CAS et refus des écritures concurrentes non versionnées. **Succès CI** : 17/17 workflows GitHub SUCCESS, **0 échec, 0 run actif** sur le commit fonctionnel exact `46a530f64215d00afe72bdd22eea88f365d72097`, vérifié après la fin des runs. Aucun merge ni déploiement.
 
**Preuve principale** : [CI #38567600156](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38567600156) **6/6 jobs SUCCESS** ; SQLite **2810 passed / 5 skipped / 3 xfailed / 121 subtests**, PostgreSQL **2814 passed / 1 skipped / 3 xfailed / 121 subtests**, Flutter **772 passed / 1 skipped**, `✓ Built build/web`. Ne pas compter skipped/xfailed comme pass. Il s'agit de la validation sur `46a530f64215d00afe72bdd22eea88f365d72097`, pas d'un autre SHA.
 
**Preuves complémentaires** : [D7 Conflict UI Evidence #38567600218](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38567600218) SUCCESS (génération vérifiée de 18 captures widget synthétiques FR/EN/AR aux 3 tailles, non équivalentes à un navigateur authentifié) ; app-lock TD-014, PWA offline/recovery/persistence, captures Chrome génériques, iOS/mobile packaging, migration drift, golden geometry, parcours P5-5 = SUCCESS au même SHA.
 
**Sécurité corrigée et couverte** : `PATCH /api/v1/profile` avec `treatment_declaration` et sans précondition CAS -> HTTP **428** sans mutation ; révision obsolète -> 409 ; forme malformée -> 422 ; requête versionnée correcte -> 200. Les PATCH legacy sans déclaration ne sont pas soumis à CAS. Tests HTTP A/B synthétiques, SQLite et PostgreSQL tous verts. Le test D9 d'accès existant n'impose pas un diagnostic ou un traitement pour terminer le premier accueil : champs médicaux facultatifs.
 
**Validation UI partielle** : les premières captures Ahem étaient illisibles, remplacées par des polices Latin/Arabic système et 18 PNG inspectées. Les textes et CTA sont majoritairement lisibles, sans overflow manifeste au widget-test, mais certaines icônes sont substituées et **la vraie boîte de dialogue distante 409 n'a pas été comparée dans Chrome réel**. Aucun score visuel final ni approbation humaine inventés.
 
**Décision / HUMAN GATES** : **D7 PRODUIT RESTE OPEN**, PR [#986](https://github.com/hraaaaf/IAMINA-MVP/pull/986) DRAFT. Restent *deux appareils physiques* avec comptes synthétiques A→B→A + offline/retry/409 et état serveur, validation sécurité/privacy clinique indépendante, arbitrage consentement de synchronisation versionné et dépendances D30 #988/#989/#990, BEFORE/AFTER réel du dialogue et approbation visuelle clinique/UX. **Aucun merge, aucun Vercel, aucune donnée patient réelle** tant que non prouvé.
 
**Prochaines actions** : réconcilier et recertifier toute nouvelle divergence de `main` ; compléter les preuves appareils/UI et audits indépendants ; seulement après feu vert humain envisager merge/post-merge. Baseline P5 roadmap historique **6/12 = 50 %**, non recalculée ici.
 
**Historique ci-dessous** : les statuts « pending », « candidat non certifié » et SHA antérieurs sont historiques. La certification 17/17 ci-dessus est celle du code `46a530f64215d00afe72bdd22eea88f365d72097`.
 
---
 
# IAMINA D7 — 14 octobre 2026 — Intégration D9 GET A→B→A (TEST-ONLY)

**Périmètre strict IAMINA** : PR #986 DRAFT, master non modifié. Avant intégration, D7 code HEAD `1a6d0f3da0b79fab1dfbd5503386b9de619f438a` contient le durcissement CAS HTTP 428, tests A/B et correction de fixture directe. Main alors courant `563766b35c7b28b86330a7d6987a9c86a738d794` ajoute uniquement `backend/diabetes/tests/test_d9_existing_account_profile_read.py`. Ce test exige par vrai bearer synthétique isolation GET A→B→A, fraîche instance HTTP et profil médical facultatif ; il ne prétend pas valider une récupération de coffre Flutter depuis un deuxième appareil physique.

**Action préparée** : merger ce seul fichier test D9 dans la branche D7 et confirmer derrière=0 ; mêmes comportements code D7 inchangés ; exigences de test supplémentaires, pas de fusion dans main. CI sur nouveau HEAD obligatoire après tout merge ; ne pas réutiliser les verts des anciens HEAD.

**Preuves visuelles de référence** : workflow D7 ciblé `38566577425` SUCCESS sur `73d5c829…`, artifact PNG #11895886103, 18 captures réelles de widget-test avec fontes Latin/Arabic, scène de section fermée / déployée inspectée à 390×844 / 768×1024 / 1280×900 FR/EN/AR. Les titres et CTA sont majoritairement lisibles, sans dépassement évident dans les captures ; quelques icônes Flutter et header mobile utilisent encore des glyphes substitutifs. **Pas de screenshot de la vraie modal 409 ni de preuve Chrome/PWA authentifiée du conflit ; score non attribué**.

**Next exact** : relire les 17 workflows de certification exact HEAD ; vérifier 428 sans mutation en SQLite et PostgreSQL, 767+ tests Flutter et 18 screenshots ; si rouge corriger puis re-certifier. Puis vrai human gate : tests A→B→A/offline/409 sur deux devices physiques, versionnement/consentement sync D30, revue security/clinician et validation UI humaine. No merge/no Vercel/no patient réel ; P5 historique 6/12 = 50 %.

---

# IAMINA D7 — 14 octobre 2026 — durcissement de la précondition CAS (CANDIDAT NON CERTIFIÉ)

**PR #986 OPEN/DRAFT, AUCUN MERGE / VERCEL / PATIENT RÉEL.** Référence avant ce correctif : fusion de main D9 et capture en fontes lisibles sur `f557795df1c0003fac43a45ec243577b5cb8c77d`; ses 17 workflows ne certifient PAS ce nouveau changement.

**Goal** : interdire tout `PATCH /api/v1/profile` qui inclut `treatment_declaration` sans `X-Iamina-Treatment-Expected-Updated-At`. En l'absence d'en-tête => **HTTP 428** ; valeur `none` si aucune révision distante, ou timestamp TZ de la version lue ; révision obsolète => 409, invalidité => 422. **PATCH de préférences historiques sans déclaration reste admis** sans CAS. Risque visé : écrasement concurrent ; aucun comportement médical ou dose modifiés.

**BEFORE prouvé par code** : backend ne vérifiait la précondition que si le client la soumettait. Tests directs/HTTP historiques créaient des déclarations sans header. Pas d'incident réel observé.

**Implémentation candidate** : garde fail-closed HTTP 428 avant mutation ; tests directs ajustés à `none` puis révision serveur actualisée ; test HTTP A/B authentifié garantit refus création et écrasement sans header, aucune mutation, et succès avec révision exacte ; test legacy sans déclaration. Suite : CI exact HEAD SQLite/Postgres + Flutter puis sécurité indépendante. Aucun contournement bearer ni changement sync/consentement.

**Visuel** : aucune modification de production. Correction de captures Flutter test D7 (chargement polices latines/arabes) sur parent `f557795d…`; workflow et inspection sur dernier HEAD requis. Les 18 premières images Ahem ne prouvent pas la lisibilité.

**Gates** : essais A→B→A physiques/offline/409, consentement versionné D30, vrai dialogue 409 en Chrome, audit indépendant privacy/clinique et validation UI humaine. NO MERGE/NO VERCEL. Avancement global historique P5=50%.

---

# D7 — 14 octobre 2026 — diagnostic ciblé des débordements mobiles (sans relancer 759 tests)

**PR #986 reste DRAFT, PAS DE MERGE / VERCEL.**

**BEFORE + preuve factuelle :** sur `cf3c781145850353d0408bf96a4269b4d3c0311d`, CI principale #38545364529 Flutter **759 pass, 3 fail, 1 skip** ; les mêmes cas mobile 390×844 FR (+114 px), EN (+82 px), AR (+94 px) ont échoué malgré le bouton CTA à retour à la ligne. Backend SQLite/PostgreSQL et les 15 autres workflows SUCCESS. Le CTA n'était donc pas la cause. La correction précédente ciblait le mauvais widget.

**Diagnostic minimal réel exécuté :** branche isolée `debug/d7-mobile-overflow-20261014` sans PR, workflow dédié `.github/workflows/d7-only-mobile-red.yml`, déclenché seulement par push sur cette branche et exécutant `flutter test --reporter expanded --name '390x844' test/features/profile/d7_conflict_cta_responsive_test.dart` : **uniquement les 3 rouges**. Run diagnostic [#38546806644](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38546806644), FAIL attendu, avec dump du RenderTree. Le `RenderFlex` OVERFLOWING est en réalité la `Row` de `_buildSectionTitle` dans `profile_screen_presentation.dart`, devant texte FR `Cible glycémique (mg/dL)` : contrainte de ligne **304 px**, `RenderParagraph` intrinsèque **390 px**, icône 20 + espacement 8 → +114 px exact. EN/AR même défaut localisé dans la même Row.

**GOAL** : toutes les sections médicales conservent titres lisibles et sans overflow en FR/EN/AR au viewport 390×844 sans raccourcir le texte ou diminuer la police ; aucun changement de métier, confidentialité, serveur, outbox/CAS.

**MOCKUP/layout cible** : icône fixe (20 px), écart 8 px, titre `Expanded(Text(softWrap:true))` dans la largeur restante (276 px sur 304), texte multi-ligne si nécessaire ; même header hors mobile et RTL.

**IMPLÉMENTATION candidate** : remplacer uniquement le `Text(title)` non contraint dans `_buildSectionTitle` par `Expanded(child: Text(title, softWrap:true,...))`; le reste de l'interface, du CTA et des tests 10 cas restent identiques. Branche diagnostic commit `39774dd219c518488d9d626f08d14e538a00f7bb`, run de **3 tests seulement** [#38547036442](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38547036442). **RÉSULTAT CERTIFIÉ** : run ciblé #38547036442 job #115795537431 **SUCCESS**, journal `flutter test --reporter expanded --name '390x844' test/features/profile/d7_conflict_cta_responsive_test.dart` : FR +1, EN +2, AR +3, `All tests passed!`, aucune erreur. Correctif minimal vérifié AVANT l'intégration à PR #986. Un seul commit et une seule CI complète doivent ensuite vérifier la non-régression globale.

**AFTER** : les 3 cas ciblés doivent passer d'abord ; captures et comparaison BEFORE/AFTER sur 390×844, 768×1024, 1280×900 spécifiques au conflit 409, score visuel seulement avec preuves ; essais sur deux appareils réels, revue clinique/privacy, consentement et validation humaine toujours à réaliser. Ne jamais clôturer D7 ni mer﻿ger sans gates. P5 50 % historique inchangé.

---

# D7 — 14 octobre 2026 — CORRECTION D'UN VRAI DÉBORDEMENT MOBILE (HEAD précédent 96302e25)

**PR #986 DRAFT — D7 TOUJOURS OUVERTE, NI MERGE NI VERCEL.** Ceci est un correctif visuel non certifié avant le prochain run GitHub.

**BEFORE / preuve rouge HEAD** `96302e2588b97a9b979f8ff4a1b7b38d38023dd7` : [CI #38544063497](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38544063497) : SQLite et PostgreSQL SUCCESS, Frontend FAIL `759 tests passed, 3 failed, 1 skipped` ; les 3 échecs sont le **RenderFlex overflow à 390×844** après expansion du Profil médical, sur `d7-resolve-treatment-conflict` : FR +114 px, EN +82 px, AR +94 px ; les tailles 768×1024 et 1280×900 réussissaient. Log job Flutter `115786704547`. Plusieurs autres workflows hors CI sont SUCCESS, UI browser screenshot encore en cours au premier contrôle de ce lot. Cela révèle une régression UX réelle : le label long de `OutlinedButton.icon` ne pouvait pas revenir à la ligne dans la largeur mobile.

**GOAL observable :** bouton de réconciliation visible/entièrement dans le viewport mobile, label intact et lisible dans FR/EN/AR sans réduction arbitraire de police, RTL respecté, même action clinique explicite et aucune mutation lors d'une simple consultation. Aucun changement à CAS/back-end, app-lock ni à la logique de sauvegarde.

**MOCKUP / cible de layout :** bouton largeur disponible sur une ligne de container, icône de conflit (~20 px) + espacement (~8 px) + libellé flexible centré pouvant prendre deux lignes ; pas de texte tronqué, ni de CTA masqué.

**IMPLÉMENTATION de ce lot :** `frontend/lib/features/profile/profile_screen_presentation.dart` remplace `OutlinedButton.icon` par `SizedBox(width: double.infinity) → OutlinedButton → Row(Icon + SizedBox + Expanded(Text(softWrap:true)))` pour le **seul CTA D7** ; `frontend/test/features/profile/d7_conflict_cta_responsive_test.dart` conserve les neuf tests réels avec patient synthetic `conflict` et assertion `tester.takeException() isNull`, ajoute les bornes géométriques (`left ≥ 0`, `right ≤ viewport width`, hauteur ≥40) aux viewports **390×844, 768×1024 et 1280×900** × **FR/EN/AR**, et 1 test `pending` sans CTA. **CI de ce nouveau HEAD obligatoire, non encore prouvée.**

**AFTER / score visuel :** à établir par nouvelle CI et captures spécifiques de l'état de conflit aux mêmes viewports ; un test widget ne remplace pas une comparaison screenshot BEFORE/AFTER. Aucun score attribué avant captures.

**Next exact :** valider les 10 tests dans la nouvelle CI; si 390 encore rouge, diagnostiquer tree Flutter, corriger sans enlever les tests. Ensuite capturer/valider dialogue clinique 409, vérifier A→B→A sur deux terminaux réels/offline/409 et audits indépendants clinique/privacy, obtenir feu vert humain avant fusion. P5 historique 50 % inchangé.

---

# IAMINA D7 — ÉTAT CANONIQUE AU 14 OCTOBRE 2026 — TESTS AUTOMATISÉS VERTS

**NE PAS CONFONDRE « CI VERTE » ET « CERTIFICATION CLINIQUE/UX ». D7 OUVERTE — PR #986 DRAFT, NI MERGE NI VERCEL.**

**Goal exact** : profil médical optionnel à choix multi-traitements déclarés par le patient ; serveur Django avec CAS strict, offline outbox + récupération/sauvegardes, isolation A→B→A, app-lock empêchant sorties réseau cliniques, conflit 409 explicitement comparé/résolu avec consentement du patient.

**Dernier HEAD complet VALIDÉ** : [`ac902f091e275f3c066918705b02e7c9f387eda2`](https://github.com/hraaaaf/IAMINA-MVP/commit/ac902f091e275f3c066918705b02e7c9f387eda2), PR [#986](https://github.com/hraaaaf/IAMINA-MVP/pull/986). [CI #38542149288](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38542149288) = **6/6 jobs SUCCESS** (ruff + pytest SQLite, PostgreSQL source-of-truth, Flutter analyze/tests/PWA, secrets/scope/taille). **16/16 workflows SUCCESS** : P5-5, P5-4A offline shell/browser persistence/update-recovery, iOS/mobile, TD-014 app-lock, Django drift, golden geometry, First-use/mobile, login/local-first, Chrome CTA, UI browser screenshot/navigation. [PWA update/recovery #38542149097](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38542149097) SUCCESS, la précédente erreur Chrome 9225 ne se reproduit pas. Le test Flutter local-first a été réparé de manière ciblée sur `_saveProfile()` dans `ac902f09` (pas de modification runtime).

**Matrice de preuves au HEAD ac902** :
- Déclaration médicale multi-code, états absent/unsure/none/later, génération CAS, conflits 409, sauvegarde v11→v12, tests de migration et refus de vieux ACK : **tests CI verts**. Ce n'est pas un essai réel multi-appareils.
- App-lock : gardes `AuthInterceptor`/`RetryInterceptor`, HTTP directs, SSE et token tardif ; tests et TD014 verts. Pas de preuve de retrait d'une requête déjà partie avant verrouillage (impossible côté navigateur).
- Isolation A→B→A et offline : simulations sur deux coffres SQLite physiques + retry serveur validées en CI. **Deux terminaux physiques/OS et comptes réels non testés**.
- Visuels : workflow UI browser screenshot SUCCESS, artéfacts GitHub `iamina-ui-browser-cert-390x844`, `iamina-ui-browser-cert-768x1024`, `iamina-ui-browser-cert-1280x900` rattachés au run [#38542149177](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38542149177). **Ces captures générales n'établissent PAS une comparaison BEFORE/AFTER du dialogue D7 conflit 409.**
- Nouvel écran de conflit D7 : section CTA conditional `d7-resolve-treatment-conflict` si statut 409, boîte locale/distante trilingue, confirmation choisie et méthode de comparaison de génération ; tests backend/store verts, mais **certification spécifique de la scène 409 manque encore**.

**LOT DE PREUVE UI PRÉPARÉ DANS LE PROCHAIN COMMIT** : `frontend/test/features/profile/d7_conflict_cta_responsive_test.dart` ajoute **10 tests widgets** : neuf tailles/langues [390×844, 768×1024, 1280×900] × [FR, EN, AR] avec vraie déclaration de traitement en état `conflict`, vérification présence CTA sans exception de layout, et absence de mutation/ACK en consultation ; dixième test vérifie absence de CTA si `pending`. **Ce lot n'est PAS validé par la CI ac902** : identifier prochain HEAD, puis run et logs.

**UI/UX protocole** : BEFORE : profil sans action de réconciliation ; cible/micro-mockup : CTA « Comparer et résoudre le conflit », dialogue côte à côte logique appareil/serveur + avertissement + « Annuler / Conserver ma version », aucun ACK avant accord ; AFTER : compare captures de l'état 409 à viewports identiques 390×844, 768×1024, 1280×900 et contrôle FR/EN/AR/RTL/clavier/a11y. Les tests widgets de rendu seuls NE SONT PAS des captures comparées : score visuel NON NOTÉ, ne pas inventer.

**Gates indispensables non franchis** : revue confidentialité/consentement et sécurité clinique indépendante ; scénario A→logout→B→A sur deux appareils réels (récupération et offline/409) ; preuve visuelle comparée de l'état conflit ; approbation UI et clinique du responsable. **Ne pas fusionner #986 ni déployer Vercel** sans gates. P5 roadmap global 50 % HISTORIQUE inchangé, ne pas inférer un nouveau %. Aucun action irréversible à exécuter automatiquement.

**Next exact** : publier les tests widgets en commit unique, vérifier CI du HEAD ; si rouge diagnostiquer et corriger. Puis captures UI avant/après à partir d'un environnement capable de rendre la scène conflit et faire valider par humain, audits clinique/privacy, 2 vrais appareils, et seulement ensuite discussion merge/deploy.

---

# REPRISE D7 — 14 octobre 2026 — fermeture des réponses HTTP tardives

**D7 EN COURS — PR #986 DRAFT, NI MERGE NI VERCEL.**
**Dernière preuve intégralement verte :** HEAD `56aa31a948d3d2fcddbde58f1237f7ecebe84756`, [CI #38487824691](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38487824691) **6/6 jobs et 16/16 workflows SUCCESS**. Les HEADs `f790b51b` (horodatages serveur), `3550ce7c` (routes médicales et coffre device-only) et `db792fad` (conflit 409 UI + CAS explicite) **ne sont pas certifiés par ce vert**. [CI du HEAD db792fad #38537317205](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38537317205) QUEUED au premier contrôle. Ne pas déclarer clôture avant CI complète du HEAD ultime.

**Goal du lot courant** : aucune consommation de réponse médicale d'une session expirée, après relock/app switch. **Implémentation ajoutée depuis db792fad dans `frontend/lib/services/api_client.dart`** : les cinq appels HTTP directs (SSE IA/chat, voice, photo de glucomètre, transcription, ingest de document) capturent l'AuthEpoch au départ et le revérifient après réception des octets, avec `requireUnlockedPatientSyncTransport(uri,...)` ; le SSE vérifie également chaque chunk et chaque token avant exposition. Ces gardes complètent les gardes déjà vérifiées au moment de `send()` ; les requêtes déjà parties avant verrouillage ne peuvent pas être physiquement rétractées. **Cet ajout n'est pas encore certifié en CI.**

**D7 fonctionnalités maintenant implémentées mais devant passer la CI du HEAD final :** choix patient multi-traitements optionnels ; coffre SQLite isolé A/B ; outbox et CAS Django strict ; restauration nouvelle device et backup v11→v12 ; traitement d'erreur et non-fabrication d'ACK ; garde Chopper et HTTP direct ; session révoquée mais UUID de coffre local récupérable derrière app-lock ; résolution de conflit 409 sur choix explicite avec relecture distante, bouton si `conflict`, SQL compare-generation, message d'absence de confirmation.

**QA visuelle D7 — obligatoire et NON achevée :** avant : sélecteur sans résolution ; cible : CTA conditionnel « Comparer et résoudre le conflit » et boîte FR/EN/AR montrant choix local/distant, avertissement du remplacement distant, boutons Annuler / Conserver ma version ; après : screenshot aux viewports `390×844`, `768×1024`, `1280×900`, comparaison avec BEFORE, contrôle accessibilité/RTL/clavier, score visuel et revue humaine. Pas de score inventé.

**Autres gates réels** : tests sur deux appareils et comptes de test réels A→logout→B→A, offline/409 et reprise multi-devices ; privacy/consentement et sûreté clinique revues indépendamment par experts et responsables habilités. Ne pas déployer Vercel ni fusionner en absence des preuves. P5 historique 50 % inchangé.

**Next exact** : contrôler workflows/jobs CI du prochain HEAD, corriger bugs observés, compléter preuve UI et tests réels si infrastructure disponible, recueillir validations humaines requises. **Ne pas poll CI.**

---

# D7 — 14 octobre 2026 — dernier lot de réconciliation clinique (PR #986 DRAFT)

**Goal** : rendre un conflit de déclaration médicale visible et récupérable sans perte, jamais choisir à la place du patient. **Succès observable** : vue locale et distante comparées, action humaine explicite, CAS basé sur dernière révision, aucune écriture serveur sans choix ; confirmation uniquement après ACK. **Preuve** : test SQL de génération, CI Flutter/backend du HEAD courant, captures comparatives et validation clinique.

**Base prouvée :** HEAD `56aa31a948d3d2fcddbde58f1237f7ecebe84756`, CI #38487824691 **16/16 workflows verts**, 6/6 jobs CI. Les commits suivants `f790b51b` (horodatage GET) et `3550ce7c` (sécurité toutes routes patient + récupération d'identité local-only) ne sont PAS couverts par cet historique. CI [#38536308029](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38536308029) sur 3550ce7c **QUEUED** au dernier contrôle ; ne pas annoncer un vert non prouvé.

**NOUVEAU LOT PRÉPARÉ À COMMITTER :** une méthode `PatientTreatmentDeclarationStore.retryConflictAfterExplicitReview(expectedGeneration,currentServerRevisionUtc)` est conditionnée par SQL au statut `conflict` et à la génération locale, et ne modifie JAMAIS les codes/état ; place seulement `pending` et avance le CAS et la génération. Le test protège contre la génération obsolète, le faux ACK et le second rattrapage. `ProfileScreen` repère `sync_status=conflict`, propose une comparaison bilingue/trilingue locale/distante, vérifie provenance, version, codes et timestamp TZ sur GET, puis ne relance le synchroniseur qu'après sélection explicite « Conserver ma version » (avec avertissement que la version distante pourra être remplacée). Annuler ne change rien ; app-lock/authEpoch et retour de réseau sont revérifiés.

**UI/UX — séquence obligatoire :**
- **BEFORE observé dans code précédent** : sélecteur de traitement et snackbar d'échec réseau, mais pas d'action utilisateur pour traiter un conflit 409 ; capture visuelle baseline spécifique état 409 NON acquise.
- **GOAL** : résolution non destructive et consentie, compatible mobile FR/EN/AR.
- **MOCKUP FONCTIONNEL** : sous le sélecteur : `[Comparer et résoudre le conflit]`; après ouverture : `Conflit de synchronisation` + `Sur cet appareil : [choix]` + `Sur votre compte : [choix]` + note de remplacement explicite + `[Annuler]` / `[Conserver ma version]`. Le bouton est bloqué en cas de changements UI non encore enregistrés.
- **IMPLÉMENTATION** : 4 fichiers Flutter/Drift + test de stockage, à certifier après commit.
- **AFTER restant** : captures réelles BEFORE/AFTER mêmes viewports `390×844`, `768×1024`, `1280×900`, vérification accessibilité/navigation/clavier/RTL et score visuel ; ne pas attribuer 10/10 sans preuves.

**Risques / human gates** : requête envoyée avant app-lock impossible à retirer après départ ; résolutions 409 répétées si autre appareil modifie entre GET/PATCH restent bloquées, jamais silencieuses. Test sur deux appareils physiques, clinique/privacy indépendante, validation UI humaine et consentement explicite à la fusion nécessaires. **Aucun merge, aucun Vercel**, P5 50 % historique inchangé.

**Next exact** : vérifier le HEAD poussé et sa CI ; lire erreur concrète si rouge et corriger ; réaliser preuve visuelle conflict-state par captures ; revue clinique/privacy ; obtenir gate humain puis merge/post-merge seulement si tous tests verts.

---

# D7 — PRIORITÉ DE REPRISE — 14 octobre 2026 : durcissement transport + coffre local

**PR #986 DRAFT, D7 NON CLOSE, aucun merge ni Vercel.** Ce bloc précède les statuts historiques ci-dessous.

**Goal** : déclaration multi-traitement sous coffre patient isolé, récupération offline, CAS sans fausse confirmation, aucun envoi clinique après fermeture d'app-lock, consultation médicale non activée sans validation clinique ; validation de l'UX aux mêmes viewports.

**Dernier vert intégral certifié** : HEAD `56aa31a948d3d2fcddbde58f1237f7ecebe84756` [CI #38487824691](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38487824691) **6/6 CI et 16/16 workflows SUCCESS**, tests A→B→A sur 2 DB SQLite isolées et reprise offline simulée compris.

**HEAD précédent** : `f790b51b1303aacff2f22e38e2383439aae64ae8` sur PR #986, test de refus du timestamp serveur sans timezone pour restauration. [CI #38535368012](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38535368012) **QUEUED au premier contrôle du 14/10/2026**, pas de preuve verte sur cette version.

**NOUVEAU LOT EN VOIE DE COMMIT (vérifier HEAD réel GitHub pour preuve) :**
- `api_client.dart` : garde `requireUnlockedPatientSyncTransport` appliquée à **toutes les routes /api/v1/** sauf `/api/v1/auth/*`, plus seulement profil/logs. Cela couvre AI/chat, KPIs, personal response, documents, consentement, demo seed et toutes routes dynamiques. Les 5 appels HTTP directs `chatStream`, audio voice/transcribe, photo de glucomètre et document ingest utilisent `readForStableAuthEpoch` et la garde immédiatement avant `send()`. Login/password reset non bloqués. `main.dart` autorise seulement les tests audit loopback explicitement autorisés en cas de lock (callback `auditAllowed || appLock.isUnlocked`). Test de 12 chemins patients refusés + login/récup autorisés.
- `auth_service.dart` : `signOut` invalide toujours immédiatement l'epoch et les sessions, mais **ne supprime plus l'identifiant stable du coffre local** qui aurait orpheliné les soins hors ligne ; le coffre n'est PAS accessible tant que local enrollment n'a pas été refait et app-lock déverrouillé. `dormantDeviceVaultForProtectedStateProbe` permet de sonder une ancienne DB pour empêcher un reset app-lock qui considérerait à tort l'installation vide ; `main.dart` l'emploie uniquement dans le probe fail-closed.
- `auth_service_local_first_test.dart` : tests de signOut révoquant la session en conservant l'identifiant, et test de ré-enrollment récupérant exactement le nom de coffre initial sans réseau. **Toute confidentialité exige que le véritable app-lock soit configuré et actif : tests d'intégration sur appareil réel restant.**
- **Ces modifications ont besoin de CI sur le HEAD qui les porte.** Ne pas extrapoler le vert précédent, ni confondre un source-level invariant avec la certification d'absence totale de fuite en vol (requêtes déjà dispatchées avant lock).

**Reste après vert** : tester flux complet A→logout→B→A avec vrais identifiants serveur et deux appareils, limites réseau/cancel et conflits 409 ; revue clinique/confidentialité externe ; preuves UI BEFORE→cible→AFTER (390×844, 768×1024, 1280×900), score visuel puis gate humain. Pas de nouveau déploiement Vercel sans autorisation. P5 = **50 % historique**, inchangé.

**Next exact** : constater SHA HEAD, valider CI correspondante, corriger tout rouge, étendre tests si un bypass découvert, confirmer artefacts UI et privacy puis attendre seulement vrai gate humain.

---

# REPRISE D7 — 14 octobre 2026 — mise à jour après CI VERTE et test d'isolation

**PR #986 DRAFT, NON MERGED, NO VERCEL. D7 NON CLOSE.** Le prochain opérateur doit vérifier le HEAD/CI avant de poursuivre.

**Goal** : coffres patient isolés, traitements déclaratifs multi-choix, synchronisation CAS + offline sans perte de données, sécurité app-lock, réconciliation explicite, contrôle clinique/privacy et UX certifiée.

**Preuve dernière CI entièrement verte** : commit [`6ce3cf63ddbf4552574bb90511b23a3a312b8bf3`](https://github.com/hraaaaf/IAMINA-MVP/commit/6ce3cf63ddbf4552574bb90511b23a3a312b8bf3) / [CI #38487298188](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38487298188) **6/6 JOBS SUCCESS** : backend SQLite, PostgreSQL, frontend Flutter analyse/tests + PWA, contrôles Git/sécurité. Autres certifications du même commit partiellement `in_progress` au relevé, NE PAS extrapoler 16/16.

**HEAD suivant prouvé poussé** : [`56aa31a948d3d2fcddbde58f1237f7ecebe84756`](https://github.com/hraaaaf/IAMINA-MVP/commit/56aa31a948d3d2fcddbde58f1237f7ecebe84756), PR #986 DRAFT. Tests uniquement : patient A→B→A par vrais fichiers SQLite distincts (traitement de B ne traverse pas vers A; déclaration A reste pending intacte), outbox après upload indisponible puis confirmation sur retry sans modifier génération/choix. **CI du HEAD** [#38487824691](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38487824691) **QUEUED au relevé** ; migrations et géométrie déjà SUCCESS, autres certifications encore running/queued. Pas encore prouvé que les nouveaux tests passent.

**Travail indépendant PRÉPARÉ mais non commité** : arbre Git `a7bf5ef5c651990c1e0c373461823ff64880a6bd` parent `56aa31a9`, `frontend/lib/services/sync_service.dart` utilise désormais `verifiedServerTreatmentRevision(profile)` au lieu de `DateTime.tryParse(timestamp)` pour restauration distante ; ceci refuse un timestamp sans timezone comme faux ACK de serveur. Nouveau test dans `frontend/test/services/sync_service_test.dart` confirme qu'un profil distant avec horodatage naïf ne crée aucune déclaration locale. **NON TESTÉ, NE PAS COMPTER LIVRÉ.** Après résultat CI de 56aa31 : commit de l'arbre préparé si HEAD inchangé et code revu ; sinon rebase.

**Risque non résolu :** véritable cycle sur deux appareils (backend Django+client), coupures réseau et 409 réalistes, déconnexion/récupération coffre device-only, revue confidentialité + sûreté clinique, réconciliation conflit, captures AVANT/APRÈS aux mêmes 390×844/768×1024/1280×900 et gate de validation humaine. Aucun merge ni déploiement Vercel sans gate explicite. P5 50 % historique non recalculé.

**Next exact :** conclure CI #38487824691 pour HEAD 56aa31, traiter failure si présente ; si success pousser garde timestamp + test, certifier sa nouvelle CI, puis suivre le reste de la séquence jusqu'aux vrais human gates. Interdiction de polling/sleep et de déclarer terminé sans preuve.

---

# D7 — ÉTAT DE REPRISE AU 13/10/2026 23h+ UTC — PR #986 DRAFT

**D7 OUVERTE : NE PAS MERGER, NE PAS DÉPLOYER VERCEL.** Lire cette section avant les historiques ci-dessous.

**Goal** : profil médical facultatif et traitements multiples purement déclaratifs, sous coffre physique isolé par patient, avec reprise offline, serveur Django CAS, consentement, app-lock et aucune inférence clinique non validée D19. **Preuve de succès exigée** : CI du HEAD exact, A→logout→B→A, deux appareils, 409 + reprise réseau, données restaurées sans erreurs de propriété/ACK, protection app-lock par vrai interceptor, revue clinique/privacy et BEFORE→mockup→AFTER UI aux viewports 390×844, 768×1024, 1280×900.

**Dernier HEAD vérifié avant commit documentaire :** `bb43cbd16d47305726aef6ffd86e92f924fa13d3` ; CI principale [#38486422869](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38486422869) **6/6 jobs SUCCESS** (backend SQLite/Postgres, Flutter analyse/tests/build, secret/scope/size). 15/16 workflows SUCCESS, seul **Pilot iOS packaging IN_PROGRESS** au dernier contrôle ; ne pas annoncer 16/16. PR [#986](https://github.com/hraaaaf/IAMINA-MVP/pull/986) reste brouillon, base main `a6284c4c`. **Ce vert ne couvre pas les modifications supplémentaires décrites ci-dessous.**

**Nouveau lot préparé pour commit après CI verte** : `frontend/lib/data/drift/local_backup.dart` tolère dorénavant les exports **scopés D7 v11 vers destination v12**, mais restaure leurs déclarations comme **pending**, baseline serveur null, génération locale 1, sans inventer de réception réseau ; refuse de restaurer une ancienne sauvegarde si une déclaration existe déjà dans le coffre de destination ; n'élargit pas les règles de provenance/patient. Tests ajoutés : v11 → v12 conservant choix, rejet d'une deuxième tentative, refus du v11 tronqué. `frontend/test/services/d7_app_lock_chopper_boundary_test.dart` (nouveau) exerce les vrais `AuthInterceptor` et `RetryInterceptor` via fausse chaîne Chopper sans réseau : verrouillage pendant attente bearer bloque tout dispatch ; auth/login reste accessible ; verrouillage pendant rafraîchissement 401 et après 503 empêche la seconde requête. **Ces nouveaux tests nécessitent CI ; ne pas déclarer réussite sans preuves.**

**Risque encore ouvert** : autres API médicales non toutes couvertes par garde app-lock transport D7 ; tests sur appareil/versions OS absents ; politique de signout du coffre device-only à auditer ; conflit multi-device persistant sans UI de réconciliation explicite ; traitement de données cliniques et consentement à revoir ; nouvelles preuves visuelles comparatives aux trois viewports et gate humain non acquises.

**Next exact** : relever le HEAD de la PR et le CI associés au nouveau lot ; si rouge, lire l'erreur job et corriger ; si vert, compléter preuves de sécurité réseau étendues, A/B sur deux appareils et offline ; BEFORE/AFTER, revue indépendante clinique/privacy, validation humaine puis seulement merge/post-merge sous conditions. P5 **50 % historique**, inchangé.

---

# REPRISE PRIORITAIRE — D7 — 13 octobre 2026, après CI SQLite/Postgres/Flutter verte

**D7 OUVERTE — PR #986 DRAFT NON FUSIONNÉE — aucun Vercel. Ce bloc est plus récent que les statuts archivés ci-dessous.**

- **Goal** : déclaration des traitements strictement facultative, patient-owned, versionnée, sans suggestion médicale implicite ; sync CAS/ACK, coffre local isolé, restauration sur autre appareil, offline, app-lock et consentement ; garde D19 pour toute individualisation clinique.
- **Dernier HEAD dont la CI principale est prouvée verte** : `f03c1f7933d5d45f47fdd52bec42d1e6d89564ab`, [run #38485886873](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38485886873) **6/6 jobs SUCCESS** : SQLite, PostgreSQL, Flutter analyze/tests/build et 3 contrôles ; P5-5, migrations et PWA également verts. Plusieurs workflows visuels/iOS encore IN_PROGRESS au contrôle, ne pas extrapoler 16/16.
- **Correctif f03 livré/testé** : six tests migration Drift v12 + test refus sauvegarde v10 obsolètes corrigés ; `LocalBackup` exporte/restaure état `pending/confirmed/conflict`, génération et révision CAS et valide les métadonnées avant toute transaction destructive ; 2 nouveaux tests. **CI principale SUCCESS.** La certification D7 globale reste ouverte.
- **Présent lot de sécurité (INCLUS dans le commit qui modifie ce document, PAS ENCORE TESTÉ CI)** : `ApiClient` transmet désormais une garde `canUsePatientSyncTransport` depuis `main.dart`, basée sur `appLockService.isUnlocked`. `AuthInterceptor` revérifie APRÈS `await getIdToken` et avant `chain.proceed`; `RetryInterceptor` vérifie AVANT premier egress et chaque retry 401/5xx après token/délai. Cela ne couvre que `/api/v1/profile`, `/api/v1/logs`, `/api/v1/logs/batch`; auth login/enrollment reste utilisable. Tests ajoutés : garde chemins et statut, lock pendant await bearer, retry après relock. **Pas de preuve de sûreté réseau globale ou de dispositif réel tant que CI/test de bout en bout non prouvés.**
- **Gates actifs** : CI du présent commit, multi-compte A→logout→B→A sur dispositif et nouveau device, offline/réessais/conflits, coffre device-only/legacy/consentement, captures BEFORE→cible→AFTER mêmes 390×844 / 768×1024 / 1280×900 + analyse visuelle, revue indépendante sécurité et clinique, validation UI explicite. Ne pas merger #986/#963 ni déployer Vercel.
- **Next exact** : constater CI du HEAD associé à ce présent commit ; corriger tous échecs prouvés ; certifier vraie sync multi-appareils, offline, egress app-lock et consentements, UI et avis médicaux ; seulement ensuite gate humain, merge et postmerge/closeout, puis D9.
- **Avancement global P5 : 50 % historique (6/12), inchangé.**

---

# REPRISE PRIORITAIRE — IAMINA D7 — 13/10/2026, contrôle CI et sûreté

**D7 TOUJOURS OUVERTE — STOP MERGE / STOP DEPLOY. Cette section fait foi sur l'archive historique ci-dessous.**

## Goal / succès / preuve

- **Goal** : profil médical facultatif, déclaration de plusieurs traitements en termes purement descriptifs, par patient, avec stockage local/Django et restauration réellement isolée entre appareils. Aucune personnalisation clinique sans D19 audité.
- **Succès exigé** : A→logout→B→A sans fuite/perte ; offline/online avec reprise, accusé de réception et détection de conflit, nouveau device, app-lock/epoch, consentement, FR/AR, revues indépendantes et captures BEFORE/AFTER aux mêmes 390×844 / 768×1024 / 1280×900.
- **Preuve partielle** : backend bearer + frontend sur HEAD `e065aff1e06858e5a8850c2bc2b2f10bc6e9888f`, **16/16 workflows SUCCESS** dont CI [#38471129419](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38471129419), jobs SQLite/PostgreSQL/Flutter PASS. La cause du 401 précédent était **un patch pytest autouse** dans `backend/conftest.py` (`conftest._session_aware_call`) qui rejetait le bearer de test avant `authenticate`. Fix ciblé dans `backend/diabetes/tests/test_d7_profile_http_isolation.py` sans modifier l'auth de production, et test bearer falsifié. La CI verte est vérifiée, ne pas la réattribuer au commit suivant.

## Repo / branche / CI actuelle

- **Repo :** `hraaaaf/IAMINA-MVP` ; PR [#986](https://github.com/hraaaaf/IAMINA-MVP/pull/986), `feat/v1-d7-medical-profile-relevance-20261013`, **DRAFT / non fusionnée**. Base main précédemment vérifiée : `a6284c4ca1aa0177efb6c1330099a8ac7a95b1fb`.
- **HEAD fonctionnel nouvellement commité :** [`be8d42188ab9918a8a21387fcf4688fa44ebc38a`](https://github.com/hraaaaf/IAMINA-MVP/commit/be8d42188ab9918a8a21387fcf4688fa44ebc38a) : traitement de conflit CAS **optionnel** par header `X-Iamina-Treatment-Expected-Updated-At` sur le PATCH protégé. `none` si le serveur n'a pas de déclaration ; timestamp ISO8601 TZ si snapshot existant ; sous transaction et verrou patient `select_for_update`, incohérence → 409 ; révision invalide → 422. Aucun jeton ou identité patient exposés, aucun changement d'OpenAPI (header non typé).
- **CI nouvelle du HEAD fonctionnel :** [#38473751701](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38473751701) **QUEUED au premier contrôle**, donc pas encore verte. Deux tests HTTP ajoutés : refus des mises à jour obsolètes et invalidité de la révision, avec isolation B. Vérifier à nouveau une fois les runs exécutés.
- **Autres fonctionnalités D7 non closes** : [`6b01b875`](https://github.com/hraaaaf/IAMINA-MVP/commit/6b01b8754cf1fa7ca92af9b5f3dba47b90b84b3e) GET Django sous auth epoch, restauration uniquement si le coffre **contient déjà** une ligne de profil et n'a pas de déclaration ; [`bef860df`](https://github.com/hraaaaf/IAMINA-MVP/commit/bef860df948284d08d1cc6ffd5566bd6c2095643) tests Flutter supplémentaires. Le service de sync ne transporte toujours pas la déclaration en bidirectionnel.

## Lot suivant — outbox locale et contrat Flutter CAS (en attente de validation)

- **Données locales** : [`f1d36041`](https://github.com/hraaaaf/IAMINA-MVP/commit/f1d3604134011ea0b90b13b73faf379c13a8ac93) ajoute migration additive Drift **v12** à `patient_treatment_declarations_v1` : `sync_status` (`pending` / `confirmed` / `conflict`), `base_server_updated_at`, `local_generation`. Toute ligne historique entre pending par défaut, une restauration validée est confirmed, l'ACK est limité à la génération envoyée. Tests locaux ajoutés (ACK, conflit persistant, révision restaurée).
- **Transport opt-in (NON activé dans UI de profil/onboarding)** : [`85d796b2`](https://github.com/hraaaaf/IAMINA-MVP/commit/85d796b285e7a23d7f472bdcc413926b18720a23), [`ca6dab8b`](https://github.com/hraaaaf/IAMINA-MVP/commit/ca6dab8b3e2e932d6cdd917a342df191e4209b79). `ApiClient.mirrorTreatmentDeclaration` utilise la précondition serveur `X-Iamina-Treatment-Expected-Updated-At`, refuse un HTTP 200 sans snapshot correspondant et timestamp horodaté, vérifie par GET sur 409 avant de qualifier un conflit ; `SyncService.sendPendingTreatmentDeclaration` accuse réception uniquement si génération inchangée, conserve la donnée locale en cas de 409 ou changement d'auth epoch. `refreshState` tient maintenant compte des déclarations `pending` et `conflict`. Tests de contrat et synchroniseur ajoutés.
- **Dernier HEAD de code lors de rédaction :** `ca6dab8b3e2e932d6cdd917a342df191e4209b79`. La [CI #38474854259](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38474854259) était **QUEUED** au premier contrôle : NE PAS attribuer le 16/16 précédent à ce HEAD. PR #986 toujours DRAFT non mergée.
- **Limite majeure** : le profil et l'onboarding utilisent encore `ApiClient.patchProfile` sans précondition ; `sendPendingTreatmentDeclaration` n'est pas encore invoqué par leurs événements de sauvegarde ni déclenché automatiquement. La chaîne multi-appareils n'est **PAS certifiée** et l'adoption UI doit être réalisée avec BEFORE→mockup→AFTER et tests.

## Blocages et interdits (actifs)

1. **Outbox/ack/dirty et CAS côté Flutter non implémentés** ; le header est seulement un contrat serveur opt-in et les anciens PATCH restent compatibles **mais sans précondition**. Ne PAS prétendre conflit totalement résolu.
2. **Nouveau terminal vierge non démontré** : la restauration du snapshot explicitement déclaré exige actuellement la ligne `patient_profiles` locale préalable. Aucun backfill automatique du profil clinique/legacy ni adoption de la base `amina` autorisé.
3. **État synchronisé trompeur** : `SyncService.state.upToDate` prend en compte les logs, pas les déclarations.
4. **Gates humains et preuves** : A/B complet, batterie d'échecs/offline, app-lock et consentement, captures BEFORE→cible→AFTER, revue indépendante privacy/sécurité/clinique et validation UI explicite manquent. **PR #986 et #963 : STOP MERGE** ; aucun Vercel sans consentement explicite.
5. **P5 avancement global** : **50 % historique (6/12)** inchangé tant que la roadmap canonique n'établit pas une mise à jour prouvée.

## Next exact et séquence restante

1. Vérifier CI du dernier HEAD de la branche (le commit documentaire postérieur peut superséder `be8d421`) ; sur échec, diagnostiquer/adapter code et relancer avec tests SQLite/PostgreSQL/Flutter sans réduire les protections.
2. Concevoir et implémenter outbox/dirty/ack versionnés sur coffre Drift (migration additive), client CAS avec gestion sûre des conflits (aucun écrasement silencieux), restauration d'un nouvel appareil sans fausse inférence clinique.
3. Tester A→logout→B→A, aller/retour backend, nouvelle installation, offline/retry, auth epoch au milieu de l'attente, refus invalides et accès sans jeton ; reconcilier `SyncUiState` avec le statut de la déclaration.
4. BEFORE → Goal visuel → mockup → AFTER aux 3 viewports, tests et score visuel. Revue indépendante privacy/sécurité/médical ; validation UI explicite utilisateur ; **alors seulement** examen de fusion/closeout/postmerge, puis lot D9.


---

## ARCHIVE HISTORIQUE — états antérieurs conservés ; ne pas reprendre leurs HEAD/CI comme actuels

# IAMINA — Handover D7, revue du profil médical — 13 octobre 2026

> **READ FIRST pour reprise**. État figé après vérification directe des PR/HEAD/CI GitHub au 13/10/2026. Ce document décrit l'état prouvé, pas une autorisation de merger. Ne jamais réécrire les décisions produit sans l'accord de l'utilisateur.

## Goal D7 (décision originale du 08/10, option A)

[Registre Notion des 29 décisions — D7](https://app.notion.com/p/3f377c663362812dbe78cead75e71922) : **profil médical progressif, modifiable et non bloquant**. Types : type 1, type 2, diabète gestationnel, prédiabète, autre et inconnu/préfère ne pas répondre. **Plusieurs traitements simultanés** (insuline, autres médicaments, hygiène de vie, autre/inconnu), possibilité de compléter plus tard, sans forcer la répétition du parcours (#9) ou inventer un fait clinique. Personnalisation pédagogique explicable et facultative seulement ; toute personnalisation *clinique* (cibles, alertes, conseils, triage) nécessite le moteur déterministe audité **D19**, applicabilité prouvée et validation médicale. Seuils de sécurité indépendants du style IAmina, gestion grossesse, mineurs, profil inconnu en fail-closed, confidentialité D24, cohérence FR/AR.

**Affinage utilisateur le 13/10 :** « je ne vois pas pourquoi proposer un traitement d'insuline pour un prédiabétique ! .. je veux que ce soit fait intelligemment ! ».
Interprétation produit : **ne jamais présenter l'insuline comme option usuelle recommandée au prédiabète** ; présenter en priorité les déclarations pertinentes (habitudes de vie), tout en préservant la possibilité de **signaler un traitement réellement suivi**, même inhabituel. Ne pas confondre une liste de saisie avec une prescription. Type 1 : ne jamais suggérer que l'hygiène de vie remplace l'insuline. Aucune modification de dose, de diagnostic ou de cible.

## GitHub — état EXACT vérifié

| Chantier | PR / branche / commit | État et preuve |
|---|---|---|
| D7 UX contextualisée | [PR #986 — Profil médical : traitements présentés selon le type déclaré](https://github.com/hraaaaf/IAMINA-MVP/pull/986), `feat/v1-d7-medical-profile-relevance-20261013`, **HEAD `5b05041fa9fca8164b0f79f1d3aab34e69194197`** | **DRAFT / NOT MERGED ; 9/9 workflows exact HEAD SUCCESS**, [CI #38403241359](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38403241359), [Chrome onboarding #38403241348](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38403241348). Dernier commit a corrigé test hérité de D6 ; l'ancien HEAD `67ca4004` avait une CI rouge, NE PAS confondre. |
| D7 propriétaire local | [PR #963 — preserve patient profile owner on edits](https://github.com/hraaaaf/IAMINA-MVP/pull/963), `e22f70f50fde2978f08479b6a14f8fa945bf59d8` | **DRAFT, NON MERGED**. Le guard basé sur UID Firebase ne certifie pas le cas comptes natifs A→B ni le stockage multi-comptes. [Issue D7 #962](https://github.com/hraaaaf/IAMINA-MVP/issues/962) OPEN. |
| D9 comptes existants | [PR #985 — Ne pas relancer l'onboarding pour les comptes existants (tests)](https://github.com/hraaaaf/IAMINA-MVP/pull/985), `9e8ba9e8007a4a1437ae9c09911f2c72526835ff` | **DRAFT, NON MERGED**. CI frontend test-only [#38395671766](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38395671766) SUCCESS. Ne prouve ni persistance backend, ni reprise après changement d'appareil ni migration des comptes incomplets. [Issue #966](https://github.com/hraaaaf/IAMINA-MVP/issues/966) OPEN. |
| Main | `a6284c4ca1aa0177efb6c1330099a8ac7a95b1fb` | D5 UI pays via IP/recherche [PR #984](https://github.com/hraaaaf/IAMINA-MVP/pull/984) MERGED, 8/8 prémerge + 4/4 postmerge verts ; D6 suppression du ton [PR #960](https://github.com/hraaaaf/IAMINA-MVP/pull/960) MERGED, 9/9 prémerge + 5/5 postmerge. D5 live Vercel géolocalisation non certifiée. |

**D7 exact-HEAD PR #986 : 9/9 SUCCESS** — UI browser screenshot 38403241277 ; P5-5 E2E pilot 38403241308 ; UI geometry 38403241347 ; first-use mobile visual 38403241315 ; auth local-first visual 38403241395 ; onboarding sticky CTA Chrome 38403241348 ; app-lock TD-014 38403241269 ; CI 38403241359 ; routes globales 38403241219. Ces preuves concernent le *sous-lot de présentation*, pas la totalité de D7.

## Avant / objectif / après / captures

**BEFORE `main`** : les deux écrans affichaient la même liste « Insuline / Comprimés / Hygiène seule » pour tous les diagnostics, sélection unique. Capture navigateur du parcours type 2 : [artifact BEFORE #11810642871](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38393570489/artifacts/11810642871). ATTENTION : BEFORE = type 2 avec ancienne liste générique, pas une capture du prédiabète lui-même ; la même liste est prouvée par le code commun.

**Cible / AFTER prototype** : si « prédiabète », montrer « Habitudes de vie », le lien « Je suis un autre traitement / Je préfère répondre plus tard », **ne pas montrer Insuline d'emblée**. Après clic volontaire, rendre visibles les autres déclarations dont insuline. Type 1 : insuline en première liste ; type 2 : habitudes de vie + médicaments déclarés ; gestationnel : présentation contextualisée ; autre/inconnu : pas de suggestion automatique. Libellés FR/EN/AR, aucune action clinique. Le même widget `MedicalTreatmentSelector` est utilisé dans le Profil et l'onboarding.

**Preuves AFTER** : [artifact Chrome exact HEAD #11817025825](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38403241348/artifacts/11817025825), captures initiales/étendues à **390×844, 768×1024, 1280×900**, parcours jusqu'au CTA. Comparaison mobile 3 colonnes présentée en conversation : `/mnt/data/IAMINA_D7_mobile_comparaison_390x844.png` (fichier sandbox de la session d'origine, ne pas supposer réutilisable dans une nouvelle session). Les deux AFTER sont issus de vrais Chromium.

**Gate visuel non levé** : l'utilisateur a vu la comparaison mobile mais n'a PAS encore explicitement validé la nouvelle UI D7. Il a seulement autorisé le **travail** (« vas y le D7 ! go ! »). Pour toute autre modification visuelle : BEFORE → Goal écrit → mockup → implémentation → AFTER mêmes viewports → comparaison/tests → score → **approbation UI avant merge**.

## Écarts structurels confirmés — D7 INCOMPLÈTE

1. **Traitements multiples** : le widget introduit ne sélectionne actuellement **qu'un seul `ChoiceChip`**, `PatientProfiles.treatment` dans Drift = **un seul String** ; backend Django `DiabetesProfile.treatment_type` = un seul CharField. D7 demande combinaisons, inconnus et déclarations réellement conservées. Aucun schéma multi ni migration/compatibilité certifié.
2. **Codes incompatibles** : frontend `pre` vs backend `prediabetes`. Frontend `tablets`/ `lifestyle`/ `insulin` vs backend `oral_meds`/`diet_exercise`/`insulin_pump`/`insulin_injections`/`insulin`. ATTENTION : une étiquette de UI « Médicaments déclarés » enregistrant `tablets` peut être trop large et créer une mauvaise sémantique. Exiger un **vocabulaire canonique versionné** et une migration sûre sans interpréter un traitement.
3. **Parcours non bloquant** : `OnboardingChatScreen._finish` exige diabetesType et treatment ; `ConsentService._profileCompletesOnboarding` exige également type+traitement non vides. Une valeur « unknown » peut faussement paraître profil médical complet. D7 demande pouvoir compléter plus tard, et D9 requiert une complétion ciblée pour compte existant, sans forcer tout l'onboarding. Consentement indépendant.
4. **Confidentialité / propriétaire** : `ProfileScreen._saveProfile` peut écrire `userId=1` ; onboarding utilise `firebaseUser?.uid.hashCode.abs() ?? 1` ; pour compte natif, `firebaseUser` est null tandis que `AuthService` peut détenir un token natif. `watchProfile()..limit(1)` n'est pas filtré par compte. **Risque déduit du code, pas preuve de fuite réelle.** Exiger scénario A→logout→B avec base Drift conservée, aucune lecture/écriture profil A sous B, refuser ambiguïtés, remédiation non destructive.
5. **Validation et risques cliniques** : pas de changement de cibles, doses, unités ou alertes sans audit D19, règles déterministes et revue clinique. Attention particulière type 1, gestationnel, enfants, traitements mixtes, inconnus. Backend cible conserve provenance et applicabilité distinctes ; toute mise à jour de diagnostic peut invalider une autorité clinique confirmée, ne pas supprimer cette barrière.
6. **UX Profil + localisation** : contrôles médicalement déclaratifs doivent préserver historique et résumé lisible, accessibilité tactile/clavier, RTL/arabe, états vides, persistance sur réouverture ; **aucune certification multi-device** à ce stade.

## Next exact et séquence restante

1. **Ne pas merger #986 ni #963.** Reprendre depuis ce fichier ; vérifier `main`, PR #986 HEAD, 9/9 workflows et artefacts avant de toucher au code. Demander l'approbation visuelle utilisateur uniquement quand l'AFTER final complet est conforme.
2. Concevoir/implémenter contrat clinique *déclaratif* canonique multi-traitements (compatibilité backend/Drift, statuts `not_answered` vs `unknown`, migrations non destructives, conservation du patient owner, pas de recommandation). **Goal observable** : insuline non suggérée dans premier écran prédiabète ; combinaisons enregistrées et relues exactement ; profil partiel autorisé sans perte de données.
3. Certifier l'identité native/Firebase (A→B et multi-profil dans même DB), traitement des duplications sans suppression implicite. **Gate sécurité/privacy** et, si nécessaire, revue médicale pour évolution du modèle.
4. Implémenter et tester état de complétion ciblée D7/D9 : ne pas redémarrer tout l'onboarding, compte partiel, compte complet, migration backend et nouvel appareil ; consentement jamais inféré.
5. Refaire tests backend PostgreSQL + Flutter analyze/tests/build + Chrome réel 390/768/1280 AFTER, screenshot BEFORE/AFTER même état de l'application, accessibilité et FR/AR. Corriger tous rouges ; tester adaptation clinique inchangée.
6. Présenter dossier visuel et sécurité à l'utilisateur pour validation. Après gates réels et verts : merge, readback `main`, 4+/4 postmerge pertinents, closeout issue/PR, Notion, fichier canonique ; passer à D9 revue fonctionnelle. **Ne jamais déployer Vercel sans autorisation explicite.**

## Ordre des 29 décisions et avancement

Ordre de dépendance décidé : **5 → 6 → 7 → 9 → 10 → 11 → 18 → 19 → 21 → 22 → 8 → 12 → 13 → 23 → 24 → 26 → 4 → 14 → 15 → 17 → 28 → 2 → 3 → 16 → 20 → 27 → 29 → 1 → 25**. Les décisions originales **D1/D25 CGM en dernier**. D5/D6 code livrés ; D5 métier reste avec issue #983 pour comptes existants et test IP hébergé ; D7 et D9 **non clôturées**. P5 roadmap historique **50% (6/12)**, ne pas inventer progression nouvelle ou score visuel final.

**Fichier canonique plus large** : `docs/handovers/2026-10-12-iamina-v1-29-sequential-cgm-last.md` sur branche `parallel/v1-03-ocr-ui-provenance-20261011`. L'original source de vérité pour décisions produit reste le registre Notion du 8 octobre. Si divergence document/CI, **GitHub live et les tests observés priment**. Ne pas confondre un prototype UI approuvé et un traitement médical validé.
