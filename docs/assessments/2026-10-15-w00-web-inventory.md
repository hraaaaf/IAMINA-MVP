# W00 — IAMINA Web V2 : registre de vérité et matrice D1–D29
> **Audit documentaire / code-source, pas certification runtime.** Relevé du 15/10/2026 sur `main@65bb0293cbdef1453c3c4a4b13c87b1e2fb41774`. Référence prospective unique : [docs/ROADMAP.md](../ROADMAP.md). Aucune activation réelle, autorisation clinique, déploiement ou mutation DB. Les tests et comportements Web ont besoin d'un contrôle exact SHA spécifique pour chaque lot.
>
> **Goal W00** : affecter D1–D29 aux lots W00–W14, classer les preuves Web et 86 PR ouvertes, identifier les dépendances et contradictions, produire un next exact sans faux statut. **Succès vérifiable** : 29 lignes D, index exhaustif 86 PR, principaux contrats code inspectés, état CI honnête, résolution du conflit d'ID, miroir Notion.

## 1. Base, preuves et limites
- GitHub `main@65bb0293cbdef1453c3c4a4b13c87b1e2fb41774` après [#1088](https://github.com/hraaaaf/IAMINA-MVP/pull/1088) ; comparaison main validée à l'entrée de W00. `docs/ROADMAP.md` V2 et `AGENTS.md` sont sous ce commit.
- **86 PR ouvertes au snapshot** : **70 DRAFT / 16 READY**, **54 ciblent main / 32 sont empilées**. READY signifie seulement *non draft*, jamais revue/certification. Toute PR a son propre HEAD, toute preuve ancienne est limitée à ce SHA ; un titre ne prouve rien.
- [#1085](https://github.com/hraaaaf/IAMINA-MVP/pull/1085) D3 DRAFT HEAD `e96d2e7f5f915a9ea6109e79a43eeaf24061c1cb` ; 8 workflows exact HEAD : **7 SUCCESS, CI #38802137612 FAILURE**. Échec test `frontend/test/features/dashboard_reminders_summary_card_test.dart:57` : attendu `1 rappel actif`, trouvé 0 ; 797 tests passés, 1 failed, 1 skipped. [Run](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38802137612). Aucune certification ni merge.
- [#920](https://github.com/hraaaaf/IAMINA-MVP/pull/920) audit calculs et [#921](https://github.com/hraaaaf/IAMINA-MVP/pull/921) enveloppe intelligence restent **DRAFT**, non fusionnées ; [#1071](https://github.com/hraaaaf/IAMINA-MVP/pull/1071) est empilée sur #920.
- CI [#38805258881](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38805258881) SUCCESS sur main W00-base pour documents ; frontend/backend SKIPPED car modification docs uniquement. **Ne prouve pas les fonctionnalités**.
- Le code présent est vérifié en lecture par fichiers source, **pas en navigateur courant** ; classement : **BASE** (code en main, nouveau besoin non certifié), **DRAFT** (PR candidate non fusionnée), **SCOPED MERGED** (livraison explicitement limitée), **UNKNOWN** (pas de preuve ciblée), **NATIVE DEFER** (hors cible Web). Les termes `livré Web` exigent tests, captures et comportement du lot sur SHA exact.
- Sources d'autorité : `docs/ROADMAP.md` (priorité), `docs/SPECS.md`, `docs/architecture/ARCHITECTURE.md`, `docs/LOCAL_FIRST_RUNTIME_BOUNDARY.md`, `docs/COMPANION_INTELLIGENCE_CONTRACT.md`, `frontend/lib/`, `backend/diabetes/api/v1/`, tests CI. Documentation ancienne = preuve historique conditionnelle.

## 2. Matrice intégrale de décision → lot → code/contrat → preuve/PR → prochaine vérification
| D | Lots Web | Besoin exact | Sources code/contrats lues ou localisées | Etat prouvé/limite | PR liée(s) | Next vérifiable |
|---|---|---|---|---|---|---|
| D1 | W11 | CGM Hub, connecteurs autorisés | API cgm.py + cgm_connections_section.dart + docs/architecture/ARCHITECTURE.md | base Nightscout compatible, fournisseur direct/non universel | aucune PR W11 validée | ateliers + contrat CGM, aucun hardware prouvé |
| D2 | W10 | Notifications vs rappels/compagnon | backend/diabetes/api/v1/proactive.py ; companion.py | base proactive; livraison notifications navigateur non prouvée | #949 | #949 DRAFT; livraison Web non certifiée |
| D3 | W03/W10 | Rappels Home sans repousser Tendance | dashboard_screen.dart + reminders_screen.dart | PR non fusionnée; CI échec sur test rappel | #1085 | #1085 DRAFT, CI #38802137612 FAILURE, 797 pass/1 fail/1 skip |
| D4 | W10 | Exports déterministes | reports_screen.dart ; services/local_report_pdf.dart | base PDF; demande multiformat pas certifiée | #954 | #954 CSV/JSON DRAFT, cadrer CSV/XLSX/PDF |
| D5 | W05 | Pays à l'onboarding | onboarding_chat_screen.dart ; services/country_choices.dart | base visible source; validation Web finale à faire | — | audit pays suggestions vs choix utilisateur |
| D6 | W03/W09 | Suppression sélecteur Tone | onboarding_chat_screen.dart ; tests/onboarding_stable_tone_choice_contract_test.dart | code/tests de tonalité présents; D6 non certifiée | — | inventorier écrans et supprimer choix seulement après mockup |
| D7 | W05 | Diabète et traitements adaptables | profile/medical_treatment_multi_selector.dart ; backend/diabetes/api/v1/profile.py | base code + branches D7, cohérence/sécurité à reprendre | PR D7 à réconcilier (recherche) | vérifier absence d'inférence thérapeutique |
| D8 | W04/W05 | Unité proposée puis choisie | onboarding_chat_screen.dart ; services/locale_preference_service.dart | base unité et pays, propagation non vérifiée | — | oracles conversions + choix patient avant cible |
| D9 | W02/W05 | Onboarding non répété compte existant | routes/app_router.dart ; test/v1_d9_existing_account_onboarding_gate_test.dart | code/test baselines; D9 nouvelles PR DRAFT | #995,#996,#997,#998,#1000,#1001,#1003 | restauration A→B→A + serveurs/coffres |
| D10 | W02/W05 | Récupération et app-lock | services/app_lock_authenticator_web.dart ; features/auth/app_lock_*.dart | WebAuthn en main; D10 Web coffre chiffré/récupération non prouvés | #1062 natif iOS = DIFFÉRÉ | valider Web storage, réinstallation, secret, recouvrement |
| D11 | W02/W05 | Compte neuf sans données démo | services/offline_demo_audit_seed.dart ; tests/first_use_zero_to_value_cert_test.dart | base audit/demo existante, interdiction à valider sur runtime réel | #970,#1021,#1059 | vérifier nouveau compte zéro clinique; PR correctif DRAFT |
| D12 | W06 | Saisie glycémie slider/clavier | features/journal/add_log_screen.dart | écran base; garde nonfinite DRAFT | #972 | test précision/unité/clavier/mobile |
| D13 | W06 | Abandon d'une saisie modifiée | features/journal/add_log_screen.dart ; edit_log_screen.dart | écrans de saisie; garantie non perte pas certifiée | #974 | tester dirty state, save in-flight, switch patient |
| D14 | W12 | Photo de repas, vision | features/documents/document_import_screen.dart ; backend/diabetes/api/v1/documents.py | capture/document existe; IA repas exacte non certifiée | #976 | atelier Vision + confirmation humaine + benchmark |
| D15 | W12/W06 | Repas voix/texte/formulaire, portions | features/journal/add_log_screen.dart ; services/meal_food_favorites_repository.dart | base de saisie; unification brouillon non certifiée | #978 | atelier multimodal puis draft unique et portions vérifiées |
| D16 | W03/W09/W13 | Copie/sélection du texte | features/companion/companion_conversation_screen.dart | livraison ciblée de sélection compagnon fusionnée; pas couverture globale | #980 MERGED (historique) | PR #980 scope restreint; tests autres écrans Web |
| D17 | W03/W06/W13 | Entry summary info progressive | features/journal/add_log_screen.dart | pas de preuve d'activation du nouveau panneau | — | BEFORE/mockup/AFTER et accessibilité clavier |
| D18 | W05/W10 | Profil poids/âge/genre | features/profile/profile_screen.dart | D18-A/B/C ouvertes, B/C stack; non livré D18 | #1060,#1064,#1066 | W02 coffre Web avant données patients |
| D19 | W04 | Audit calculs/metrics/nuances | backend/diabetes/api/v1/analytics.py ; kpis.py ; docs/ROADMAP.md | audit PR #920 non fusionné, #1071 stack | #920,#943,#944,#945,#1071 | reprendre CAL-01…12, indépendant clinique et oracles |
| D20 | W10 | Poids descriptif/notifications opt-in | profile_screen.dart ; reminders_screen.dart | D20 A–G empilés DRAFT et D18 dépendance | #1074,#1076,#1077,#1078,#1079,#1083,#1086 | ne pas revendiquer envoi OS; consentement et Web APIs |
| D21 | W03/W13 | Ramadan masqué, code conservé | features/profile/profile_screen.dart ; features/auth/onboarding_chat_screen.dart | cible approuvée, codepath exact pas inspecté | — | auditer feature flag effets, aucun masquage de sécurité |
| D22 | W04/W05 | Unités AVANT objectifs | features/auth/onboarding_chat_screen.dart ; features/journal/reports_screen.dart | champ unité de base, propagation end-to-end non prouvée | — | lancer tests valeurs initiales et conversions |
| D23 | W03/W13 | Préférences profil regroupées | features/profile/profile_screen.dart | UI existante, futur ordre non validé | — | mockup + test responsive/fr/AR/RTL |
| D24 | W02/W08/W13 | Paramètres IA + OFF réel | features/profile/profile_screen.dart ; services/consent_service.dart | base consent; branches opt-out empilées | #934 stack,#1056 | fail-closed serveur et client, refus egress |
| D25 | W11 | Données/appareils, connexion CGM | features/import/cgm_connections_section.dart ; services/cgm_service.dart | UI de base; les source-filter labels ne prouvent pas fabricant direct | — | atelier CGM onboarding + fraîcheur/révocation |
| D26 | W02/W08/W13 | Confidentialité/compte/danger zone | features/profile/profile_screen.dart ; services/auth_service.dart | base existante; changement ciblé non prouvé | — | design distinction logout/suppression; sécurité réelle |
| D27 | W03/W09/W13 | Avatar IAmina flottant Home-only | features/dashboard/dashboard_screen.dart ; companion/companion_conversation_screen.dart | cible maquette validée; code livré non démontré | #693 ancien DRAFT | screenshots 390/768/1280 + clavier/safe-area |
| D28 | W07/W08/W09 | Intelligence déterministe avant chat | backend/diabetes/api/v1/companion.py ; services/clinical/ ; frontend/lib/features/companion/ | base overview/proactive; enveloppe projet PR #921 DRAFT | #921,#1056 | une vérité Home/Reports/IAmina, zéro autorité LLM |
| D29 | W05/W10 | Feedback premiers utilisateurs | features/auth/onboarding_chat_screen.dart ; features/profile/profile_screen.dart | aucune preuve dédiée de livraison D29 | — | opt-in réel, suppression, timing et egress |

**Ne pas interpréter** `—` comme absence de code : signifie *aucune PR dédiée confirmée ici*. Une API/source repérée n'est pas une livraison ni une validation clinique.

## 3. Conflits et décisions de gouvernance

**GOV-01 — collision `D30` (corrigée dans la roadmap V2).** Le [registre Notion des décisions](https://app.notion.com/p/3f377c663362812dbe78cead75e71922) comporte déjà une **#30 : onboarding privacy-first, pseudonymie/absence d'egress clinique non consenti, APPROUVÉE EN PRINCIPE**, avec les PR #987–#992 DRAFT. La roadmap précédente assignait à tort D30/D31 au *couple d'ajouts d'architecture Web* ; elle n'était pas source d'une D31 ratifiée. Pour éviter d'usurper le numéro du registre :
- `D30` = **décision utilisateur existante sur privacy-first**, prévue dans **W02** ; revue Web complète encore requise ;
- `A-WEB-01` = **cible topologie frontend Vercel séparé du backend Vercel**, décision de cadrage utilisateur (non-déploiement), **W01** ;
- `A-WEB-02` = **contrat Web/Neon, sécurité, consentement, coffre, compatibilité local-first**, à définir W01/W02 ; *ce n'est pas une décision produit D31 approuvée*.
Toute extension du registre produit demeure un arbitrage humain distinct. La matrice D1–D29 reste complète.

**ARC-01 — architecture cible ≠ as-built certifié.** `frontend/vercel.json`, `backend/vercel.json` et `vercel.json` existent. `frontend/vercel_build.sh` contient un projet frontend review identifié et un backend `iamina-certified.vercel.app` ; le chemin backend Vercel/Neon est connu dev/cert. Cela ne prouve pas que **deux projets de production** et leur base sont prêts. Le dépôt décrit Django/Flutter/Drift, le backend `api/index.py` et des API séparées. W01 doit vérifier limites serverless, jobs longs, origine API/CDN, config secrets, CORS/CSRF, migration/backup/restore, et usage d'une DB managée indépendante de l'exécution Vercel.
**CONTRADICTION À TRAITER :** `docs/LOCAL_FIRST_RUNTIME_BOUNDARY.md` définit la donnée patient comme local-first sans dépendance Vercel/Neon ; W01/W02 doivent expliciter comment l'objectif Vercel peut coexister avec le coffre Web, une connexion nouvelle et l'offline, via ADR approuvé avant modification irréversible. **Pas de bascule silencieuse vers serveur-patient**.

**SEC-01 — privacy/egress avant W05/W06 et IA** : les branches #987–#992 et #1056 contiennent des correctifs potentiellement critiques encore **DRAFT** ; ne pas supposer qu'ils protègent main. Reproduire sur main avec données synthétiques avant promotion, priorité à auth, consentement, séparation A/B, egress texte/image, CSRF et journaux. Si fuite reproduite, isoler correctif sécurité avant fonctionnalités.

**STACK-01 — 32 PR empilées** : les séries D9, D18→D20, D19/CGM, V1-03 opt-out/SSE n'ont pas leur état de merge indépendamment. Rebase/remplacement rationnel sur main actuel, **pas de fusion automatique d'un enfant sans parent**. Archiver/fermer les branches obsolètes seulement après vérification du diff et de la dépendance.

**CGM-01** : `cgm_connections_section.dart` présente des noms de fabricants mais le backend requiert `base_url` et identifiant pour l'adaptateur compatible Nightscout. **Un label Dexcom/Libre/LinX n'établit pas OAuth officiel ni disponibilité au Maroc.** W11 doit faire brainstorming et parcours d'onboarding, puis preuve de source, consentement, timestamp, lecture seule, compatibilité.

**OCR-01** : P5-2 historique documente un échec du Tesseract arabe plein-document comme chemin principal ; aucune qualification générale Vision repas / OCR document sur Web. W12 commence par brainstorming et onboarding + benchmark réel ; photo et texte proposés restent incertains et exigent confirmation avant journal.

**UI-01** : D16 sélection de texte livrée seulement sur surface Companion [#980](https://github.com/hraaaaf/IAMINA-MVP/pull/980), elle n'est pas un signal que D16 globale est terminée. D3 test exact HEAD rouge malgré plusieurs audits visuels verts. Pour W03/W13 : BEFORE, objectif, maquette, AFTER **mêmes** 390×844, 768×1024, 1280×900 quand pertinents, FR/AR/RTL, clavier, accessibilité, tests; pas de score sans images réelles.

**QA-01** : l'inventaire est une preuve de présence de source + CI consultée, **non un test Web E2E complet de W01–W14**. W00 ne ferme aucune D et ne modifie pas P5 historique **6/12=50%** ; avancement V2 non encore quantifié.

## 3 bis. Dettes techniques canoniques à reprendre (audit `docs/TECHDEBT.md`)

Ce registre actuel comporte **quatre dettes non résolues**. Elles ne sont pas confondues avec les 86 PR ni comptabilisées comme fonctionnalités D livrées.

| Dette | Etat constaté | W / action nécessaire |
|---|---|---|
| **TD-001 — egress texte/media non structuré** | Le contrôle central existe, mais la désidentification du texte libre n'est pas universelle ; OCR cloud d'un document patient demeure volontairement bloqué | **W02/W08 avant W12** : conserver fail-closed, bench OCR local et données synthétiques, revue PHI, ne pas expédier d'images brutes patient |
| **TD-002 — Firebase migration** | L'identité distante cible Django existe ; dépendances Firebase de migration encore installées, désactivées par défaut | **W01/W02** : inventaire SDK et mode de migration, supprimer seulement après plan de reprise/compatibilité |
| **TD-009 — MFA staff/pro** | Authentification forte des rôles privilégiés incomplète | **W02/W14**, hors ouverture patient/professionnel sans gate |
| **TD-012 — grands widgets Flutter** | Plusieurs découplages de composants terminés, dette résiduelle sur grands composants | **W03/W13** selon changement concret, ne pas refactoriser sans risque reproduit ou gain de maintenance vérifiable |

Autre écart : `docs/LOCAL_FIRST_RUNTIME_BOUNDARY.md` est un contrat existant non réécrit ici ; sa notion de patient runtime local-first ne devient pas automatiquement compatible avec la topologie Vercel proposée. W01 doit documenter l'arbitrage dans un nouvel ADR plutôt que modifier discrètement cette doctrine.

## 4. Ordre consolidé en fonction des dépendances
- **Chemin critique :** W00 (matrice/état) → **W01** (ADR topologie et contrats navigateur↔API↔Neon) → **W02** (patient, coffre Web/consentement, D30 privacy-first) ; **W04** (calculs et unités) → W05 (onboarding) + W06 (capture) → W07 (insights) ; W08 doit précéder IA externe W09 ; W14 après W13 et toutes gates.
- **Parallèle sans intégration prématurée :** W03 quick wins et revue des captures, préparation W04/CAL, ateliers W11 CGM et W12 OCR/Vision. Le D3 rouge exige remédiation dans son lot, pas validation dans W00.
- **Native-only** : D10 iOS #1062, alignment Android/iOS/P5-4B et ponts capteur OS restent hors plan Web ; ne pas déclarer certifié ni fermer automatiquement.
- **Gates :** confidentialité/CNDP et transferts sous juridiction applicable, safety clinique/locale, isolation patient, restauration DB et accord explicite pour toute opération Vercel ; aucun traitement patient réel sans gate correspondant.

## 5. Registre complet des 86 PR ouvertes (snapshot de W00)
`WEB-REVIEW` = piste de triage, **non preuve de compatibilité**. `STACKED` = base de PR différente de main. `NATIVE-DEFER` = cible native exclue, sauf dépendance sécurité non différable. `TRIAGE` = vérifier avant toute décision de fermeture/merge.

| PR | GitHub state | Base | Classe de tri initiale | Titre |
|---|---|---|---|---|
| [#1086](https://github.com/hraaaaf/IAMINA-MVP/pull/1086) | DRAFT | STACKED: feat/v1-d20-consent-profile-controls-20261015 | TRIAGE | D20-G: revalidate patient consent and source immediately before future OS dispatch |
| [#1085](https://github.com/hraaaaf/IAMINA-MVP/pull/1085) | DRAFT | main | WEB-REVIEW | fix(D3): rappels locaux après Tendance, sur main actuel |
| [#1083](https://github.com/hraaaaf/IAMINA-MVP/pull/1083) | DRAFT | STACKED: feat/v1-d20-profile-trend-view-20261015 | TRIAGE | D20-F: patient-local voluntary weight notice consent UI (no sending) |
| [#1079](https://github.com/hraaaaf/IAMINA-MVP/pull/1079) | DRAFT | STACKED: feat/v1-d20-weight-delivery-ledger-20261015 | TRIAGE | D20-E: neutral source-traceable weight trend on real ProfileScreen |
| [#1078](https://github.com/hraaaaf/IAMINA-MVP/pull/1078) | DRAFT | STACKED: feat/v1-d20-vault-optin-preferences-20261015 | TRIAGE | D20-D: patient-local durable notice reservation and dedup (no sending) |
| [#1077](https://github.com/hraaaaf/IAMINA-MVP/pull/1077) | DRAFT | STACKED: feat/v1-d20-notice-policy-optin-20261015 | TRIAGE | D20-C: persist voluntary weight-notice preferences in patient-local vault |
| [#1076](https://github.com/hraaaaf/IAMINA-MVP/pull/1076) | DRAFT | STACKED: feat/v1-d20-weight-trend-descriptive-20261015 | TRIAGE | D20-B: consent-first deterministic weight notice eligibility (no sending) |
| [#1074](https://github.com/hraaaaf/IAMINA-MVP/pull/1074) | DRAFT | STACKED: feat/v1-d18-c-profile-progressive-ui-20261015 | TRIAGE | D20-A: deterministic opt-in-ready weight trend basis (no notifications) |
| [#1071](https://github.com/hraaaaf/IAMINA-MVP/pull/1071) | DRAFT | STACKED: audit/v1-01-calculation-authority-20261009 | WEB-REVIEW | fix(D19): disjoint CGM metric, AGP and sufficiency time windows |
| [#1070](https://github.com/hraaaaf/IAMINA-MVP/pull/1070) | DRAFT | STACKED: fix/pulper-groq-gptoss-contract-20261014 | WEB-REVIEW | [P0 #1067] Isolated browser OCR comparison — Tesseract.js / PaddleOCR.js (synthetic only) |
| [#1066](https://github.com/hraaaaf/IAMINA-MVP/pull/1066) | DRAFT | STACKED: feat/v1-d18-local-first-weight-vault-20261015 | WEB-REVIEW | feat(D18-C): optional local progressive-profile UI (DRAFT / NO MERGE) |
| [#1065](https://github.com/hraaaaf/IAMINA-MVP/pull/1065) | DRAFT | main | WEB-REVIEW | docs: record CNDP/GCC onboarding decisions as proposed pilot requirements |
| [#1064](https://github.com/hraaaaf/IAMINA-MVP/pull/1064) | DRAFT | main | WEB-REVIEW | feat(D18-B): local-only patient-vault weight observation store |
| [#1062](https://github.com/hraaaaf/IAMINA-MVP/pull/1062) | DRAFT | main | NATIVE-DEFER | ci(D10 iOS #1057): capture Pods_Runner Simulator linker root cause on Actions |
| [#1060](https://github.com/hraaaaf/IAMINA-MVP/pull/1060) | DRAFT | main | WEB-REVIEW | feat(D18-A): append-only weight history and optional birth year/identity |
| [#1059](https://github.com/hraaaaf/IAMINA-MVP/pull/1059) | DRAFT | main | TRIAGE | test(D10×D11): synthetic integration of current main protections and draft D11 zero-demo |
| [#1056](https://github.com/hraaaaf/IAMINA-MVP/pull/1056) | DRAFT | main | WEB-REVIEW | fix(v1-03): POST-only SSE, deferred patient egress and auth/CSRF regressions (#925) |
| [#1037](https://github.com/hraaaaf/IAMINA-MVP/pull/1037) | DRAFT | main | TRIAGE | docs(agent-council): publish proof-bounded preliminary 15-domain triage |
| [#1034](https://github.com/hraaaaf/IAMINA-MVP/pull/1034) | DRAFT | main | WEB-REVIEW | fix(sync): prevent internal exception disclosure in batch journal API |
| [#1021](https://github.com/hraaaaf/IAMINA-MVP/pull/1021) | DRAFT | main | WEB-REVIEW | fix(D11): never inject synthetic clinical data into real patient accounts |
| [#1005](https://github.com/hraaaaf/IAMINA-MVP/pull/1005) | DRAFT | main | TRIAGE | fix(Pulper): Groq GPT-OSS only, repair structured reply + reasoning HTTP 400 |
| [#1003](https://github.com/hraaaaf/IAMINA-MVP/pull/1003) | DRAFT | STACKED: feat/v1-d7-medical-profile-relevance-20261013 | TRIAGE | D9 — First-use recovery on D7, combined CI certified (DRAFT, awaiting safety validation) |
| [#1001](https://github.com/hraaaaf/IAMINA-MVP/pull/1001) | DRAFT | STACKED: feat/v1-d7-medical-profile-relevance-20261013 | TRIAGE | D9 — Owner-bound first-use restoration on D7 (DRAFT, pending release gates) |
| [#1000](https://github.com/hraaaaf/IAMINA-MVP/pull/1000) | DRAFT | STACKED: feat/v1-d7-medical-profile-relevance-20261013 | TRIAGE | D9 — Clean first-use restoration on D7, combined CI green (DRAFT) |
| [#998](https://github.com/hraaaaf/IAMINA-MVP/pull/998) | DRAFT | STACKED: feat/v1-d7-medical-profile-relevance-20261013 | TRIAGE | D9 — Verify combined first-use server and patient-vault flow (temporary CI base) |
| [#997](https://github.com/hraaaaf/IAMINA-MVP/pull/997) | DRAFT | STACKED: feat/v1-d7-medical-profile-relevance-20261013 | TRIAGE | D9 — Restore authenticated first-use state in patient vault (D7-stacked DRAFT) |
| [#996](https://github.com/hraaaaf/IAMINA-MVP/pull/996) | DRAFT | main | WEB-REVIEW | D9 — Fail-closed Flutter transport for owner-bound first-use proof |
| [#995](https://github.com/hraaaaf/IAMINA-MVP/pull/995) | DRAFT | main | WEB-REVIEW | D9 — Server-side explicit first-use proof, owner-scoped and consent-independent |
| [#992](https://github.com/hraaaaf/IAMINA-MVP/pull/992) | DRAFT | main | TRIAGE | D30 — Integrate journal + profile clinical egress holds before D7 |
| [#990](https://github.com/hraaaaf/IAMINA-MVP/pull/990) | DRAFT | main | TRIAGE | fix(D30): block unauthenticated raw clinical media and SSE egress |
| [#989](https://github.com/hraaaaf/IAMINA-MVP/pull/989) | DRAFT | main | TRIAGE | fix(D30): prevent unconsented clinical profile PATCH from local-only vault |
| [#988](https://github.com/hraaaaf/IAMINA-MVP/pull/988) | DRAFT | main | TRIAGE | D30-1 safety: block unauthenticated clinical log sync egress |
| [#987](https://github.com/hraaaaf/IAMINA-MVP/pull/987) | DRAFT | main | TRIAGE | D30-0 — Privacy-first onboarding: ADR, threat model and recovery gates |
| [#978](https://github.com/hraaaaf/IAMINA-MVP/pull/978) | DRAFT | main | TRIAGE | test(V1 decision #15): synthetic multimodal meal converges to one draft |
| [#976](https://github.com/hraaaaf/IAMINA-MVP/pull/976) | DRAFT | main | TRIAGE | test(V1 decision #14): uncertain photo meal must require human confirmation |
| [#974](https://github.com/hraaaaf/IAMINA-MVP/pull/974) | DRAFT | main | TRIAGE | fix(V1 decision #13): block discard/navigation during active glucose save |
| [#972](https://github.com/hraaaaf/IAMINA-MVP/pull/972) | DRAFT | main | TRIAGE | fix(V1 decision #12): fail closed on nonfinite glucose input before slider |
| [#970](https://github.com/hraaaaf/IAMINA-MVP/pull/970) | DRAFT | main | TRIAGE | test(V1 decision #11): empty real patients never receive audit/demo records |
| [#954](https://github.com/hraaaaf/IAMINA-MVP/pull/954) | DRAFT | main | TRIAGE | feat(V1 decision #4): synthetic-only deterministic CSV/JSON primitives |
| [#949](https://github.com/hraaaaf/IAMINA-MVP/pull/949) | DRAFT | main | TRIAGE | test(V1 decision #2): fail-closed proactive API authorization and replay |
| [#945](https://github.com/hraaaaf/IAMINA-MVP/pull/945) | DRAFT | main | TRIAGE | fix(v1-01 CAL-11): reconcile apple/banana nutrition IDs and peeled weights to USDA Foundation 2026 |
| [#944](https://github.com/hraaaaf/IAMINA-MVP/pull/944) | DRAFT | main | TRIAGE | ci(v1-01 CAL-11): verify 7 nutrition FDC IDs directly from official USDA April 2026 archive |
| [#943](https://github.com/hraaaaf/IAMINA-MVP/pull/943) | DRAFT | main | TRIAGE | test(v1-01): parallel CAL-09/10 day-boundary, CAL-11 USDA source oracle and CAL-12 PDF quarantine |
| [#942](https://github.com/hraaaaf/IAMINA-MVP/pull/942) | DRAFT | main | TRIAGE | test(v1-03): zero-client clean local-first install with offline disk restart |
| [#941](https://github.com/hraaaaf/IAMINA-MVP/pull/941) | DRAFT | main | TRIAGE | test(v1-03): integrated safety CI for opt-out + POST SSE + dormant P3 + PWA upgrade |
| [#940](https://github.com/hraaaaf/IAMINA-MVP/pull/940) | DRAFT | STACKED: parallel/v1-03-optout-transport-inventory-20261011 | TRIAGE | test(v1-03): PWA SSE POST upgrade marker and compatibility trial 0.1.0+2 |
| [#939](https://github.com/hraaaaf/IAMINA-MVP/pull/939) | DRAFT | STACKED: parallel/v1-03-optout-transport-inventory-20261011 | TRIAGE | test(v1-03): integrate SSE auth/urgent hotfix with persistent local AI opt-out |
| [#938](https://github.com/hraaaaf/IAMINA-MVP/pull/938) | DRAFT | main | TRIAGE | security(v1-03): stop patient text in SSE GET URLs (isolated hotfix) |
| [#937](https://github.com/hraaaaf/IAMINA-MVP/pull/937) | DRAFT | STACKED: parallel/v1-03-module-alias-404-audit-20261011 | TRIAGE | fix(v1-03): P3 dormant option A — 16/16 exact-HEAD green (#929) |
| [#936](https://github.com/hraaaaf/IAMINA-MVP/pull/936) | DRAFT | STACKED: safety/v1-03-glucose-ocr-unit-provenance-20261011 | TRIAGE | test(p3): Django boot timing and dormant alias verified — 16/16 green (#929) |
| [#935](https://github.com/hraaaaf/IAMINA-MVP/pull/935) | DRAFT | STACKED: safety/v1-03-glucose-ocr-unit-provenance-20261011 | TRIAGE | test(v1-03): legacy SSE GET guarded — 16/16 exact-HEAD green (#925 #927) |
| [#934](https://github.com/hraaaaf/IAMINA-MVP/pull/934) | DRAFT | STACKED: safety/v1-03-glucose-ocr-unit-provenance-20261011 | TRIAGE | feat(v1-03): per-device AI opt-out option A — 19/19 exact-HEAD green (#924) |
| [#933](https://github.com/hraaaaf/IAMINA-MVP/pull/933) | DRAFT | STACKED: safety/v1-03-glucose-ocr-unit-provenance-20261011 | TRIAGE | docs(v1-03): OCR reachability and clinical preactivation evidence matrix (#923) |
| [#932](https://github.com/hraaaaf/IAMINA-MVP/pull/932) | DRAFT | STACKED: security/v1-03-strip-client-curl-logger-20261011 | TRIAGE | fix(v1-03): fail-closed glucose OCR when unit is absent or ambiguous (#923) |
| [#931](https://github.com/hraaaaf/IAMINA-MVP/pull/931) | DRAFT | STACKED: security/v1-03-cross-route-cookie-csrf-20261010 | TRIAGE | fix(V1-03): remove credential/patient-payload curl logging from API client (#930) |
| [#928](https://github.com/hraaaaf/IAMINA-MVP/pull/928) | DRAFT | STACKED: fix/v1-03-sse-post-scoped-20261010 | TRIAGE | fix(v1-03): cross-route cookie-session CSRF guard (#927) — DRAFT |
| [#926](https://github.com/hraaaaf/IAMINA-MVP/pull/926) | DRAFT | STACKED: security/v1-03-summary-local-only-20261010 | TRIAGE | fix(v1-03): POST SSE body + deferred egress scope (#925) |
| [#922](https://github.com/hraaaaf/IAMINA-MVP/pull/922) | DRAFT | main | TRIAGE | fix(v1-03): local-only deterministic summary narration |
| [#921](https://github.com/hraaaaf/IAMINA-MVP/pull/921) | DRAFT | main | WEB-REVIEW | feat(v1-02): governed patient intelligence envelope — first backend slice (OPEN) |
| [#920](https://github.com/hraaaaf/IAMINA-MVP/pull/920) | DRAFT | main | WEB-REVIEW | audit(v1-01): calculation authority and cross-surface inventory (OPEN) |
| [#918](https://github.com/hraaaaf/IAMINA-MVP/pull/918) | READY (non fusionnée) | main | TRIAGE | test(ux95): verify compact 360px navigation and actual keyboard destinations |
| [#869](https://github.com/hraaaaf/IAMINA-MVP/pull/869) | DRAFT | STACKED: preview/intent-envelope-v1-demo | TRIAGE | feat(companion): integrate frozen Intent Envelope V1 into runtime |
| [#866](https://github.com/hraaaaf/IAMINA-MVP/pull/866) | DRAFT | STACKED: feat/companion-intent-envelope-router | TRIAGE | preview(companion): exercise Intent Envelope V1 in synthetic demo |
| [#865](https://github.com/hraaaaf/IAMINA-MVP/pull/865) | READY (non fusionnée) | main | TRIAGE | feat(companion): validate Intent Envelope Router V1 candidate |
| [#849](https://github.com/hraaaaf/IAMINA-MVP/pull/849) | READY (non fusionnée) | main | TRIAGE | fix(demo): keep personal CGM metrics out of education routing |
| [#787](https://github.com/hraaaaf/IAMINA-MVP/pull/787) | READY (non fusionnée) | main | TRIAGE | feat(foodpicker): B34 Bahrain core |
| [#701](https://github.com/hraaaaf/IAMINA-MVP/pull/701) | DRAFT | main | TRIAGE | refactor(td012): extract certified Login presentation |
| [#693](https://github.com/hraaaaf/IAMINA-MVP/pull/693) | DRAFT | main | TRIAGE | feat(dashboard): premium mobile IAMINA conversation bar |
| [#684](https://github.com/hraaaaf/IAMINA-MVP/pull/684) | READY (non fusionnée) | main | NATIVE-DEFER | fix(auth): restore native onboarding before consent |
| [#683](https://github.com/hraaaaf/IAMINA-MVP/pull/683) | READY (non fusionnée) | main | TRIAGE | fix(auth): harden hosted review consent onboarding flow |
| [#679](https://github.com/hraaaaf/IAMINA-MVP/pull/679) | READY (non fusionnée) | main | TRIAGE | fix(vercel): repair hosted auth and PWA release pipeline |
| [#678](https://github.com/hraaaaf/IAMINA-MVP/pull/678) | DRAFT | main | TRIAGE | fix(vercel): recover hosted auth-consent-onboarding pipeline |
| [#677](https://github.com/hraaaaf/IAMINA-MVP/pull/677) | READY (non fusionnée) | main | TRIAGE | fix(vercel): gate hosted flow on real remote credential |
| [#672](https://github.com/hraaaaf/IAMINA-MVP/pull/672) | DRAFT | main | TRIAGE | fix(vercel): make hosted review use remote account auth |
| [#595](https://github.com/hraaaaf/IAMINA-MVP/pull/595) | DRAFT | STACKED: deploy/p5-6-base-parent | TRIAGE | deploy: P5-6 exact candidate preview |
| [#589](https://github.com/hraaaaf/IAMINA-MVP/pull/589) | READY (non fusionnée) | main | TRIAGE | chore(infra): prepare IAMINA Django backend for Vercel |
| [#573](https://github.com/hraaaaf/IAMINA-MVP/pull/573) | READY (non fusionnée) | main | TRIAGE | P5-6: bind release approvals to exact candidate SHA |
| [#551](https://github.com/hraaaaf/IAMINA-MVP/pull/551) | READY (non fusionnée) | main | TRIAGE | test: replay P5-5 pilot rehearsal on current main |
| [#302](https://github.com/hraaaaf/IAMINA-MVP/pull/302) | READY (non fusionnée) | STACKED: release/dashboard-p6-next-best-action-clean | TRIAGE | chore(dashboard): sync current main into P6 release branch |
| [#223](https://github.com/hraaaaf/IAMINA-MVP/pull/223) | READY (non fusionnée) | main | TRIAGE | fix(i18n): localize medication and reminder dates |
| [#222](https://github.com/hraaaaf/IAMINA-MVP/pull/222) | READY (non fusionnée) | main | TRIAGE | fix(i18n): localize global render fallback |
| [#221](https://github.com/hraaaaf/IAMINA-MVP/pull/221) | READY (non fusionnée) | main | TRIAGE | feat(i18n): localize AI Summary shell |
| [#207](https://github.com/hraaaaf/IAMINA-MVP/pull/207) | READY (non fusionnée) | main | TRIAGE | P3-EVALS canonical closeout sync |
| [#182](https://github.com/hraaaaf/IAMINA-MVP/pull/182) | DRAFT | STACKED: agent/p3-evals-1-clean | TRIAGE | p3 evals 2 |
| [#171](https://github.com/hraaaaf/IAMINA-MVP/pull/171) | DRAFT | STACKED: agent/p3-horizon-0-rebased | TRIAGE | p3 horizon adapters |
| [#138](https://github.com/hraaaaf/IAMINA-MVP/pull/138) | DRAFT | main | TRIAGE | P2-PROACTIVE — Deterministic attention and insight lifecycle |

## 6. Critères de closeout et suite
- [x] Main SHA figé pour le snapshot.
- [x] 29/29 décisions inventoriées et attachées aux W.
- [x] 86 PR indexées, 70 DRAFT / 16 READY, bases distinguées.
- [x] Source Web, Backend, API CGM, auth WebAuthn, consent/local-first, Vercel et CI comparés en lecture.
- [x] D3 exact HEAD rouge consigné.
- [x] Collision D30/D31 corrigée en séparant numéro de décision et codes A-WEB.
- [ ] Revue documentaire indépendante et CI sur le **HEAD final de la PR W00**, merge puis CI postmerge ; miroir Notion du résultat.
**Next exact :** ouvrir W01 : ADR de topologie 2 projets Vercel + Neon, PWA/offline/secret storage, contrat API, modèle d'identité/consentement ; puis W02. Aucun déploiement Vercel autorisé.
