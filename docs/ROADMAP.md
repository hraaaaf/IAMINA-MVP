# IAmina — Canonical Roadmap

> **2026-10-12 — CAL-11 VÉRIFICATION USDA EN CI :** la [PR #944 DRAFT](https://github.com/hraaaaf/IAMINA-MVP/pull/944) a résolu le **blocage d'accès au ZIP officiel** via GitHub runner, [run 38272356607](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38272356607) : archive primaire téléchargée/ZIP valide et preuve 11756709069. Premier résultat rouge : le parseur n'admettait pas les entrées JSON `null` de `FoundationFoods`, **avant confrontation des sept FDC IDs**. Correctif prudent + deux tests négatifs/positifs dans SHA `e77304be0d049516f4d8b07914427ae3ebe9552d` ; [nouveau run 38272863911](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38272863911) lancé, verdict encore en attente. Ne pas présenter données pomme/banane ou portions comme vérifiées avant résultat officiel. CAL-09/10 jour du patient, CAL-12 PDF et revues médicales ouverts ; #943 conserve 17/17 CI sur son SHA distinct. [Dossier décision CAL](assessments/2026-10-12-v1-01-cal09-cal11-cal12-decision-gates.md). Aucune donnée patient, merge, ni Vercel.

> **2026-10-12 — CERTIFICATION INTÉGRÉE V1-01 CAL-09/10 + CAL-11 + CAL-12 :** [PR #943 DRAFT](https://github.com/hraaaaf/IAMINA-MVP/pull/943), commit exact **`f7ebe654cd69a03acf6a3694ff0633e8a5b5042e`**, **17/17 workflows GitHub `completed/success`**, dont [CI principale `38268340588`](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38268340588) **6/6 jobs SUCCESS** : backend Ruff/pytest + PostgreSQL, Flutter analyze/tests/build PWA, secret hygiene/scope et size advisory ; [Chrome unités BEFORE/AFTER `38268340548`](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38268340548) SUCCESS, UI missing routes `38268340380` SUCCESS, les 15 autres workflows également verts. Diff vs [#920 `81bf4d6`](https://github.com/hraaaaf/IAMINA-MVP/pull/920) : 4 fichiers test/script uniquement, zéro runtime/valeur clinique/UI changé. **Portée :** CAL-09/10 dépendance UTC/UTC+1 *caractérisée*, **pas de politique du jour patient approuvée** ; CAL-11 oracle synthétique PASS, **source réelle USDA Foundation Foods avril 2026 non téléchargée ni comparée par FDC ID**, les valeurs pomme/banane et les 110–115 g banane non certifiés ; CAL-12 import/export PDF non typé bloqué, **PDF clinique Unicode/RTL toujours absent**. Les docs USDA officiels confirment l'archive Foundation Foods **04/2026** et son ZIP **459 Ko**, mais fetch ZIP/DNS indisponible depuis cet environnement (404/connexion, ne jamais déclarer provenance ligne par ligne). **Statut `V1-01_TECHNICAL_CI_17_OF_17 / DECISION_19_OPEN / NOT_MERGED / NOT_DEPLOYED`**. Next exact : obtenir la source primaire USDA officielle (ou voie API officielle à clé autorisée) et auditer les sept FDC ID ; solliciter arbitrage clinique jour/fuseau et consentement/export typé ; préparer revue indépendante. Aucun merge ou Vercel sans autorisation explicite, tracker V1 0/29 décisions totalement livrées, P5 historique 6/12 = 50 %.

> **2026-10-12 — V1-01 exécution simultanée CAL-09/10, CAL-11, CAL-12 :** trois branches indépendantes issues de [PR #920](https://github.com/hraaaaf/IAMINA-MVP/pull/920) `81bf4d6` (17/17 CI verts), intégrées pour UNE campagne de certification sur [PR #943 DRAFT](https://github.com/hraaaaf/IAMINA-MVP/pull/943), HEAD `f7ebe654cd69a03acf6a3694ff0633e8a5b5042e` (**17 workflows démarrés**, [CI `38268340588`](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38268340588) queued au premier relevé, aucun succès final acquis). CAL-09/10 : 2 tests de caractérisation de la dépendance `_patterns` au jour UTC vs UTC+01 pour 5 observations, sans fixer un jour clinique ; CAL-11 : oracle reproductible local de l'archive primaire USDA Foundation `2026-04`, 8 essais purement synthétiques, **l'archive USDA réelle n'a pas pu être téléchargée, aucune valeur FDC certifiée**, les poids banana 110–115 g restent non sourcés ; CAL-12 : nouveau garde des `import/export` du PDF local ASCII non typé depuis `frontend/lib`. **Diff V1-01 #920→#943 : 4 fichiers (tests et script de contrôle uniquement), aucun runtime/UI/valeur médicale modifié.** Statut #19 reste EN COURS, aucune décision V1 des 29 entièrement livrée ; revues cliniques/privacy/RTL et source USDA primaire requises. **Next exact :** lire la CI exacte #943, corriger échecs sur nouveau SHA, puis traiter les gates source/clinique non substituables. Pas de merge ni Vercel sans autorisation explicite. P5 historique 6/12 = 50% distinct.

> **2026-10-12 — REPRISE DE PRIORITÉ V1 PAR DÉCISION PROPRIÉTAIRE :** arrêter d'ouvrir de nouveaux lots de QA/first-install tant que la feuille de route V1 des **29 décisions approuvées** (appelées « 27 étapes » dans la demande de reprise ; [checklist source](https://app.notion.com/p/3f477c6633628161aba2c43201805156)) n'a pas repris son **ordre canonique**. La V1 couvre **V1-01 → V1-11** ; le programme global P5 **12 lots / 6 clos** est distinct. État du registre au 10/10 : **29/29 décisions arbitrées, 0/29 livrées intégralement, #19/#22/#28 en cours**, les sous-jalons cochés étant des preuves techniques seulement. Contrôles GitHub relus au 12/10 : [#920 V1-01](https://github.com/hraaaaf/IAMINA-MVP/pull/920) `81bf4d6` **17/17 CI**, [#921 V1-02](https://github.com/hraaaaf/IAMINA-MVP/pull/921) `5b43f01` **2/2 CI**, [#941 V1-03](https://github.com/hraaaaf/IAMINA-MVP/pull/941) `d3562e8` **25/25 CI**, tous DRAFT/non mergés et **non livrés**. [#942](https://github.com/hraaaaf/IAMINA-MVP/pull/942) first-install reste DRAFT à suivre sans en faire le chemin critique (au contrôle : 20 verts/25, 1 rouge PWA, 2 en cours, 2 queued). **Next exact prioritaire : V1-01/#19 calculs et autorité clinique** — reprendre le [dossier CAL](https://github.com/hraaaaf/IAMINA-MVP/blob/audit/v1-01-calculation-authority-20261009/docs/assessments/2026-10-09-v1-01-calculation-authority-audit.md), classer CAL-09/10 jour/fuseau clinique, CAL-11 provenance USDA/FDC, CAL-12 PDF typé Unicode/RTL, preuves et revues. Ensuite V1-02 (#28), puis fermer V1-03 (#24/#26/#28) **avant** V1-04 et les autres lots selon dépendances ; P5-6 et le release gate patient restent séparés. **0 client, local-first**. Aucun merge ni Vercel sans permission explicite.

> **2026-10-12 — V1-03 lot FIRST-INSTALL ZÉRO CLIENT :** [PR #942 DRAFT](https://github.com/hraaaaf/IAMINA-MVP/pull/942), SHA `5d3f4fa1e2fa1e6824c8046471611581a76ec05a`, descend de [#941](https://github.com/hraaaaf/IAMINA-MVP/pull/941) (ce dernier **25/25 CI verts**). Un seul nouveau fichier de tests Flutter, aucun runtime modifié : première installation locale sans authentification distante et sans HTTP, réouverture de SQLite réellement sur disque avec glycémie **synthétique** conservée, refus IA persistant après reconstruction des services avec zéro réseau. 25 workflows GitHub **déclenchés pour #942**, résultat encore **non confirmé** au lancement ([CI `38263636140`](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38263636140)). Cela reste une **preuve synthétique**, pas une qualification de vrais appareils ni une activation clinique. Goal suivant : CI exact HEAD #942 → appareil vierge PWA/iOS/Android (non patient) → revue engineering ciblée → autorisation merge distincte d'éventuel déploiement Vercel ; P5-6A/B avant premier patient. Voir [handover §24](handovers/2026-10-11-iamina-v1-03-option-a-p3-dormant-handover.md). **P5 historique 50 %** inchangé.

> **V1-03 2026-10-12 — RECTIFICATION ZÉRO CLIENT :** le propriétaire confirme **0 client**. La V1 est **local-first**, Vercel/Neon sont des environnements de développement/certification et non le runtime patient. Les anciennes tâches de migration des clients installés sont caduques : priorité aux essais de **première installation vierge** et à la sécurité sur données synthétiques. Les gates relatifs aux premières données patient restent régis par le §9. La PR #941 `d3562e8` a **25/25 CI verts**, est DRAFT, non mergée/non déployée. Voir [handover §23](handovers/2026-10-11-iamina-v1-03-option-a-p3-dormant-handover.md) et [gate pré-lancement](assessments/2026-10-12-v1-03-distribution-privacy-cutover-gates.md). Merge et Vercel demandent des autorisations distinctes. **P5 historique 6/12 = 50 %.**

> **Reprise V1-03 actuelle (2026-10-11) :** [`docs/handovers/2026-10-11-iamina-v1-03-option-a-p3-dormant-handover.md`](handovers/2026-10-11-iamina-v1-03-option-a-p3-dormant-handover.md) — PR #937 option A, code `4d287bb...`, 16/16 CI, DRAFT et base #936, sans merge ni release. Toujours revérifier GitHub HEAD et CI à l'ouverture d'une nouvelle session.


> **Pack des revues V1-03 — 2026-10-11 :** [preuves & gates indépendants](assessments/2026-10-11-v1-03-independent-review-readiness.md) — tests #932/#934/#935/#936/#937 verts sur leurs HEAD individuels, aucun CI exact-HEAD sur la documentation #933. SSE ingress/anciens clients, refus IA sur vrais appareils, OCR clinique et intégration de la pile restent OPEN. Aucun merge ni Vercel. `NOT_RELEASE_AUTHORIZED`.

> **Audit client SSE/upgrade ciblé — 2026-10-11 :** inventaire source au HEAD #934 `f0b02165` de **33 services Dart + 6 entrées Flutter** : aucune référence détectée à la consultation `/api/v1/app-compatibility` ni à ses états version dans ces 39 fichiers. Pas de preuve de consultation/notification du minimum côté client, ni d'inventaire de vraies installations. Le backend teste `version_unknown`; ne pas inférer un upgrade forcé, ni exposer GET avec PHI. Voir [dossier de revue V1-03](assessments/2026-10-11-v1-03-independent-review-readiness.md). Réconciliation local-first et validation multi-appareil avant distribution ; aucun merge/Vercel/patient.

> **Correction par preuve binaire sur déploiement Vercel (2026-10-11) :** [audit des alias SSE et bundle réel](assessments/2026-10-11-v1-03-deployed-sse-url-privacy-divergence.md). Alias review et certified pointent vers commits historiques `1e44ba57` et `b13b44e7` où le code source inclut GET SSE avec `?message`. **Toutefois le vrai JS web servi (HTTP 200) ne contient pas `chat/stream`** ; le parcours Flutter actif `/companion/chat` passe par `CompanionConversationScreen` → `CompanionService.sendChatMessage` en POST. Exposition GET du **parcours web actif non démontrée** ; anciens clients, anciennes PWA, logs/ingress, runtime authentifié restent UNKNOWN. Backend GET legacy à éliminer avant pilote avec validation client/rollout ; pas de fuite avérée. Pas de merge/Vercel sans autorisation explicite.

> **P0 V1-03 — dérive des déploiements SSE (vérifiée 2026-10-11) :** les SHAs Vercel production (backend `df004bcb`, frontend `1e44ba57`) conservent **GET `/api/v1/ai/chat/stream?message=…`**, alors que #932/#935 étaient non fusionnées. `main` journalise aussi un extrait patient lors du triage urgent ; la migration naïve vers POST faisait renvoyer du JSON avant l'auth/CSRF au client SSE. [Dossier de preuve et de reprise](assessments/2026-10-11-v1-03-sse-production-drift-pr938.md) ; [hotfix isolé PR DRAFT #938](https://github.com/hraaaaf/IAMINA-MVP/pull/938), non fusionné et **NON DÉPLOYÉ**. Aucune fuite réelle prouvée, rétention/ingress et versions distribuées inconnues. **Gate P0 :** CI exacte, tests urgent/CSRF, stratégie de migration clients+logs, validation indépendante, autorisation explicite de merge ET Vercel. `NOT_RELEASE_AUTHORIZED`.

> **2026-10-12 — P0 SSE/CSRF hotfix [PR #938](https://github.com/hraaaaf/IAMINA-MVP/pull/938) : CI TECHNIQUE VERTE, NON FUSIONNÉ, NON DÉPLOYÉ.** HEAD exact `beeed3ecb60b68a9a30b5a9d46736f9a6f520e4d`, base `main`, 13 fichiers, DRAFT. [CI `38230019452`](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38230019452) 6/6 succès ; SQLite **2796**, PostgreSQL **2800** tests réussis ; Flutter **646** réussis, build PWA OK. Les 3 autres workflows (migration, P5-5, compagnon E2E) sont verts au même SHA. Les échecs Bearer précédents venaient d'une fixture test qui remplaçait globalement l'authentification native ; corrigée et vérifiée en CI. **Les déploiements Vercel identifiés utilisent toujours d'anciens commits GET-with-PHI**, sans divulgation réelle établie. Gates : clients distribués/caches, ingress/logs/rétention, sécurité/privacy/clinique, autorisations humaines de merge ET Vercel séparées ; la décision P3 dormant reste #937 non fusionnée. [Dossier de preuves](assessments/2026-10-11-v1-03-sse-production-drift-pr938.md) et [handover](handovers/2026-10-11-iamina-v1-03-option-a-p3-dormant-handover.md). `NOT_RELEASE_AUTHORIZED`.

> **2026-10-12 — Gate de migration V1-03 confirmé en lecture seule :** sur #938 HEAD `beeed3ec`, `frontend/pubspec.yaml`, `frontend/web/iamina_service_worker.js` et fallback `flutter_bootstrap.js` réutilisent tous `0.1.0+1`. Le service worker PWA hors hosted-review met `main.dart.js` en cache-first et le retire seulement au changement de schéma ; les anciens clients peuvent donc continuer à émettre le GET historique après un déploiement serveur tant que la mise à jour des builds/clients réels n'est pas prouvée. Vercel metadata 12/10 : review production `1e44ba57` et certified production `df004bcb`, tous deux anciens. Drains/retention et distributions natives inconnus (404 API n'implique pas zéro drain). **Next :** inventaire de parc autorisé, nouvelle version/build et cache schema distincts, vraie matrice d'upgrade synthétique, examen des politiques ingress/privacy et validation humaine de l'ordre de cutover. [Dossier section 15](assessments/2026-10-11-v1-03-sse-production-drift-pr938.md). Aucun merge/Vercel ; `NOT_RELEASE_AUTHORIZED`.

> **2026-10-12 — Exécution V1-03 PARALLÈLE (demande utilisateur) :** quatre pistes autonomes en lecture de preuve/QA : **A clients et PWA/GET→POST**, **B refus IA par installation (#934)**, **C OCR unité/provenance et avis clinique (#932/#923)**, **D Vercel ingress/drains/logs/rétention** ; **P3 dormant #937** a sa propre preuve technique. **Ne pas mettre ces audits en séquence inutilement.** Point de convergence : revue de 10 fichiers communs #932/#938, **5 blobs identiques** (CSRF/session auth/conftest/matrice CSRF/test transport) et **5 différents** (`ai.py`, `triage_vital.py`, `test_input_safety.py`, `openapi.json`, `api_client.dart`) avec conflits fonctionnels potentiels. Intégration/CI unique seulement après consolidation et preuves des risques ; autorisations humaines **merge et Vercel séparées**. Les mocks de consentement ne sont pas des tests vrais appareils, et l'API Vercel drains 404 ne prouve pas zéro drain. [Handover section 16](handovers/2026-10-11-iamina-v1-03-option-a-p3-dormant-handover.md). `NOT_RELEASE_AUTHORIZED`.

> **2026-10-12 — CONVERGENCE V1-03 :** [PR #941 DRAFT](https://github.com/hraaaaf/IAMINA-MVP/pull/941), HEAD `22ff929624c3860446b58ce6130852594d3060ed`, base `main@13b7cce1` ; composition #934 refus AI / #939 urgence SSE après auth/CSRF (en conservant les protections sans LLM de #932) / #937 P3 dormant / #940 build d'essai PWA `0.1.0+2`. **11/11 checks statiques passés, 25 workflows GitHub déclenchés**, [CI `38251414965`](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38251414965) et [P5-4A upgrade `38251414930`](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38251414930) initialement **queued**. Aucune certification globale avant verdict sur HEAD exact ; pas d'appareils distribués ni logs/drains prouvés, pas d'avis clinique indépendant. L'assemblage contient 87 fichiers cumulés et ne doit **pas** être fusionné simplement parce que les PR sources sont vertes. [Handover section 19](handovers/2026-10-11-iamina-v1-03-option-a-p3-dormant-handover.md). **NOT_MERGED / NOT_DEPLOYED / NOT_RELEASE_AUTHORIZED.**

> **2026-10-12 — PR #941, reprise CI après correction du test harness :** HEAD intégré initial `22ff9296` : 25 workflows dont 15 verts, 1 échec Developer portability macOS et 9 en cours au constat ; CI centrale ancien HEAD 2 jobs backend rouges (tests SSE obsolètes). Diagnostic : les tests historiques exigeaient l'interception et le log SSE **avant auth** que le nouveau code interdit, ainsi qu'un sous-processus benchmark sans `backend` dans le chemin Python sur macOS. Deux correctifs **tests uniquement** : `89327df0` (assertions urgence SSE après auth, no pre-auth logging), `d3562e8` (subprocess cwd backend). **Nouveau HEAD #941 `d3562e814e39d412516f421e66cb285fa7df50ce`**, 25 workflows relancés automatiquement ; au contrôle **3 SUCCESS, 8 in_progress, 14 queued**, zéro failure à cet instant ; [CI `38252290789`](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38252290789) queued, [Developer portability `38252290702`](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38252290702) in_progress, [PWA update `38252290695`](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38252290695) in_progress. Ne pas annoncer CI verte avant preuve exact-HEAD. [Handover section 20](handovers/2026-10-11-iamina-v1-03-option-a-p3-dormant-handover.md). Aucun merge ni Vercel ; `NOT_RELEASE_AUTHORIZED`.

> **2026-10-12 — V1-03 PR #941, recertification `d3562e8` : 24/25 workflows SUCCESS, dernier Android TD-008 IN_PROGRESS.** [CI principale `38252290789`](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38252290789) : **6/6 jobs verts**, SQLite **2865**, PostgreSQL **2869**, Flutter **688** tests passed et PWA built ; Developer portability macOS/Windows SUCCESS. [P5-4A Chrome recovery `38252290695`](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38252290695) devenu **SUCCESS après relance du seul job échoué** `114830462759` ; artefact `11749571584` retained. [TD-008 Android `38252291102`](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38252291102) première tentative n'avait pas atteint les tests (ADB Broken pipe après boot sans KVM) ; deuxième tentative job `114830488188` `in_progress` au dernier contrôle. **Ne pas annoncer 25/25.** Gates appareils/distributions réels, ingress/logs/drains, clinicien OCR, revues externes et autorisations merge/Vercel restent non franchis. [Handover §21–21a](handovers/2026-10-11-iamina-v1-03-option-a-p3-dormant-handover.md). `NOT_RELEASE_AUTHORIZED`.

> **2026-10-12 — TECHNICAL_CI_GREEN : V1-03 PR [#941](https://github.com/hraaaaf/IAMINA-MVP/pull/941) à HEAD exact `d3562e814e39d412516f421e66cb285fa7df50ce` : **25/25 workflows SUCCESS** sur GitHub. [CI centrale `38252290789`](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38252290789) 6/6 jobs verts (SQLite **2865** tests passés, PG **2869**, Flutter **688** + build PWA) ; [Developer portability `38252290702`](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38252290702) macOS/Windows vert ; [PWA update `38252290695`](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38252290695) vert en relance ciblée et artefact de preuve `11749571584` ; **dernier [Android TD-008 `38252291102`](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38252291102) job `114830488188` SUCCESS sur émulateur**. Rien n'a été mergé ou déployé. Reste : migration des clients historiques PWA/natifs réellement installés, preuves ingress/APM/logs/drains/rétention, refus IA sur vrais appareils, revue clinicien OCR et revues privacy/sécurité indépendantes, deux autorisations humaines *merge puis Vercel* distinctes. **CI complète ≠ V1-03 release autorisée**. [Handover section 22](handovers/2026-10-11-iamina-v1-03-option-a-p3-dormant-handover.md). Statut : `CI_CERTIFIED / DRAFT / NOT_MERGED / NOT_DEPLOYED / NOT_RELEASE_AUTHORIZED`.

> **Authority:** this is the single canonical forward tracker for IAMINA. If an issue, PR body, handover, assessment, AGENTS note, architecture note or historical phase document conflicts with this file on current status, priority or next work, **this file wins**. Historical documents remain evidence only.
>
> **Global audit:** 2026-09-17, reconciled against `main@df457cfdcc574439adb791fbfc44d484a1224417`, P5-4A merge #639, TD-014 merge #649, P5-6 release-gate evidence, #318/#320, `docs/TECHDEBT.md`, and the clarified local-first runtime boundary. The last explicitly frozen P5-6 candidate is `fb42e4d641b7b057607fe6a2de3d5104ccf15d0b`; later runtime/code changes mean it is retained as historical freeze evidence only, not as the current release candidate. The predecessor `5b27a22fc5c05a06e7eeeb0e841bb0e7dadce7f6` remains the last exact **remote development/certification** deployment proof. Vercel/Django/Neon is not the patient production runtime. No current release candidate exists until an explicit re-freeze is performed when the pre-real-patient gate is reactivated.
>
> **Canonical global progress:** **6/12 atomic roadmap lots CLOSED = 50.0%**. Atomic denominator: P5-0, P5-1, P5-2, P5-3, P5-4A, P5-4B, P5-5, P5-6 consent evidence engineering, P5-6A, P5-6B, P5-7, P5-8. Closed atoms currently retained: P5-0, P5-1, P5-2, P5-4A, P5-5 and P5-6 consent evidence engineering. The P5 whole-lot metric remains **4/9 = 44.4%** because P5-4B remains deferred and P5-6 remains open as a macro release gate. Retained MENA remains **32/38 = 84.2%** for its narrower scope.
>
> **Release posture:** `NOT_RELEASE_AUTHORIZED`. No current release candidate is frozen or authorized for deployment or real-patient processing. Engineering, UX, reliability, security and synthetic/non-patient work may continue. P5-6A/#318 and P5-6B/#320 are retained as mandatory **pre-real-patient gates**, not as the current engineering critical path.

## Product V1 — 29 approved decisions (2026-10-09)

> **Status:** product decisions **29/29 approved**; the V1 implementation lots below are **PLANNED, not automatically built, tested or clinically certified**. This forward product workstream supplements — and **does not erase or renumber** — the retained P5 pilot-readiness/release workstream, its \`6/12\` historical atomic completion baseline, or the mandatory pre-real-patient P5-6A/P5-6B gates.
>
> **Decisions source:** [IAMINA — 29-discussion register](https://app.notion.com/p/3f377c663362812dbe78cead75e71922). **Linked Notion canonical roadmap:** [01 — ROADMAP CANONIQUE](https://app.notion.com/p/3df77c66336281f5b308ec17f7f0a63b). The original source #28.1 means **intelligence/analytics BEFORE the chatbot**; our workshop subnumber #28.1 refers separately to **LLM isolation**. Do not interchange them.
>
> **Baseline inspected:** \`main@f6f5a0a07b9d9ae243dda699e1f5fe58c69fe192\`, CI run \`37836917174\` success. Existing clinical engines and companion contracts are retained; PRs #865/#866/#869 (Intent Envelope) and #918 (UX tests) are open and must be reconciled, not assumed merged. Existing first-use certification #879/#880 is evidence of that earlier, narrower flow, not certification for these new requirements.

### Goal and architecture

**IAMINA Intelligence Engine is independent of the chat surface.** Patient-scoped, provenance-bearing data → verified eligibility, units and timing → governed deterministic calculations, comparisons and observations → a versioned, evidence/uncertainty-bearing insight/decision envelope → the same authorized result in **Home, Reports and the guided IAmina conversation**.

A generative LLM may **only** generate non-patient generic wording or an opaque-token-only wrapper, with strict egress proof, no clinical authority and local final assembly. No patient message, history, measurements, demographics, clinical facts or correlated metadata may reach a third-party LLM. If privacy/policy/verification fails, **use no LLM**. Clinical predictions remain hidden research-only until independent scientific, clinical and regulatory approvals; no arbitrary one-month forecast.

### New implementation lanes — priority is proposed engineering order, not clinical authority

| Order | Lot | Priority | Deliverable and source decisions |
| --- | --- | --- | --- |
| 01 | **V1-01 — Full calculation and clinical-authority audit** | P0 | Enumerate every clinical, statistical, conversion, report and nutrition calculation and UI consumer; classify normative vs descriptive and fail closed on missing evidence. **#19 #11 #22** |
| 02 | **V1-02 — Intelligence Engine / governed patient context** | P0 | Reuse Clinical Twin, observations, evidence registry, longitudinal and multi-source contracts; one versioned patient-scoped fact/insight envelope with source, eligibility, uncertainty and authority, consumable by all three surfaces. **#28 original source-first intent #7 #18** |
| 03 | **V1-03 — Strict model/AI privacy boundary** | P0 | Enumerate all LLM egress paths, replace/disable patient-context prompts, enforce generic/opaque allowlisted payloads and negative egress tests, preserve effective global AI opt-out. **#28 workshop 28.1 #24 #26** |
| 04 | **V1-04 — True first-use and progressive profile** | P0 | Country/unit before targets, editable multi-treatment and unknown-type profile, no real-account demo records, existing-account continuity, secure recovery/app-lock, first-measure value, opt-in feedback; reuse previous merged first-use work. **#5 #7 #8 #9 #10 #11 #18 #22 #29** |
| 05 | **V1-05 — Guided IAmina conversation** | P0 | Deterministic question graph from opening, 2–4 options, reversible narrowing, repeat/back/free text locally routed, bounded responses, one main message, FR/AR/darija and RTL, non-floating chat mini-avatar. Home-only floating avatar. **#28 workshop 28.2/28.4/28.5 #6 #16 #27** |
| 06 | **V1-06 — Native-feeling CGM Integration Hub** | P1 | Manufacturer/model selection and allowed authorization, read-only connector orchestration behind IAMINA; authorized official APIs first, isolated audited adapters where lawful, legacy Nightscout compatibility, import fallback, real freshness/availability and revocation. No patient-run Nightscout requirement and no claim of universal CGM support. **#1 #25** |
| 07 | **V1-07 — Reliable intelligent capture** | P1 | Premium and precise glucose slider, unsaved-change guard, expandable secondary entry details; one editable meal draft from voice, text, form or assistive photo suggestions, natural portions, explicit human confirmation. **#12 #13 #14 #15 #17** |
| 08 | **V1-08 — Insights, reminders, notifications and deterministic reports** | P1 | Notification bell distinct from reminders, 2–3 upcoming reminders on home, one consented meaningful nonurgent insight per initial 24 h, chat/bell event-ID deduplication, opt-in weight trend, deterministic FR/AR PDF and CSV/XLSX exports. **#2 #3 #4 #20 #28 workshop 28.3** |
| 09 | **V1-09 — Premium UX, settings and accessibility** | P1 | Global and AI preference hierarchy, effective AI off without losing measurements, separate privacy/account actions and logout, Ramadan feature flag disabled, text copy/selection, home avatar target and reduced motion. **#16 #21 #23 #24 #26 #27** |
| 10 | **V1-10 — Predictive ML research in shadow** | P2 | Predefine scientifically meaningful target/horizon and population; ethical, isolated study data, temporal/external/prospective validation, calibration, bias and subgroups; no patient-facing predictions or effects on clinical advice or notifications. **#28 workshop 28.6** |
| 11 | **V1-11 — Whole-product certification and pilot safety gate** | Release gate | Cross-feature true first-use to first measurement/insight/chat, CGM and exports; clinical validation, egress/patient isolation, security/accessibility and exact-head CI/post-merge. P5-6A/P5-6B pre-real-patient/legal/data-residency/processor prerequisites remain mandatory. No Vercel deploy without explicit approval. **All 29** |

### V1-03 — #925 Inventaire statique des anciens clients SSE (2026-10-11)

- **Preuve source :** `frontend/pubspec.yaml` indique `0.1.0+1`; le client `ApiClient.chatStream` canonique construit `POST` JSON sans query patient. `backend/core/app_compatibility.py` dispose déjà d'une politique version/build et `GET /api/v1/app-compatibility` ; valeurs par défaut version minimum/récente `0.1.0` build `1`, configurables par environnement. **Sans version/build envoyé, décision = `version_unknown`, `compatible=null`, `update_required=false`**. Aucun appel de compatibilité observé dans les quatre fichiers source Dart inspectés (API partagé, main et mappings), **pas un inventaire de toutes les installations réelles**.
- **Non vérifié :** anciennes versions réellement distribuées ou encore actives, comportement de leurs appels GET, stratégie forced-update, réglages actuels d'environnement et journaux ingress, absence d'historique d'URL sensibles. Ne pas inventer de taux de clients migrés.
- **Next / gate privacy :** inventaire de versions/builds avec collecte minimale autorisée, déterminer la version minimum garantissant le transport POST, plan de migration/rollback sans redirection ni GET PHI, puis vérification des logs CDN/proxy/APM et rétention sur environnement synthétique. [Issue #925](https://github.com/hraaaaf/IAMINA-MVP/issues/925) mise à jour. **Aucun nouveau code, pas de release Vercel.**

### V1-03 — #923 OCR : dossier clinique de non-activation et matrice de preuve (2026-10-11)

- **Goal :** préparer la revue sans rendre l'OCR patient utilisable ni prendre de décision médicale implicite. [Audit #933](https://github.com/hraaaaf/IAMINA-MVP/pull/933) complété par commit **documentation uniquement** `5eaf5fafe2163ee308603e724f43c66feaee99f7`, fichier `docs/assessments/2026-10-11-v1-03-ocr-reachability-unit-audit.md`.
- **Constats source :** lecture OCR numérique sans unité / deux unités = aucune proposition ; HI/LO sont renvoyés sans valeur (`value=null`) et avec `needsConfirmation=true`, mais `confidence=1.0` ; une valeur unique lisible peut avoir `needsConfirmation=false` sans preuve de dialogue de confirmation ; valeurs 401–600 mg/dL non reconnues par le motif courant, bien que commentées. **Aucun écran patient courant relié à l'OCR** selon le précédent inventaire ; aucune capture optique validée.
- **Pack de revue** : scénarios sans unité, unités contradictoires, HI/LO, multiples valeurs, valeurs supérieures à 400, conversions, annulation, sauvegarde nulle sur refus, offline/retour, locales et accessibilité. **Critère future UI :** feature flag OFF, preuve de l'unité optique et confirmation **explicite** avant écriture, tests SQLite/PG et BEFORE/AFTER mêmes 3 viewports. Aucune validation clinique ni UI rendue par cet audit.
- **Gate restant :** clinicien qualifié tranche seuils, HI/LO et actions, privacy/processor contrôle l'egress et la persistance ; pas de merge/release/Vercel. Le dernier code certifié #932 reste `15cfe25f` (16/16), et la dernière caractérisation test de #933 `2828ee75...` (16/16) ; **ce nouveau commit de document n'a pas de certification CI qui lui soit attribuable**.

### V1-03 — Décision A : aliases P3 explicitement dormants pour V1 (#929)

- **Décision utilisateur : A, 2026-10-11.** Aucun alias HTTP `/api/v1/diabetes/*` exposé pour V1 ; conserver les routes canoniques `/api/v1/logs/*` et `/api/v1/ai/chat`, ainsi que le registre `diabetes` et son moteur clinique. Une activation P3 ultérieure exige un ADR et un lot indépendant de sécurité/auth/CSRF/consent/triage/clinique.
- **Code implémenté dans [PR DRAFT #937](https://github.com/hraaaaf/IAMINA-MVP/pull/937)**, branche `safety/v1-03-p3-dormant-manifest-triage-20261011`, commit `9cba062075768c8ebd8a4744ce77c3f0f1621535` basé sur #936 `62cc18bc` : le montage dynamique de `ModuleRegistry.all()` a été retiré de `diabetes.api.main` (dormance indépendante de l'ordre d'import). Le manifeste conserve le `url_prefix="/diabetes"` **réservé et non monté** ; `interactive_endpoints` contient uniquement le vrai `/api/v1/ai/chat`. `DiabetesConfig.ready()` enregistre le triage depuis ce manifeste, sans l'alias fictif ; la comparaison middleware SSE ne mentionne plus le stream P3 dormant.
- **Tests prévus sur ce HEAD :** 404 sur alias chat/logs même avec texte urgent ; aucun provider IA ; absence de tous ces chemins dans OpenAPI et Django resolver ; triage d'urgence du vrai chat conservé ; processus Django neuf confirme qu'aucun montage automatique ModuleRegistry n'est tenté. Diff #936→#937 : **1 commit, 7 fichiers, 5 code/tests et 2 documents**, pas de nouveau endpoint ni DB/migration. **CI [#38174253867](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38174253867) lancée, conclusion non certifiée au moment de cette note.**
- **ADR adopté :** [ADR-0009](adr/ADR-0009-v1-p3-dormant-aliases.md) enregistré sur cette branche documentaire (commit `8af3b7b46d1339b8b333a5b936905edc6cf311de`). Il précise la règle V1 « aucune exposition P3 », l'enregistrement du seul chat canonique pour le triage et les gates si activation future. **La certification du code est indépendante de cet ADR.**
- **Premier essai CI #937 :** Ruff `I001` (deux blocs d'imports) signalé sur `9cba062...`, **pas** d'anomalie comportementale démontrée par ce lint. Correctif style-only `4d287bb1c8049b416b7e0f2c7ad5aa031c370ca7` sur les deux fichiers concernés ; [CI #38174457859](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38174457859) nouvelle exact-HEAD en cours. Aucune réussite revendiquée avant workflow complet.
- **Closeout code #937 vérifié :** HEAD exact `4d287bb1c8049b416b7e0f2c7ad5aa031c370ca7` : **16/16 workflows SUCCESS**, [CI #38174457859](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38174457859) **6/6 jobs SUCCESS**. Base PR **restaurée** sur `parallel/v1-03-module-alias-404-audit-20261011` (#936 SHA `62cc18bc...`), `DRAFT`, `merged=false`, `mergeable=true`, ahead 2, behind 0, diff 7 fichiers attendus. Aucun merge/Vercel. **Next exact :** handover canonique, cohérence issue #929 / Notion, puis audits V1-03 et vrais gates cliniques/privacy ; `NOT_RELEASE_AUTHORIZED`.

### V1-03 — #929 Mismatch manifest chat / logs router (preuve source 2026-10-11)

- **Observation source indépendante :** le manifeste `DIABETES_MANIFEST.interactive_endpoints` annonce `/api/v1/diabetes/ai/chat`, mais `DiabetesConfig.ready()` enregistre dans ModuleRegistry uniquement `diabetes.api.v1.logs.router` pour le module. Ce routeur définit `/logs`, `/logs/batch` et `/logs/{log_id}` ; aucune opération `/ai/chat`. Le routeur `ai_router` est monté séparément à `/v1`. **Même un futur montage de ce routeur logs à /v1/diabetes ne produirait pas l'alias chat promis.** TRIAGE_REGISTRY annonce la voie namespacée, mais cela ne crée pas d'endpoint HTTP.
- **Conséquence :** deux problèmes distincts avant toute activation P3 : (1) timing de montage établi dans le bootstrap Django CI isolé de #936 (registre vide à la construction, puis enregistrement dans ready()), (2) déclaration du manifeste incompatible avec le routeur effectivement enregistré. Aucun bypass CSRF ni fuite prouvés.
- **Arbitrage ultérieur (historique)** : la décision A d'octobre 2026 conserve les alias dormants ; [PR #937](https://github.com/hraaaaf/IAMINA-MVP/pull/937) porte le correctif explicite en certification. Toute exposition P3 future nécessitera une nouvelle décision et une revue indépendante. [Issue #929](https://github.com/hraaaaf/IAMINA-MVP/issues/929) suivie.

### V1-03 — #936 Diagnostic de la cause P3 par trace Django initialisation (2026-10-11)

- **Goal :** expliquer sans modifier de route pourquoi `ModuleRegistry.get("diabetes")` est enregistré mais `/api/v1/diabetes/logs/batch` demeure absent. **Dernière preuve certifiée** : PR DRAFT [#936](https://github.com/hraaaaf/IAMINA-MVP/pull/936) SHA `8330a3fc8a4f69095b198710b650a21567262572`, **16/16 workflows SUCCESS**, CI [#38142776367](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38142776367). `logs_router` est monté uniquement sous `/v1`; alias pas en URLconf ou OpenAPI. Cela ne prouvait pas la chronologie du registre.
- **Preuve d'ordre CI backend nouvelle :** `backend/core/tests/test_p3_dormant_alias_route_guard.py::test_fresh_django_bootstrap_registry_timeline` lance Django dans un Python propre et trace `ModuleRegistry.all()` depuis `diabetes.api.main` **avec registre vide AVANT** `ModuleRegistry.register()` de `DiabetesConfig.ready()`, puis module diabetes présent et `logs_router` monté uniquement sur `/v1`. Test passé dans les deux jobs backend de la [CI #38172670213](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38172670213) sur HEAD `62cc18bc0266838a98bbd7fe6b3ad8c794c82938` : **SQLite 2850 passed, 5 skipped, 3 xfailed, 177 subtests ; PostgreSQL 2854 passed, 1 skipped, 3 xfailed, 177 subtests**. Runner : Django 6.1.2 et Ninja 1.7.1. **Cause de timing confirmée pour cette construction CI**, pas une preuve de la totalité de la chaîne d'import ni une autorisation d'activer l'alias. Aucun endpoint modifié.
- **CERTIFICATION / CLOSEOUT engineering sur HEAD exact** `62cc18bc0266838a98bbd7fe6b3ad8c794c82938` : **16/16 workflows GitHub completed/success**, [CI #38172670213](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38172670213) **6/6 jobs SUCCESS** et contrôles Chrome/packaging tous verts. Diff depuis précédent HEAD certifié `8330a3...` : 4 commits / **2 fichiers** (test + assessment), sans runtime, DB ni CSRF ; diff parent #932 SHA `15cfe25fcc93fff00a1198d705fb683c7a2eb960` → HEAD **ahead 10 / behind 0 / 2 fichiers**. **PR #936 restaurée sur sa base #932**, vérifié `mergeable=true`, `DRAFT`, `merged=false`, HEAD inchangé. Aucune route exposée/merge/Vercel.
- **Gates OPEN** : arbitrage métier alias P3 dormant vs actif ; de plus, `DIABETES_MANIFEST.interactive_endpoints` annonce `/api/v1/diabetes/ai/chat`, mais `DiabetesConfig.ready()` ne déclare que `logs_router` (aucun chat), et le triage ne crée pas une route. L'ordre d'initialisation n'est donc qu'une des deux incohérences. Si dormant, réconcilier manifeste/triage/docs sans exposer. Si actif, construire routeur dédié et certifier auth/CSRF/consent/triage SQLite+PG avant exposition et revue privacy/clinique. **Closeout exact-HEAD vérifié le 2026-10-11 :** 16/16 workflows SUCCESS sur `62cc18bc0266838a98bbd7fe6b3ad8c794c82938`, CI #38172670213 6/6 jobs SUCCESS ; PR #936 DRAFT/open, base #932 `15cfe25f`, mergeable=true, merged=false, HEAD inchangé. Gate P3 dormant/actif ouvert. **Next :** inventaire de compatibilité SSE / sécurité ingress et autres audits non bloqués ; aucun merge/Vercel/patient.

### V1-03 — #935 SSE legacy GET : anti-redirect et contrat migration POST (2026-10-11)

- **Goal sans gate humain :** empêcher toute réouverture involontaire de `GET /api/v1/ai/chat/stream?message=...` et toute redirection susceptible de recopier du texte patient dans une nouvelle URL, sans toucher aux endpoints patient. L'upgrade recommandé est `POST /api/v1/ai/chat/stream` avec JSON body, pas un redirect.
- **Code/test isolé :** sur [PR DRAFT #935](https://github.com/hraaaaf/IAMINA-MVP/pull/935), `backend/core/tests/test_v1_03_legacy_sse_no_provider.py` ajoute (1) GET synthétique 405, sans header `Location` et sans reflet du marqueur, provider IA jamais instancié, (2) validation OpenAPI que le chemin expose `post` avec `application/json` et pas `get`. Rapport `docs/assessments/2026-10-11-v1-03-sse-ingress-legacy-csrf-audit.md` actualisé. Diff initial **deux fichiers tests/docs**, aucun runtime modifié.
- **Certification engineering clôturée 2026-10-11 :** [PR #935](https://github.com/hraaaaf/IAMINA-MVP/pull/935) HEAD exact `5f2378ee7935bb64b5af850b6bfb2e68a9a49ebe` : **16/16 workflows GitHub `completed/success`** ; [CI #38159577622](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38159577622) **6/6 jobs success** (Flutter analyse/tests/PWA, backend ruff/pytest, PostgreSQL, secrets/scope/PR size). La base PR **restaurée** sur `safety/v1-03-glucose-ocr-unit-provenance-20261011` (#932, SHA `15cfe25fcc93fff00a1198d705fb683c7a2eb960`) ; `get_pr_info` a confirmé **mergeable=true, DRAFT, non fusionnée**, HEAD inchangé. Diff parent → HEAD **ahead 7 / behind 0, deux fichiers tests+doc uniquement** ; diff depuis précédent HEAD #935 `2270dc0644...` : ahead 3, behind 0, mêmes deux fichiers. Aucun merge/Vercel.
- **Limites et gates toujours OPEN :** ceci ne prouve ni log-redaction/retenue effective en CDN, Edge, APM ou WAF, ni compatibilité des anciens clients réellement installés. Ne pas exposer de GET PHI, ni traiter des patients réels, ni déployer sur Vercel sans autorisation explicite.
- **Next exact :** mettre à jour issue #925 et Notion avec les preuves du closeout, puis poursuivre l'inventaire des clients historiques / politique de migration et préparer audit de logging ingress autorisé avec données strictement synthétiques. Les revues privacy/clinique/sécurité et la certification sur vrais appareils restent des gates humains avant release.

### V1-03 — Quatre audits + tests de caractérisation vérifiés, sans activation (2026-10-11)

- **Goal de ce lot :** établir la preuve source des risques OCR, consentement, SSE/CSRF et alias de module, ajouter des tests minimaux empêchant les régressions avant remédiation fonctionnelle. **Succès engineering de ce sous-lot : 4 rapports + 4 tests sur 4 PR isolées, avec leurs suites GitHub exact-HEAD vertes.** Ce n'est **pas** une validation patient, une correction de tous les risques ou une approbation clinique/privacy.
- **Base commune :** DRAFT [#932](https://github.com/hraaaaf/IAMINA-MVP/pull/932) `15cfe25fcc93fff00a1198d705fb683c7a2eb960`. Les quatre PR sont **DRAFT**, base restaurée sur `safety/v1-03-glucose-ocr-unit-provenance-20261011`, `mergeable=true`, non fusionnées. Diffs contrôlés sur la baseline commune : seulement tests/documents; aucun code applicatif ni réglage d'environnement modifié.
- **OCR #923 / [#933](https://github.com/hraaaaf/IAMINA-MVP/pull/933)** : `docs/assessments/2026-10-11-v1-03-ocr-reachability-unit-audit.md` et `frontend/test/glucose_ocr_activation_boundary_test.dart` ; 170 Dart ciblés sans appel OCR hors définitions, HI/LO et multi-candidats caractérisés, nouveau caller non revu interdit par test. SHA du code certifié **`2828ee75dff42ec33843ee9fb95d896440aa4ecf`** ; [CI #38134510579](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38134510579).
- **Opt-out #924 / [#934](https://github.com/hraaaaf/IAMINA-MVP/pull/934)** : `docs/assessments/2026-10-11-v1-03-ai-optout-scope-audit.md` et `frontend/test/services/v1_03_optout_scope_regression_test.dart` ; refus « sans IA » temporaire en mémoire, révocation serveur différente, injections principales vérifiées. SHA **`2901b2e69beec2c69377279d986b0fb7315554d3`**, [CI #38134513649](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38134513649). **Gate** : arbitrage local persistant vs retrait global ; redémarrage/multi-appareils non certifiés.
- **SSE/CSRF #925/#927 / [#935](https://github.com/hraaaaf/IAMINA-MVP/pull/935)** : `docs/assessments/2026-10-11-v1-03-sse-ingress-legacy-csrf-audit.md` et `backend/core/tests/test_v1_03_legacy_sse_no_provider.py` ; GET patient obsolète doit 405 sans invocation LLM, POST body et CSRF couverts. SHA **`2b66192165dfe342c777b815e1ec55577bfb3af2`**, [CI #38134516790](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38134516790). Logs réels ingress/CDN/APM et anciens clients non audités.
- **Registry #929 / [#936](https://github.com/hraaaaf/IAMINA-MVP/pull/936)** : `docs/assessments/2026-10-11-v1-03-p3-module-alias-404-audit.md` et `backend/core/tests/test_p3_dormant_alias_route_guard.py` ; alias P3 absent alors que le registre est peuplé, garde OpenAPI/resolver ajouté ; cause racine du 404 et activation intentionnelle non décidées. SHA **`f8fe4f75973f189e3efe152c5976ae055e0a524a`**, [CI #38134518213](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38134518213).
- **Preuve GitHub au 2026-10-11 : 16/16 workflows `completed/success` sur chacun des quatre HEADs testés, total 64/64.** Les quatre CI `CI` ont six jobs conclus `success` chacune, comprenant **Backend — ruff + pytest**, **Backend — PostgreSQL source-of-truth**, **Frontend — analyze + tests + PWA build** et les gates scope/secrets/PR. La base PR avait été temporairement `main` pour lancer GitHub Actions `pull_request`, puis a été restaurée sans changer ces HEADs.
- **Réserve :** revues humaines clinique/privacy/sécurité à la fin du projet, preuve optique et UI OCR, persistance/retrait IA, logs CDN/legacy et choix de compatibilité P3 restent **OPEN**. `NOT_RELEASE_AUTHORIZED`, aucune fusion, déploiement Vercel ni patient. **29/29 décisions produit approuvées ; 0/29 déclarées totalement livrées** par ce lot.
- **Next exact :** préparer tests supplémentaires sans autoriser egress patient : matrice redémarrage/offline des refus IA, observation ingress/clients hérités en environnement autorisé, diagnostic import/version Ninja et parcours OCR sous gate clinique ; ensuite arbitrages humains, corrections ciblées, CI et closeout des sous-lots suivants.

### V1-03 — Option A sélectionnée : refus IA persistant sur cet appareil (#924)

- **Décision utilisateur explicite au 2026-10-11 : A.** « Continuer sans IA » doit rester effectif après redémarrage sur le **même appareil** ; **pas** de retrait serveur automatique ni effet sur les autres appareils. L'alternative B est écartée pour ce lot ; le gate choix A/B est clos, mais la validation technique/sécurité indépendante reste ouverte.
- **Goal :** aucun egress IA patient depuis ce client si marqueur de refus local enregistré, jusqu'à une nouvelle acceptation volontaire confirmée par serveur, notice courante, profil et levée du marqueur sécurisé. **Succès :** refus relu avant création des clients API, erreur de lecture fail-closed, écriture confirmée avant navigation, lecture de marqueur inconnu = refus, réacceptation requérant effacement sûr. La politique serveur indépendante est inchangée.
- **Code en [PR #934 DRAFT](https://github.com/hraaaaf/IAMINA-MVP/pull/934) :** `ConsentEvidenceStore` ajoute `iamina.ai_consent.local_declined_v1` à FlutterSecureStorage ; `ConsentService` initialise le refus au démarrage, le refuse immédiatement sans rediriger avant écriture, puis le communique au routeur ; `main.dart` lit et ferme le gate en erreur ; `ConsentScreen` persiste avant dashboard et efface le marqueur **seulement après une nouvelle acceptation vérifiée**. `app_router.dart` permet /consent malgré opt-out ; section Compte du profil affiche état par appareil et action « Réactiver IAmina avec mon consentement », localisée FR/EN/AR, uniquement si refus local.
- **Tests :** parcours widget d'écriture confirmée/erreur et réactivation/erreur d'effacement ; tests Mocktail du marqueur de stockage ; service avec consentement ancien et refus restauré, preuve manquante, instances indépendantes ; contrats d'injection/navigation/bootstrap. Harnais navigateur synthétique `profile-ai-disabled` et captures 390×844/768×1024/1280×900 ajoutés ; **BEFORE** dans les artefacts [UI #38147733708](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38147733708), **AFTER** dans [UI #38155284106](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38155284106), inspection visuelle effective aux trois résolutions consignée ci-dessous ; positions de défilement différentes, donc aucun test de différence pixel à pixel revendiqué.
- **Certification technique option A — 2026-10-11 :** PR #934 HEAD exact `f0b02165b478db6b6bb25d33f534a502ffa542f8` : **19/19 workflows SUCCESS**, [CI #38155284168](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38155284168) 6/6 jobs verts (Flutter analyze/tests/PWA, backend ruff/pytest, PostgreSQL, secret/scope/PR size), [captures UI #38155284106](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38155284106) 3/3 jobs Chrome verts. Le rouge précédent (684 pass, 1 fail) venait uniquement du test de source obsolète recherchant `void _declineWithoutAI()` devenu async; corrigé en test-only `02e8d07...`, sans relâcher le garde. **Inspection manuelle réelle des PNG BEFORE #38147733708 vs AFTER #38155284106** sur 390×844, 768×1024, 1280×900 : section Compte visible, état « IAmina désactivée sur cet appareil », CTA de réacceptation lisible, déconnexion séparée, pas de débordement visible ; **appréciation visuelle qualitative ~8/10**, inspection humaine des 3 images (pas de mesure automatique ni de test utilisateur) ; les deux captures ont des positions de défilement différentes et ne justifient pas une précision de score à la décimale. Mobile nécessite scroll pour afficher le compte et le libellé CTA se replie sur deux lignes; desktop a une densité faible, pas de défaut bloquant. Compare `15cfe25...`→HEAD : ahead 40, behind 0, 21 fichiers attendus, aucun fichier hors scope évident. **Closeout technique de cette PR vérifié :** base #934 restaurée par action GitHub sur `safety/v1-03-glucose-ocr-unit-provenance-20261011` (base SHA `15cfe25fcc93fff00a1198d705fb683c7a2eb960`), puis `get_pr_info` : **mergeable=true, DRAFT/open, merged=false**, HEAD inchangé `f0b02165...`; compare **ahead 40, behind 0, 21 fichiers attendus**. Ceci clôt la certification engineering option A, **pas** la revue privacy/clinique, les tests appareils réels ou le release gate. Aucun Vercel, merge, patient réel. Aucun Vercel, merge, patient réel.
- **Limites :** marqueur local **par installation**, pas synchronisé au serveur ; les refus antérieurs à l'installation du code n'étaient pas persistés, pas de migration rétroactive inventée. Si stockage sécurisé indisponible à l'écriture, ne pas annoncer le succès. Un test de classe / stockage mocké **ne constitue pas** une preuve sur deux vrais appareils, navigateur PWA fermé/réouvert ou traitement médical autorisé.
- **Next exact :** clôturer la traçabilité PR #934 / issue #924 / Notion sur la base restaurée, puis reprendre les prochains diagnostics V1-03 sans consentement patient. Avant toute éventuelle fusion ou release : revue indépendante privacy/sécurité/clinique et validation sur vrais appareils, sans prétendre que le 19/19 équivaut à une autorisation patient. **Aucun merge/Vercel.**

### V1-03 — Suite au 2026-10-11 : #934 fail-closed et #936 diagnostic certifiés séparément

- **Goal #934 :** interdire tout appel IA patient `ApiClient` ou `CompanionService` quand le `ConsentService` local n'est pas injecté, **avant token HTTP / requête au fournisseur**. La démo isolée n'émet pas de requête IA patient ; ses fixtures synthétiques sont explicitement consenties. Aucune activation automatique du consentement réel. Deux services durcis, tests négatifs, fixtures unitaires et harnais E2E corrigés. **Preuve exact-HEAD : `55aefac2038deef2389aa4f2955962526f939bb3`, 16/16 workflows `completed/success`, [CI #38147733716](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38147733716) 6/6 jobs SUCCESS dont backend pytest/ruff, PostgreSQL, Flutter analyze/tests/PWA et [E2E chat #38147733767](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38147733767) SUCCESS.** Premier HEAD `a6f3090` : 15/16 ; [E2E #38142335923](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38142335923) échoué sans appel `/api/v1/ai/chat` parce que le harnais indépendant omettait `ConsentService`, conformément au nouveau refus ; injection **synthétique uniquement** ajoutée au harnais puis E2E prouvé vert. [PR #934](https://github.com/hraaaaf/IAMINA-MVP/pull/934) de nouveau sur base `safety/v1-03-glucose-ocr-unit-provenance-20261011` à `15cfe25f`, **ahead 16 / behind 0, diff 9 fichiers, mergeable, DRAFT, non fusionnée**.
- **Goal #936 :** discriminer un alias route P3 `/api/v1/diabetes/logs/batch` non monté d'un alias monté mais non résolu, sans activer de nouveau routeur. **Preuve exact-HEAD `8330a3fc8a4f69095b198710b650a21567262572` : 16/16 workflows SUCCESS, [CI #38142776367](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38142776367) 6/6 jobs dont backend PostgreSQL/Flutter.** Le même `logs_router` existe dans `ModuleRegistry` mais `api._routers` le monte seulement sous `/v1`. Pas d'alias HTTP/OpenAPI ; sa cause temporelle et le choix de le rendre actif ne sont **pas** prouvés. [PR #936](https://github.com/hraaaaf/IAMINA-MVP/pull/936) DRAFT sur #932, mergeable, diff 2 fichiers test/rapport, non fusionnée.
- **#935 ingress lecture seule :** projets Vercel `iamina-review` et `iamina-certified` identifiés ; la réponse metadata ne prouve ni redaction ni rétention ; `list_drains` = erreur HTTP 404 **non interprétable comme absence**. Aucun log patient consulté, aucun changement infra, commit doc-only #935.
- **Statut vérifié :** sous-lots **#934 correction technique et #936 diagnostic clos côté preuves CI**, pas les gates produit/médicaux. Les audits initiaux avaient 64/64 workflows au total sur leurs propres commits ; **32/32** supplémentaires sont prouvés ici sur #934/#936, sans confusion avec les anciens HEADs. Quatre PR de revue restent DRAFT et non mergées.
- **Gates encore OPEN :** #924 choix persistance du « sans IA » versus révocation serveur globale, tests redémarrage/offline/multi-device ; #929 activation ou non de l'alias P3 ; #923 UI OCR/provenance optique/clinique ; #925/#927 logs ingress réels, vieux clients et privacy. Aucun signoff indépendant clinique/sécurité/privacy, aucune activation patient. **`NOT_RELEASE_AUTHORIZED`, pas de merge ou Vercel.** 29 décisions produit approuvées ne deviennent pas 29 décisions livrées.
- **Next exact :** traiter les diagnostics sans gate restant et clarifier les deux arbitrages humains (#924, #929) lorsque nécessaire, puis tests ciblés/CI exacte, revues indépendantes au gate final et closeout GitHub + post-merge une fois autorisés.

### V1-03 — Glucose OCR / provenance explicite de l'unité #923 / DRAFT #932 (2026-10-11)

- **Goal :** jamais de valeur OCR glycémique exploitable lorsque l'unité mg/dL ou mmol/L est absente, invalide ou contradictoire ; ne jamais la déduire de la grandeur numérique.
- **Code :** `backend/media/vision.py` ne demande plus au modèle de deviner l'unité, refuse unité manquante/invalide, NaN et booléen avant de produire `value` (fallback `value: null`). Le `unit: mg/dL` conservé avec `value: null` est **uniquement le placeholder historique du schéma**, pas une valeur ou unité reconnue. `frontend/lib/core/clinical/glucose_ocr_shield.dart` exige **une seule** unité explicite reconnue avant tout résultat numérique, et renvoie valeur nulle si aucune ou deux unités ; conversion mmol/L historique conservée. `HI/LO` et la logique d'autres chiffres restent à arbitrer cliniquement. Aucun egress cloud de photos patients n'est autorisé ou ouvert par ce lot.
- **Tests :** `backend/media/tests/test_vision_provider_boundary.py` étend les fixtures synthétiques avec absence/null/invalide/booléen/NaN/non-objet et unités explicites ; `frontend/test/glucose_ocr_unit_provenance_test.dart` protège les nombres sans unité, étiquettes contradictoires et cas unitaires mg/dL/mmol/L. **Ces tests ne prouvent ni lecture optique réelle ni l'accessibilité UI du helper**.
- **Scope/pile :** [issue #923](https://github.com/hraaaaf/IAMINA-MVP/issues/923), [PR #932](https://github.com/hraaaaf/IAMINA-MVP/pull/932) DRAFT, empilée sur #931 → #928 → #926 → #922 ; HEAD code `4fabb9f66ba9baaf6a5830466a6e9c05b068d136`, diff **4 fichiers, 2 commits devant/0 derrière** avant le closeout. La **CI exact-head du commit documentaire suivant reste à établir** ; aucune affirmation de 15/15 sans résultats.
- **NO-GO release :** validation clinique indépendante de la provenance de l'unité, provenance optique, intégration UI réelle, France/Maroc unités/langues et cas d'urgence, consentement/egress #924, sécurité #928 et processor/pilote non acquis. L'utilisateur a demandé de reporter la revue au **gate final du chantier**, pas de la considérer approuvée. **Aucun merge ni déploiement** pour ce lot. [Handover du sous-lot](handovers/2026-10-11-iamina-v1-03-ocr-unit-provenance-handover.md).

### V1-03 — Confidentialité logs HTTP client #930 / DRAFT #931 (2026-10-11)

- **Goal :** supprimer dans le client API Flutter partagé un intercepteur Chopper de diagnostic susceptible de journaliser les en-têtes `Authorization` et les corps de requête contenant des données patient lorsque des listeners sont actifs. Il s'agit d'un **risque conditionnel démontré par lecture du code**, pas d'une fuite réelle constatée.
- **Preuve de correction :** la suppression de `CurlInterceptor()` dans `frontend/lib/services/api_client.dart` laisse `TimeoutInterceptor`, `AuthInterceptor` et `RetryInterceptor` intacts ; un nouveau test Flutter `no_sensitive_chopper_logging_contract_test.dart` empêche de réintroduire un intercepteur Curl/HTTP de journalisation dans la configuration centrale. Diff par rapport à #928 : **2 fichiers, 1 ligne supprimée + 25 lignes de test**, aucun changement d'API, de cookie, de sécurité serveur ou de saisie patient.
- **Dernier HEAD technique vérifié :** `590d627f045bff406ad8a054ed13cb48c119bbd3` (commit CI à arbre Git inchangé après `a99e57b0`) : **15/15 workflows GitHub SUCCESS**, [CI #38105654095](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38105654095), Flutter/PWA, backend SQLite/PostgreSQL, Chrome et iOS/mobile verts. **Le présent commit documentaire aura son propre SHA, à recertifier exact-head**, sans transférer automatiquement ce résultat.
- **Empilage :** [issue #930](https://github.com/hraaaaf/IAMINA-MVP/issues/930) ; [DRAFT PR #931](https://github.com/hraaaaf/IAMINA-MVP/pull/931) basée sur [DRAFT #928](https://github.com/hraaaaf/IAMINA-MVP/pull/928), parent SHA `3be13de4`, contrôle **ahead 2 / behind 0 / 2 fichiers**, mergeable et non mergée avant closeout docs. Base `main` autorisée **temporairement** uniquement pour les 15 vérifications sur le nouveau SHA ; remettre #931 sur #928 après vérification. Conserver le parent #928 inchangé.
- **NO-GO release :** aucune approbation réellement indépendante sécurité/privacy ; revue des autres sinks d'observabilité et contrats clients nécessaire, plus les gates login-CSRF, cookie+Bearer, triage urgent, #923/#924, processor/CNDP et pilotes déjà ouverts. Aucun merge ni déploiement Vercel. [Handover canonique du sous-lot #931](handovers/2026-10-11-iamina-v1-03-client-curl-logging-handover.md).

### V1-03 — CSRF transversal #927 / enfant DRAFT #928 (2026-10-11)

- **Goal :** refuser avant mutation toute opération unsafe `/api/v1/` présentant un cookie de session sans CSRF, qu'un Bearer réel/falsifié soit présent ou non. Garder l'auth native Bearer-only, le re-login web et le SSE urgent avec CSRF valide.
- **Preuve du HEAD code + tests `513655b885092c923fdba7e265cce273d323a101` :** **15/15 workflows exact-head GitHub SUCCESS** ([CI #38104035936](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38104035936)). Backend SQLite **2 844 passed, 5 skipped, 3 xfailed, 177 subtests passed** ; PostgreSQL **2 848 passed, 1 skipped, 3 xfailed, 177 subtests passed** ; Flutter **660 passed, 1 skipped**, PWA build, migrations, Chrome, iOS/mobile packaging, Protected Shadow et secret hygiene verts.
- **Perfection pass prouvé :** inventaire dynamique via `api.get_openapi_schema()` de **28 opérations unsafe avec `SessionAuth`** (39 opérations unsafe en tout). Le test résout chaque chemin côté Django, vérifie cookie sans CSRF → **403** et cookie+Bearer falsifié sans CSRF → **403**, sans effet métier. Il complète la matrice de quatre familles avec Bearer valide/jeton valide et le `POST` SSE urgent (403 sans CSRF, SSE 200 déterministe sans LLM avec CSRF). Ces tests ne sont pas une preuve exhaustive de compatibilité de clients externes ni de l'ingress.
- **Cause racine d'anciens rouges :** fixture pytest `FirebaseAuth.__call__` monkeypatchant indirectement `HybridBearerAuth` (alias), avec une observation SSE contaminée ; le mock a été retiré. Aucun incident/exploit patient prouvé. L'alias ModuleRegistry `/api/v1/diabetes/logs/batch` observé 404 et absent de l'OpenAPI est isolé dans [#929](https://github.com/hraaaaf/IAMINA-MVP/issues/929), sans relâcher le CSRF pour rendre le test vert.
- **Stack/release :** [PR #928](https://github.com/hraaaaf/IAMINA-MVP/pull/928) DRAFT, **base #926** (`fix/v1-03-sse-post-scoped-20261010`) rétablie et comparée au SHA `513655b8` : **16 commits ahead / 0 behind, 8 fichiers**, mergeable, non fusionnée. La base `main` est temporairement réutilisée seulement pour les 15 workflows du **dernier commit documentaire**, puis doit revenir à #926. Le nouveau SHA documentaire exige sa **propre CI exact-head** ; ne pas transférer le vert de `513655b8`.
- **NO-GO produit/release :** avis indépendant humain sécurité/confidentialité toujours absent ; politique cookie+Bearer, exception publique login-CSRF, accès triage urgent sans CSRF, inventaire runtime/ingress et ancien client, [#923](https://github.com/hraaaaf/IAMINA-MVP/issues/923), [#924](https://github.com/hraaaaf/IAMINA-MVP/issues/924), processor/CNDP, native/a11y/pilotes à arbitrer. **Aucun merge, Vercel, ni usage patient.** [Handover canonique](handovers/2026-10-11-iamina-v1-03-cross-route-csrf-handover.md).

### V1-03 — SSE POST CSRF route-level green backend, 2026-10-10

- **Latest code HEAD:** `2c61bc77a682d67b33cfba0f01bf90de4ac96ca4` in [DRAFT #926](https://github.com/hraaaaf/IAMINA-MVP/pull/926); first security test showed cookie-session POST SSE sans CSRF HTTP 200 instead of 403. Previous diagnosis did NOT prove the specific Django-Ninja callback root cause; route-level `check_iamina_csrf` now denies session-cookie requests without CSRF (also false Bearer header); keeps validated cookie and bearer path and deterministic urgent SSE. Synthetic tests include CSRF 403/403/200 and stream cancellation. **Engineering proof:** [CI #38086256670](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38086256670), SQLite 2833 pass, PG 2837 pass, Flutter 660 pass, PWA built; 12/15 exact-code-head workflows green as written, 3 UI/iOS runs ongoing. **The subsequent docs-only HEAD requires its own CI.**
- **Security debt explicitly open:** [#927](https://github.com/hraaaaf/IAMINA-MVP/issues/927) all unsafe cookie-session routes require dedicated CSRF validation; ingress/proxy body logs, legacy GET 405 clients and rollout remain unproven. #926 temporarily targets main only for CI, then must retarget to parent #922. [Scoped handover](handovers/2026-10-10-iamina-v1-03-sse-post-handover.md). #923 clinician OCR provenance, #924 privacy optout semantics, CNDP/processor/a11y/natives and P5-6 remain human gates. No merge, deployment or patient release. 29 V1 decisions approved, 0 fully delivered.

### V1-03 — session CSRF red diagnosed and hardening candidate (2026-10-10)

- **Real CI finding:** new synthetic cookie-session POST without CSRF returned HTTP 200, not expected 403, on exact-head 1bc5cb (backend red, [CI #38070369320](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38070369320)). Do not claim security validated merely because the earlier 44d6c27 code HEAD had 15/15 green; that older suite did not include this negative test. No observed patient exploit.
- **Candidate fix, requires new exact-head CI:** backend/amina/vercel_session_auth.py now rechecks all unsafe cookie-authenticated operations independent of Ninja's operation CSRF bypass; if an invalid bearer-looking header triggers the general API middleware exemption and falls back to session, SessionAuth overrides that exemption for cookie CSRF check. Tests assert 403 missing CSRF, 403 invalid bearer+missing CSRF, 200 with valid cookie+CSRF. Native verified bearer-only path remains intact. [Scoped handover](handovers/2026-10-10-iamina-v1-03-sse-post-handover.md). Until CI evidence, PR #926 stays DRAFT/NOT CERTIFIED; no merge/deploy. All previous human clinical/privacy/processor/legacy-GET gates remain.

### V1-03 — SSE POST transport #925 candidate (2026-10-10)

- **DRAFT STACKED PR [#926](https://github.com/hraaaaf/IAMINA-MVP/pull/926)** on #922: POST JSON SSE removes free-form patient chat text from request query/URL. Deterministic urgent middleware now emits SSE; per-chunk external TEXT egress is patient-scoped; no-store and PHI-safe error/triage logging. GET is disabled (405); coordinated old-client rollout is outstanding.
- **Code proof:** commit 44d6c27dd3aaa4bf5b60bdac6e112efba92a523c achieved **15/15 exact-head GitHub workflows SUCCESS**, [CI #38069507466](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38069507466), SQLite 2831 passed, PostgreSQL 2835 passed, Flutter 660 passed; packaging and UI succeeded. Two stale unit tests responsible for prior backend-red CI were corrected. **This new test/docs commit needs its own exact-head CI; previous success cannot certify it.**
- **Open safety gates:** early client-disconnect and session-only CSRF tests newly added; ingress/proxy body logging, legacy GET compatibility/rollback, independent clinical/security/privacy, #924 withdrawal semantics, #923 unknown glucose units, CNDP/processor, FR/AR/Darija/RTL, accessibility and P5-6A/B. #925 remains OPEN, #926 unmerged; no Vercel deploy or patient release. 29 decisions approved, 0 fully delivered. [Technical handover](handovers/2026-10-10-iamina-v1-03-sse-post-handover.md).

### V1-03 — Verified local AI notice required at patient network boundary (2026-10-10)

- **Goal / risk:** prior code correctly blocked an explicit session-local AI refusal, but allowed client AI calls to proceed when `hasDeclinedLocally == false` yet `ConsentService.hasConsent == false` (no currently verified notice). In addition, the legacy `ApiClient.chatWithAmina` REST path had no local guard. Backend global consent/egress protections remained independent and fail-closed; this was a **source-level defense-in-depth gap, not a demonstrated patient leak**.
- **Fix on code HEAD** `cf169c80960b4f404de630aaae91782a3356bdb9` in [PR #922](https://github.com/hraaaaf/IAMINA-MVP/pull/922): injected `ApiClient` now rejects locally unverified or explicitly declined AI before bearer/HTTP on patient chat stream, legacy chat, voice, transcription, meal image and web glucometer OCR. `CompanionService` similarly prevents patient text/voice egress before bearer or HTTP while preserving public synthetic audit demo without patient consent and honoring explicit local refusal. Typed refusal codes are distinct (`ai_declined_locally` vs `ai_consent_unverified_locally`) with FR/EN/AR screen copy. No server consent mutation; optional service constructors remain for legacy/testing and cannot prove global coverage alone.
- **Observable proof:** synthetic tests in `frontend/test/services/v1_03_local_decline_network_gate_test.dart` assert zero calls to bearer or mock HTTP for refusal and absent local proof. **Exact code HEAD 15/15 GitHub workflows SUCCESS**: [CI #38062688614](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38062688614) Ruff ✅; SQLite **2821 pass/5 skip/3 xfail**; PostgreSQL **2825 pass/1 skip/3 xfail**; Flutter **658 pass/1 skip** and PWA build ✅. [iOS packaging #38062688533](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38062688533), [Android packaging #38062688639](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38062688639), [Chrome screenshots #38062688623](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38062688623), [global routes #38062688570](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38062688570) and 10 other exact-head workflows also SUCCESS.
- **State / next:** exact-green **technical PR draft, not released**. Separate privacy follow-ups: [#924](https://github.com/hraaaaf/IAMINA-MVP/issues/924) user/product decision on device/session vs server-wide consent withdrawal, persistence/restart/multidevice; [#925](https://github.com/hraaaaf/IAMINA-MVP/issues/925) patient `GET /ai/chat/stream?message=...` query-string potentially entering request logs, no observed leak (migrate safely to POST streaming); clinician [#923](https://github.com/hraaaaf/IAMINA-MVP/issues/923) OCR unit provenance. New unverified-consent error copy has **no dedicated tri-viewport error-state BEFORE/AFTER**; earlier photo-CTA tri-viewport proof is valid only for that previous UI change. Formal a11y, clinical, CNDP/privacy, Groq processor, P5-6A/B and release/merge gates remain OPEN; no real patient use, Vercel deploy, or merge. **29 V1 decisions approved, zero fully delivered.** This docs commit needs its own exact-head workflows.

### V1-03 — Photo consent UI truthful, three-viewport visual proof, exact code HEAD GREEN (2026-10-10)

- **Goal:** local AI decline / missing current verified consent prevents the photo AI action while *manual food search, categories and logging remain accessible*. Strict provider-bound raw patient media block and patient server consent authority remain independent and unchanged.
- **Implementation since previous handover:** `ConsentService.hasConsent` now masks explicit local decline; shared consent-aware `ApiClient` and `CompanionService` deny local-declined patient AI network paths before auth/HTTP; meal photo and meal voice use shared client. `AddLogSheet` no longer derives photo AI eligibility from historic `aiConsentGivenAt`, but `context.watch<ConsentService?>()?.hasConsent ?? false`. `MealCapturePanel` disables `meal-photo-button` when false. Regression includes synthetic no-bearer/no-HTTP tests, static consent and client wiring, plus real Flutter widget test **verified consent → photo enabled → `declineLocally` → photo disabled, manual food search remains**.
- **Code HEAD VERIFIED:** `c96b69c4314744e727e10bcdcf700286a1daa7f1`, PR [#922](https://github.com/hraaaaf/IAMINA-MVP/pull/922) **OPEN/DRAFT/UNMERGED**. **15/15 exact-head workflows SUCCESS**, including [CI #38060367097](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38060367097) (backend SQLite/PostgreSQL and Flutter/PWA), [browser #38060366996](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38060366996), [iOS #38060367106](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38060367106), [Android #38060367195](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38060367195), and 11 other certification runs on this SHA.
- **BEFORE → Goal → reference/mockup → AFTER:** BEFORE exact Chrome patient screen `add-log-meal` from [run #38059314922](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38059314922); AFTER from [run #38060366996](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38060366996). Same 390×844, 768×1024 and 1280×900 screenshot fixtures, same layout/reference; only disabled CTA styling intended. Pillow pixel-level RGB comparison (non-zero channel difference, aligned image dimensions) shows **0.4366%**, **0.1775%**, **0.1198%** changed pixels respectively, i.e. **99.5634%**, **99.8225%**, **99.8802%** identical pixels, no viewport resizing. Screenshot observation confirms manual `meal-food-search`, categories, meal note and Save placement retained. **Visual stability score 9.9/10 (layout-only, not clinical/privacy/a11y certification)**; functional no-click widget test is separate. CI screenshot workflow green, but full manual a11y/language acceptance remains open.
- **Limits/human gate:** local decline is **ephemeral** and does not revoke authenticated server consent; optional service constructors and device restart/multidevice behavior need explicit privacy/product choice [#924](https://github.com/hraaaaf/IAMINA-MVP/issues/924). Unverified CGM/glucometer OCR unit authority [#923](https://github.com/hraaaaf/IAMINA-MVP/issues/923) needs clinician review; external patient raw media remains denied. P5-6A/B, CNDP, processor contracts, a11y/FR-AR-Darija remain open. **29 V1 decisions approved, 0 fully delivered**. The docs-only closeout SHA created from this checkpoint **must receive its own exact-head CI**; do not merge, deploy Vercel or authorize real patients.

### V1-03 — Media API manual fallback after privacy denial: exact-head 7/7 green (2026-10-10)

- **Code HEAD** `d48b5cbb7b3ad5cc3d817ea491033c9600b38f3f`, [PR #922](https://github.com/hraaaaf/IAMINA-MVP/pull/922) **DRAFT/UNMERGED**. **7/7 exact-head workflows SUCCESS**: [CI #38045938976](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38045938976) (SQLite **2821 passed, 5 skipped, 3 xfailed**; PostgreSQL **2825 passed, 1 skipped, 3 xfailed**, each 125 subtests); [migration #38045938953](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38045938953), [Companion E2E #38045938949](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38045938949), [Protected Shadow #38045938993](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38045938993), [UI geometry #38045939002](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38045939002), [Chrome screenshot #38045939111](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38045939111), [P5-5 rehearsal #38045938972](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38045938972) all **SUCCESS**.
- **PRE / bug:** new V1-03 external media guard intentionally raises `AIProcessorPolicyDenied` to prevent raw patient audio/image/document reaching external processors even with simulated approved processor + consent. `media/vision.py` and `media/voice.py` propagate this refusal; `ai/api/v1/ai.py` image and `ai/api/v1/voice.py` STT callers did not handle it, potentially returning an API error instead of the existing manual/low-confidence response.
- **Change:** only the API boundary catches `AIProcessorPolicyDenied`: meal image → empty food list + `fallback=true`; glucometer web OCR → `value=null` + `fallback=true` (unit field is response placeholder, **not a measured unit**); voice chat → empty transcript + existing error text; transcription-only → empty transcript/low confidence. `AIEgressDenied` (scope/consent denial) is **not** misreported as successful media interpretation. Seven synthetic tests cover six refused-provider scenarios plus voice absent-consent case; no provider network calls or patient data. Flutter `meal_capture_panel.dart` already shows unavailable notice and preserves manual food selection; no UI layout was changed.
- **CI regression honestly recorded:** [first new candidate CI #38045796018](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38045796018) failed pytest collection because fixture name `request` is reserved. Renamed test-only fixture to `fake_request` on `d48b5cb`, followed by 7/7 green. **Separate medical safety finding, not fixed or clinically signed off:** `backend/media/vision.py::_GLUCO_USER` asks external OCR to guess unit from number magnitude and normalizes invalid/missing unit to `mg/dL`; `frontend/lib/core/clinical/glucose_ocr_shield.dart` assumes mg/dL when no mmol token. External cloud OCR is currently blocked; native OCR still merits high-priority deterministic unit-evidence review with a clinician, explicit user confirmation and synthetic adversarial tests before release.
- **Status:** V1-03 remains **OPEN**; independent clinician/privacy/CNDP/Groq/security/natives FR-AR-Darija/RTL/a11y reviews, visual same-viewport BEFORE/AFTER for future UI changes, global AI opt-out coverage and P5-6A/B release gates outstanding. This closeout documentation commit requires its **own exact-head CI**; no merge, Vercel deployment or real patient authorization. **29 decisions approved, 0 fully delivered**.

### V1-03 — Raw patient media external egress fail-closed, code HEAD green (2026-10-10)

- [PR #922](https://github.com/hraaaaf/IAMINA-MVP/pull/922) code candidate `d1abf68056f0b5d4ded534a5f2afb8aff2e3c0dd`, **OPEN/DRAFT/unmerged**. Exact-head [CI #38043299895](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38043299895) **SUCCESS** (SQLite **2814 passed/5 skipped/3 xfailed**, PostgreSQL **2818 passed/1 skipped/3 xfailed**, 125 subtests; Ruff and LLM/AI egress anti-bypass succeeded); [migration drift #38043299841](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38043299841), [Companion E2E #38043299888](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38043299888) and [Protected Shadow token-only synthetic live #38043299942](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38043299942) all **SUCCESS**. Dedicated Flutter job skipped; not frontend certification.
- **PRE:** `media/voice.py` and `media/vision.py` send raw audio/image to Gemini through `llm.runtime.execute_external_provider_call` once scope+granular consent and approved processor policy succeed. `media/documents/extractors/image.py` delegates to VisionBackend with its own local eligibility check. Current Gemini policy is **PENDING**, so no actual network patient-data leak was demonstrated, but future approval alone could previously open raw-media egress without V1 privacy evidence. The `llm.factory` static-generic text check does **not** protect image/audio.
- **Fix and proof:** new `backend/core/external_media_v1.py` rejects every non-text external operation **including future unknown modalities**; invoked in `backend/llm/runtime.py` after scope/processor checks and before provider/circuit-breaker/transport construction. Six synthetic scenarios `meal_vision`, `glucometer_ocr`, `voice_chat`, `voice_transcription`, `document_ingest` (image/document) simulate approved processor plus real synthetic patient+granular consent and require **zero vendor calls**; additional negative consent absent/revoked and unknown future modality tests. Legacy circuit-breaker/error tests mock only this new gate in isolated synthetic transport simulations. No network media test sends patients.
- **Real red resolved, not hidden:** previous [CI #38042757860](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38042757860) failed at Ruff I001 for import spacing in `external_media_v1.py`; PostgreSQL and other three workflows were green. Commit `d1abf68` only corrected the import spacing, then exact-head CI **4/4 green**. Media capture/vision/STT cloud capability is therefore **intentionally unavailable** until a separately governed privacy-preserving transport contract exists. Do not claim feature equivalence, approved external media or all V1-03 gates closed.
- Remains **OPEN**: true global AI opt-out/intentional-local UX, other direct model routes and complete egress inventory, native FR/AR/Darija/RTL and a11y review, qualified clinician/privacy/legal/CNDP/Groq reviewers and true-release gate. This new docs-only SHA needs exact-head CI before closeout. No merge, Vercel, pilot or real patient authorization.

### V1-03 — Protected Shadow provider-direct edge tightened, 4/4 code workflows green (2026-10-10)

- [PR #922](https://github.com/hraaaaf/IAMINA-MVP/pull/922) technical HEAD `bc31fe06d4efb9279968893d1c5399d54b6882bb` **OPEN/DRAFT/unmerged**. Exact-head [CI #38042006742](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38042006742) **SUCCESS** (SQLite **2802 pass/5 skip/3 xfail**, PostgreSQL **2806 pass/1 skip/3 xfail**, 125 subtests; Ruff and gateway/egress anti-bypass passed), [migrations #38042006680](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38042006680) **SUCCESS**, [Companion E2E #38042006751](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38042006751) **SUCCESS**, and [Protected Shadow three-call synthetic live probe #38042006598](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38042006598) **SUCCESS** (43 targeted tests passed; machine_passed true; 3 planned non-patient token-only Groq calls; FR, Darija Arabic and Latin all passed). Flutter dedicated job skipped; not certified.
- The OFF-by-default staff-only `companion/protected_provider_shadow.py` adapter calls `complete_text` **outside** `llm.factory`. Independent last-hop validation now rejects all unapproved locale/script pairs and nonopaque token forms **before** processor check or provider construction in both normal and internal-live shadow modes; negative tests include injected metadata. Only locales `fr/en/ar/ar-MA` with predefined scripts are allowed. This **does not** authorize unrestricted patient-context prompts, clinician use, release or patient processing.
- First shadow candidate `9fd4e30` [probe #38041934929](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38041934929) FAILED at Ruff import ordering **before network**; corrected to `bc31fe0` without weakening validation. Clinical/native language/privacy/accessibility and UX BEFORE/AFTER reviews, consent/opt-out, image/audio boundaries and pilot gate remain OPEN. **No merge, Vercel or patient release.** This new docs-only commit still needs exact-head CI.

### V1-03 — Strict external text egress gate technically green (2026-10-10, NOT released)

- [PR #922](https://github.com/hraaaaf/IAMINA-MVP/pull/922) code HEAD `8292a130a674e132f011aea3d1d819547fba0571` **OPEN/DRAFT/unmerged**. Exact-head [CI #38037493525](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38037493525) **SUCCESS** (SQLite **2791 passed / 5 skipped / 3 xfailed**; PostgreSQL **2795 passed / 1 skipped / 3 xfailed**; 125 subtests). Ruff, gateway anti-bypass and egress anti-bypass succeeded. [Migration #38037493457](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38037493457) **SUCCESS**; [Companion E2E #38037493521](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38037493521) **SUCCESS**. The dedicated Flutter job was **SKIPPED by scope**, NOT a Flutter certification.
- New fail-closed boundary: `backend/core/external_text_v1.py` enforces an **exact static generic (non-patient) prompt pair** at `backend/llm/factory.py::_execute_external_complete`, before the network operation. Anonymization by regex alone is not anonymity proof; even when processor, consent and FinOps would otherwise permit text egress, any dynamic patient-content prompt is denied. Six synthetic adversarial values/languages were tested at the actual guarded outbound provider call path. Existing synthetic FinOps tests use the fixed approved generic fixture. This gate is for the `llm.factory` **text-provider boundary**, not evidence that all media or directly invoked shadow adapters are certified.
- New gate is intentionally *not* a general-purpose patient narration capability. Chat/stream and the legacy narrator may still **construct** patient-derived prompts internally; the external text gateway now refuses their transmission. Local-only behavior and failure UX must be checked separately. `companion/protected_provider_shadow.py` uses an independent OFF-by-default, staff-gated, opaque-token `complete_text` adapter; verify that specific boundary independently before any experimental use. Audit image/audio and global opt-out separately.
- V1-03 and **all 29 approved decisions remain OPEN/not fully delivered**. Mandatory security/privacy and qualified clinician, native FR/AR/Darija/RTL, accessibility, egress/UX BEFORE→AFTER and release gates still apply. No merge, real patient, Vercel or pilot authorization. This documentation update is a **new HEAD** and requires its own exact-head CI.

### V1-03 — Second safety slice technically green, release still gated (2026-10-10)

- [PR #922](https://github.com/hraaaaf/IAMINA-MVP/pull/922), code HEAD `c2effc096f86eb08e7c73118e17042fec3106ba2` **OPEN/DRAFT, unmerged**. [CI #38036057381](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38036057381) **SUCCESS**: SQLite 2785 passed / 5 skipped / 3 xfailed; PostgreSQL 2789 passed / 1 skipped / 3 xfailed, 125 subtests; anti-bypass and OpenAPI SUCCESS. [Migration #38036057344](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38036057344) and [Companion E2E #38036057367](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38036057367) **SUCCESS**. Dedicated Flutter test/PWA CI job **SKIPPED by scope**; do not claim its certification.
- Additional local-only `/ai/doctor-brief`: patient-authenticated deterministic recorded-count / descriptive-mean summary, with no LLM prompt, no CGM TIR/CV/GMI promotion, synthetic tests for no consent, authorization, patient separation, insufficient data, and FR/EN/AR/ar-MA candidate copy. `companion/narrator.py` no longer logs text of a model-authored Doctor Brief or patient ID in its success log; regression added. Translations/clinical language require independent qualified review.
- Previous failing CI [#38035782616](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38035782616) correctly identified two stale gateway-reference tests plus a forbidden mock string in anti-bypass scanner; tests corrected **without weakening the scanner or restoring patient egress**.
- **V1-03 remains OPEN**: `companion/conversation.py` still forms user/history/memory/clinical prompts in chat and stream; `companion/narrator.py.summarize` builds a patient-derived prompt; final provider-bound payload, external-model generic/opaque allowlist, global opt-out, UI `ai_provider=fallback` and clinical/native-locale/a11y proof remain unclosed. Processor network PENDING; **no actual external patient-data transfer is proven**. Clinical/privacy approvals, merge, post-merge, real patients and Vercel are NOT authorized by green CI. Reconfirm the new docs-only SHA with exact-head workflows before treating this closeout as current.

### V1-03 — Technical candidate in draft (2026-10-10, NOT released)

- [PR #922](https://github.com/hraaaaf/IAMINA-MVP/pull/922), candidate clinical-code HEAD `8ca3ac69657b5c2c7014286514af8231292f82e2`, separate branch `security/v1-03-summary-local-only-20261010`, **OPEN/DRAFT/unmerged**. This does not close V1-03 or any of the 29 complete decisions.
- Bounded fixes: `/ai/summary` emits one local deterministic pattern report without its former double model-formatting path; `run_clinical_analysis` prevents raw CGM row fraction from authorizing normative patterns; `/ai/summary` returns `project_public_kpis` rather than raw SQL CV/TIR/TAR/TBR/GMI; `DiabetesEngine.analyze` masks unverified normative CGM and suppresses the raw TIR trend/label.
- **Technical parent-HEAD proof only:** [CI #38034929969](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38034929969) SUCCESS, SQLite **2780 passed / 5 skipped / 3 xfailed**, PostgreSQL **2784 passed / 1 skipped / 3 xfailed**, [migration drift #38034930096](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38034930096) SUCCESS, [Companion real-chat E2E #38034930097](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38034930097) SUCCESS. The main CI's dedicated Flutter analyze/test/PWA job was **SKIPPED by scope**, not counted as a tested frontend.
- Remaining P0/privacy and clinical gates: actual final provider-bound prompt of Doctor Brief, chat/stream and other LLM routes; global opt-out, consent, identity, language and access-negative testing; recorded AGP/chart truthfulness; `ai_provider=fallback` may misleadingly display degraded AI mode; qualified clinician, security/privacy, native FR/AR/Darija/RTL + accessibility and release review. V1-01 #920 / V1-02 #921 remain draft. **No authorization for merge, real patients or Vercel deployment**.
- Detailed proof: [V1-03 assessment](assessments/2026-10-10-v1-03-summary-cgm-safety-audit.md) and [handover](handovers/2026-10-10-iamina-v1-03-summary-cgm-handover.md). Documentation commit requires **fresh exact-HEAD CI**; the parent-HEAD success does not certify later commits.

### Critical path, parallelism and evidence

1. **Start with V1-01** (audit register, actual backend→frontend call graph, bad/unknown inputs, units and model authority). In parallel, non-invasive inventory of reused V1-02 contracts and external egress paths V1-03. Do not replace an already certified module merely because a new layer name exists.
2. **One vertical proving slice**: authenticated patient → eligible existing measurement → versioned, provenance-bearing deterministic observation → exact same fact, uncertainty and status in Home, Reports and guided Chat → prove no patient information can exit via LLM. This is the first functional milestone before broad visual changes.
3. **V1-04 and V1-05** follow the certified data/safety contracts; **V1-06** may progress in parallel once consent, patient isolation and manufacturer access checks are proven. Manual measurement remains usable without any CGM account.
4. **V1-07/V1-08/V1-09** converge capture, actionable observations and design consistency; refine against actual screenshots. **V1-10** is independent research and never a release dependency for descriptive V1.
5. Each lot requires exact **Goal → observable success → test evidence**. Backend Django/SQLite+PostgreSQL where relevant, provenance/negative/cross-patient tests, API/frontend/real navigation, and **BEFORE → written target → approved mockup → implementation → AFTER at identical viewports**, including 390×844, accessibility and honest visual score when UI changes.
6. **Never present an unverified CGM feed as real-time safety monitoring, a descriptive trend as causal/predictive medical advice, a demo record as real patient data, or an unreviewed narrator as clinical authority.** Emergency safety routing is independent from the 24-hour nonurgent attention budget and global AI toggle.
7. Deployment to Vercel remains human-approved separately. The historical P5 pilot release gate requires explicit release re-freeze and competent professional/legal authorization before identifiable real-patient processing. Historical progress figures are not transferable to V1-01…V1-11. **No V1 implementation completion percentage is claimed yet.**

### Traceability — all original 29 issue numbers

| Original remarks | Assigned implementation lots |
| --- | --- |
| #1 #25 | V1-06 |
| #2 #3 #4 #20 | V1-08 |
| #5 #7 #8 #9 #10 #18 #22 #29 | V1-04 (also V1-01/V1-02 for evidence and context) |
| #6 #16 #27 | V1-05 / V1-09 |
| #11 #19 | V1-01 / V1-04 |
| #12 #13 #14 #15 #17 | V1-07 |
| #21 #23 #24 #26 | V1-03 / V1-09 |
| #28 | V1-02 / V1-03 / V1-05 / V1-08 / V1-10 |

**Next exact:** establish the V1-01 full-calculation audit manifest on current main; check source→derivation→patient output, mark evidence gaps, author tests with no unsupported clinical promotion; then run exact-head checks and proceed with the first vertical proving slice. Keep P5 release gates untouched.

---

## North star

Ship one safe, measurable Morocco/MENA diabetes-companion PWA pilot, collect real evidence, then make an explicit go/no-go decision before broader rollout or a second disease capsule.

## Non-negotiable product boundaries

- Diabetes is the only live condition.
- IAMINA is a patient companion, not a physician replacement.
- Deterministic clinical/safety logic is authoritative; generative models may only narrate approved bounded output.
- No diagnosis, prescription, dose calculation, treatment optimization/change or autonomous medical instruction.
- Language/dialect enablement requires explicit safety parity; location never silently determines language or emergency jurisdiction.
- Pilot delivery is PWA-first. Native Android/iOS is deferred unless explicitly activated.
- **Patient runtime is local-first:** first device enrollment, subsequent reopen, core clinical persistence and required local workflows must not require Vercel, Neon, Firebase, SMTP or another remote processor to be reachable.
- `iamina-certified` on Vercel, its Django runtime and its dedicated Neon database are **development/integration/certification infrastructure**, not the patient production runtime.
- Remote account creation is disabled by default in the patient path and may be enabled only explicitly for a remote DEV/certification account flow. Remote account, synchronization or auxiliary services may degrade independently; their outage or credential rejection must not destroy local enrollment or valid local clinical state.
- Local enrollment is continuity state; Web/PWA patient access is additionally protected by the merged strong device-local WebAuthn app-lock from #649. IAMINA does not own a weak PIN/password fallback for this lock and does not receive biometric material.
- Engineering proof, human approval, legal/CNDP approval and real-patient authorization are separate gates.
- No identifiable real-patient health data may enter IAMINA until the pre-real-patient gate is explicitly completed and release is authorized.

---

# 1. Executive status

| Area | Canonical status | Forward consequence |
|---|---|---|
| **Global canonical roadmap** | **🟡 6/12 = 50.0%** | continue verified non-patient engineering and remaining unresolved debt |
| Gate A Secure Core | ✅ CLOSED / certified 10.0/10 | maintenance only |
| Historical P0 foundations / product truthfulness / agent governance | ✅ CLOSED | no reopening without new defect/evidence |
| Global UX / Dashboard / Journal | ✅ CLOSED | regressions only |
| Clinical Data Layer & Privacy foundation | ✅ MERGED | residual privacy debt remains under `docs/TECHDEBT.md` |
| Companion intelligence / proactive lifecycle | ✅ CLOSED through current convergence | no active forward feature lot |
| CGM gateway V1/V1.1/V2/V2.1 | ✅ CLOSED | physical-sensor evidence remains external if later claimed |
| P4-FRUGAL PRE-PILOT | ✅ CLOSED 10.0/10 | real pilot economics belong to P5-7 |
| MENA retained tracker | 🟡 32/38 = 84.2% | informational only |
| P5 whole-lot tracker | 🟡 4/9 = 44.4% | active program |
| P5-4A offline packaging | ✅ CLOSED / AUTH_LOCAL_FIRST + STRONG_LOCAL_APP_LOCK | local-first availability and WebAuthn app-lock are merged; keep regression coverage |
| P5-6 consent evidence engineering | ✅ CLOSED atomic sublot | retained as merged engineering evidence |
| P5-6 remote dev/cert infrastructure | ✅ EXACT_REMOTE_PATH_HEALTHY / NOT_PATIENT_PROD | proves Vercel/Neon dev/cert path for `5b27a22…`; does not define patient production topology |
| P5-6 last frozen candidate evidence | 🟠 HISTORICAL_FREEZE / NOT_CURRENT | `fb42e4d…`; runtime/code advanced later, so explicit re-freeze is required before any release attempt |
| P5-6 current release candidate | ⚪ NONE | must be created by an explicit exact-SHA re-freeze when the pre-real-patient gate is reactivated |
| P5-6A / P5-6B | ⏸️ PRE_REAL_PATIENT_GATE / DEFERRED | mandatory before first identifiable real-patient health data; not current engineering critical path |
| Real-patient release | 🟠 NOT_AUTHORIZED | blocked until pre-real-patient gate is completed and explicitly authorized |

### Progress arithmetic

1. **Canonical global progress: 6/12 = 50.0%.** Equal-weight atomic forward lots; P5-4A is re-closed after merged local-first remediation and exact-head proof.
2. **P5 Pilot Readiness: 4/9 = 44.4%.** Historical whole-lot P5 accounting; P5-4 and P5-6 remain open as macro lots.
3. **Retained MENA: 32/38 = 84.2%.** Informational only; never a release gate.

No partial credit is assigned inside an atomic lot. Deferring a gate does not close it and does not increase progress.

---

# 2. One critical path

**Current non-patient engineering path:** continue verified product/security/reliability/UX work on synthetic or non-patient data, prioritizing reproduced defects and the unresolved items that remain in `docs/TECHDEBT.md`.

**Mandatory pre-real-patient path, activated before the first identifiable real-patient health data:** explicit exact-SHA re-freeze → P5-6A restricted safety evidence + P5-6B processor/CNDP evidence bound to the **actual local-first patient runtime and genuinely enabled external processors** → actual patient-runtime topology proof → three exact-SHA approved audits → explicit human release decision → controlled PWA pilot → P5-7 observed evidence → P5-8 go/no-go.

The Vercel/Django/Neon development/certification stack is not a mandatory patient-production dependency and must not be inserted into the patient processor/residency inventory solely because it exists for engineering. The pre-real-patient path is deferred, not waived. No release, deployment authorization or regulatory approval is implied by current engineering progress.

---

# 3. P5 Pilot Readiness

## P5-0 — Security reconciliation

**Status:** ✅ CLOSED.

## P5-1 — Morocco linguistic certification

**Status:** ✅ CLOSED / HUMAN_APPROVED / retained exact-main evidence.

Retained proof includes PR #579, exact-main evidence SHA `2d18428a0c59a18c82a1c0dfb410469f17f81e04`, green post-merge CI/migration, packet #34683056185, artifact #10295285314 and human approval in #515.

## P5-2 — Arabic OCR real-world evidence

**Status:** ✅ CLOSED with negative qualification result.

Real-camera Tesseract `ara` failed the required quality floor. No local Arabic full-document primary is qualified.

## P5-3 — Native TTS real-device evidence

**Status:** 🟡 DEFERRED / HUMAN_DEVICE_GATE.

Tracker: #518. Required only before a native pilot/distribution claim; it does not block the current PWA-first pilot.

## P5-4 — Pilot packaging

**Status:** 🟡 SPLIT / P5-4A CLOSED / P5-4B DEFERRED.

### P5-4A — PWA packaging engineering

**Status:** ✅ CLOSED / AUTH_LOCAL_FIRST_VERIFIED / STRONG_LOCAL_APP_LOCK_MERGED.

The reproduced offline-auth regression is resolved. PR #639 (`fix(auth): restore local-first offline reopen boundary`) merged as `bd13e8ad0c6f3ff2c4376b00c43fb8c54068d053`; its final candidate head was `05d02a0def7b909b83615c506ccf97f9623f1c6b`.

Retained local-first contract:

- first patient-device enrollment creates only a device-local enrollment marker plus opaque installation identifier and performs **zero required network requests**;
- subsequent local boot/reopen performs **zero required auth-network requests**;
- the default patient enrollment UI requests no email/password and makes no online-account claim;
- remote account registration is disabled by default and `registerWithEmail()` fails closed unless `IAMINA_REMOTE_ACCOUNT_ENROLLMENT=true` is explicitly enabled for the remote DEV/certification flow;
- local enrollment/session and the Django-signed remote API bearer are separate states;
- remote bearer rejection/expiry clears remote credential use only and cannot erase local enrollment or local clinical state;
- explicit sign-out clears the remote bearer, local marker and opaque local device identifier even if remote logout is unavailable;
- malformed secure-storage text never bootstraps local enrollment.

The separate strong local-auth debt was then resolved by PR #649 (`feat(auth): add strong local WebAuthn app-lock`), merged as `main@df457cfdcc574439adb791fbfc44d484a1224417`. The final exact candidate `fd5bc4392ceda6b411b72f3ceb9254119024ac5c` passed all 15 pull-request workflows, including CI #4454, TD-014 local app-lock certification #14 and TD-008 device integration baseline #14.

Fresh TD-014 artifact `10517999169`, digest `sha256:a0d17487f8cdca0bed18979e650eab6efc6679c76d834938dbae58de3e4f0255`, was inspected and retained:

- WebAuthn platform authenticator with required user verification;
- local/offline unlock with application network unavailable;
- user-verification failure fails closed;
- a genuinely mutated public key fails closed;
- no application network is required for unlock;
- BEFORE / setup / locked captures at `390×844`, `768×1024`, `1280×900`;
- zero horizontal overflow in the retained visual report;
- final P5-4A `AuthService` remained byte-identical through the app-lock lot.

Controlled pilot URL, physical target-browser installation, any patient distribution hosting, production release and real-patient authorization remain external.

### P5-4B — Native Android/iOS alignment

**Status:** 🟡 DEFERRED.

Future native-only work includes permanent signing/provisioning and physical-device install/update/recovery evidence.

## P5-5 — End-to-end pilot rehearsal

**Status:** ✅ CLOSED / `PASS_WITH_BOUNDARIES`.

Retained synthetic/non-patient proof includes main `88b78e036ce3494dfe37921e70e064fbfdabd6bb`, rehearsal #34573137446, CI #34573137452 and artifact #10188573954.

## P5-6 — Real-patient release gate

**Status:** ⏸️ PRE_REAL_PATIENT_GATE / DEFERRED / NOT_RELEASE_AUTHORIZED.

This gate is mandatory before the first identifiable real-patient health data enters IAMINA. It is not the current day-to-day engineering priority while work remains synthetic/non-patient. Deferral does not constitute approval, closure or waiver.

### Last retained frozen candidate evidence

The last explicitly frozen release SHA was `fb42e4d641b7b057607fe6a2de3d5104ccf15d0b`, with:

- safety corpus: 59 exact cases;
- parity coverage: 10 technical tuples;
- safety fingerprint: `823d109b0ddd10d1874eec53027eafd9d65884f14810304af3681c57c82cf7e5`;
- consent notice version: `2026-09-12.1`.

That SHA is retained as historical exact-freeze evidence. It is **not** the current release candidate because later runtime/code changes have advanced `main`. A new exact release candidate must be explicitly re-frozen before the pre-real-patient gate is executed.

### Historical candidate re-freeze proof

The predecessor candidate `5b27a22fc5c05a06e7eeeb0e841bb0e7dadce7f6` proved the **remote Vercel/Django/Neon development/certification path**. It did not prove or define the patient production runtime. Two release-gate/runtime defects were then fixed:

- PR #602 made the local-only consent audit consume the restricted residency manifest and bind genuine CNDP health-processing evidence to the exact release SHA;
- PR #603 made native password recovery require an explicit provider-neutral SMTP contract when that remote recovery path is enabled, removed silent delivery assumptions and preserved account-enumeration resistance.

Validation retained for the historical `fb42e4d…` freeze:

- #602 exact-head CI #4186 / workflow `34771054574` SUCCESS;
- #602 exact-head migration drift #3733 / workflow `34771054541` SUCCESS;
- #603 exact-head CI #4189 / workflow `34771391814` SUCCESS;
- #603 exact-head migration drift #3736 / workflow `34771391809` SUCCESS;
- #603 merge `main@fb42e4d641b7b057607fe6a2de3d5104ccf15d0b`;
- post-merge CI #4190 / workflow `34773613905` SUCCESS;
- post-merge migration drift #3737 / workflow `34773613814` SUCCESS.

Clinical rebind proof retained for that historical freeze:

- `backend/core/safety_corpora.py` blob is identical between `5b27a22…` and `fb42e4d…`: `bf046c298ee8e77591f5c5b1049b806a6255bfcf`;
- `backend/core/triage_classification.py` blob is identical between those candidates: `eba7a57967eeec1ba4b264c90ccab1a30e516b38`;
- the retained corpus therefore remains 59 exact cases / 10 tuples with fingerprint `823d109b0ddd10d1874eec53027eafd9d65884f14810304af3681c57c82cf7e5`.

This is historical technical exact-corpus evidence only. It does not fabricate reviewer identity, qualification or a new human approval. Any later runtime/code change invalidates use of that historical freeze as the current release candidate and requires another explicit re-freeze before a real-patient release attempt.

### P5-6 consent evidence engineering

**Status:** ✅ CLOSED atomic sublot / MERGED / GREEN.

Retained from #591: exact notice version/hash/locale, legacy consent invalidation, server acceptance receipts, withdrawal revocation, current-consent AI-egress verification, consent-epoch isolation, Flutter/server fail-closed behavior and Secure Storage + Drift local gating.

### P5-6 remote development/certification deployment state

**Status:** ✅ PREDECESSOR_REMOTE_PATH_HEALTHY / NOT_PATIENT_PROD / NO_CURRENT_CANDIDATE.

Proven predecessor **remote development/certification** topology:

- Vercel project `iamina-certified` / `prj_Pn9FnyconF3h2w9gOU74iV98kJoU`;
- exact source `5b27a22fc5c05a06e7eeeb0e841bb0e7dadce7f6`;
- deployment `dpl_8ex2k82KaozE6Fxc8wQBYJuRU43y`;
- state `READY`, target `production` in Vercel's deployment terminology, runtime region `cdg1`, one Python serverless function;
- stable alias `iamina-certified.vercel.app` resolved to that deployment;
- dedicated Neon project `IAMINA` / `square-sun-82359137`, PostgreSQL 16, region `aws-eu-central-1`, default branch `production` / `br-fragrant-frost-b1lbdfzs`;
- migrations current and health HTTP 200 with `status=ok`, `db=ok`, `cache=unavailable`;
- cache unavailability is non-fatal under the existing health contract; no Redis readiness claim is made;
- no AqarFinder/Supabase database and no unrelated Neon database was reused.

The words `production` above describe Vercel/Neon environment labels only. They do **not** mean patient production. `docs/LOCAL_FIRST_RUNTIME_BOUNDARY.md` defines the runtime boundary.

The historical `fb42e4d…` freeze was **not deployed**. PR #603 deliberately made the remote Django production-settings path fail closed until an explicit SMTP/reset contract is configured. That is a remote dev/cert deployment condition, not a requirement for local clinical availability. No future Vercel deployment may occur without separate explicit owner authorization.

### P5-6A — Safety qualification manifest

**Tracker:** #318.

Current state: `OPEN / PRE_REAL_PATIENT_GATE / DEFERRED / REVIEW_ATTESTED / OWNER_QUALIFICATION_ATTESTATION_RETAINED / HISTORICAL_EXACT_CORPUS_EVIDENCE_RETAINED / CURRENT_CANDIDATE_PENDING_REFREEZE / RESTRICTED_QUALIFICATION_REFERENCES_PENDING`.

Already retained: owner-attested safety/clinical review, Darija adjudication/runtime cutover, safety-owner/parity attestation and English-locale validation. Owner qualification wording: **« professionnels qualifiés »**, reference `issue-318:owner-attestation:professionnels-qualifies`.

Still missing before real-patient release:

- explicit exact-SHA re-freeze of the future release candidate;
- real opaque native-reviewer references for `fr`, `ar`, `en`, `ar-MA`;
- real qualification references required by the manifest contract;
- non-stale `reviewed_on` / `review_due_on`;
- approved coverage of all 59 exact case IDs;
- approved coverage of all 10 exact parity tuples;
- restricted safety manifest bound to the newly refrozen exact candidate and exact safety fingerprint;
- exact-SHA safety audit PASS.

### P5-6B — CNDP / consent / processor / residency

**Tracker:** #320.

Current state: `OPEN / PRE_REAL_PATIENT_GATE / DEFERRED / REMOTE_DEV_CERT_PATH_PROVEN / PATIENT_RUNTIME_TOPOLOGY_PENDING / COMPLIANCE_EVIDENCE_PENDING`.

Still required before real-patient release:

- explicit exact-SHA re-freeze of the future release candidate;
- freeze the **actual local-first patient runtime topology** and enumerate only the external processors genuinely enabled for that pilot;
- account-specific processor/DPA/subprocessor/retention/deletion/privacy/security evidence for every genuinely enabled external processor;
- if remote password recovery is enabled for the pilot, choose/configure its mail processor and include it in that evidence inventory; if it is not enabled, do not fabricate it as a runtime dependency;
- deployment/distribution-specific patient notice/consent approval evidence for the actual pilot architecture;
- applicable CNDP health-data processing evidence;
- foreign-transfer basis/evidence for every actual external destination where applicable;
- restricted residency manifest bound to the newly refrozen exact candidate and actual patient topology;
- exact-SHA consent and residency audit PASS outputs.

Public provider/CNDP documentation can define requirements but cannot substitute for account-specific approvals. Development-only Vercel/Neon infrastructure is excluded from the patient processor/residency inventory unless the actual pilot architecture later enables it for patient data.

The current pilot scope enables no external AI processor. `--local-only` remains mandatory for the consent audit when the gate is activated; it does not waive the global CNDP health-processing authorization gate.

### P5-6 success proof

When preparation for the first real-patient pilot starts, first explicitly re-freeze the exact release SHA and bind all restricted manifests to that same SHA and the actual patient runtime topology. Then all three fail-closed audits must PASS against it:

```bash
python manage.py audit_pilot_consent_governance \
  --local-only \
  --residency-manifest /restricted/iamina/pilot-residency.json \
  --require-approved \
  --expected-source-commit-sha <EXACT_REFROZEN_SHA>

python manage.py audit_pilot_data_residency \
  --manifest /restricted/iamina/pilot-residency.json \
  --require-approved \
  --expected-source-commit-sha <EXACT_REFROZEN_SHA>

python manage.py audit_safety_corpus_review \
  --manifest /restricted/iamina/safety-review-manifest.json \
  --require-approved \
  --expected-source-commit-sha <EXACT_REFROZEN_SHA>
```

Then and only then: explicit human real-patient release decision.

## P5-7 — Observed pilot evidence

**Status:** ⚪ PENDING P5-6.

Collect real pilot MAU/activation/retention, safety incidents, reliability/offline/update failures, LLM route/cost and zero-model rate, storage/egress cost, satisfaction/support burden and clinically safe usefulness signals. Synthetic evidence cannot become P5-7 proof.

## P5-8 — Go / No-Go

**Status:** ⚪ PENDING P5-7.

No second disease capsule before this evidence-based decision gate.

**P5 whole-lot tracker:** 4/9 = 44.4%.  
**Canonical global atomic tracker:** 6/12 = 50.0% with P5-4A closed.

---

# 4. MENA / multimodal residuals

## P0-MENA-2 — Locale + safety contract

**Status:** 🟡 IMPLEMENTATION CLOSED / PRE_REAL_PATIENT_EVIDENCE DEFERRED.

Runtime locale/high-severity variant coverage is implemented and bound into the exact safety corpus. Remaining release-relevant work is external/restricted review evidence under #318/P5-6A, activated before real-patient use rather than treated as current implementation debt.

## P0-MENA-4 — Multimodal provider benchmark

**Status:** 🟡 DEFERRED / EXTERNAL-HUMAN EVIDENCE, issue #319.

Groq + `openai/gpt-oss-120b` remains the conversational candidate; no local Arabic full-document OCR primary qualifies under the current strict floor; native TTS evidence is deferred to P5-3; STT remains deferred by owner decision.

Retained MENA metric: 32/38 = 84.2%, informational only.

---

# 5. Parallel engineering debt

`docs/TECHDEBT.md` owns unresolved compromises; it is not a competing roadmap. Critical/high debt is promoted into the current engineering path only when the corresponding feature is active or a current defect is reproduced. Pre-real-patient compliance evidence remains a separate future release gate.

Reconciliation retained through 2026-09-17:

- TD-010 observability retention lifecycle is CLOSED by PR #610, merge `e9c04beee31638ff86d7fd0b50d5eddccc313c4e`, post-merge CI #4206 / workflow `34787203311` SUCCESS and migration drift #3742 SUCCESS;
- former TD-005 and TD-006 were removed from the unresolved-debt register because current runtime safety variant coverage is implemented and the only remaining release gate is the restricted human qualification/approval evidence already owned by #318/P5-6A;
- former TD-007 was removed after verifying the explicitly approved/documented `SELF_CARE_ONLY` pilot operating model: PR #24 formalized no human monitoring, mandatory disclosure and fail-closed evidence requirements for any future `MONITORED_HUMAN` mode; P0.6 PR #128 later centralized all patient-facing urgent responses through that policy;
- TD-008 device-level critical-flow coverage is CLOSED by PR #636 / merge `532376020d4696d4098994a97a764a1994c7f92f`; the dedicated integration baseline landed, the resolved debt was removed in `8d54168674c316ddcc64846384b0bcac72650fe4`, and handover `4e7b04a3387da68374e00ab858e63b914faa1884` retained the closeout;
- historical TD-013 authentication abuse protection is CLOSED by PR #623, merged as `main@f045491a3e07db388067fe54c60fd0c4b543e050`; exact-head CI #4238 and drift #3760 succeeded, then exact-main post-merge CI #4241 and drift #3761 succeeded. Tracker #622 is closed. The retained limiter is PostgreSQL-backed, covers login/registration/password-reset, is independent of Redis availability, stores HMAC-derived identifiers rather than raw IP/email, and has typed 429/recovery tests;
- TD-003 provider timeout/circuit-breaker/failure UX is CLOSED by backend breaker PR #628, frontend typed-error UX PR #629 and docs closeout PR #630. Exact-head #629 CI #4280, Companion E2E #98, UI browser #710, UI geometry #707 and missing-routes #66 succeeded; #630 exact-head CI #4291 and post-merge CI #4292 succeeded;
- TD-014 patient local app-lock/re-authentication is CLOSED by PR #649 / merge `df457cfdcc574439adb791fbfc44d484a1224417`; final candidate `fd5bc4392ceda6b411b72f3ceb9254119024ac5c` passed 15/15 workflows and its fresh WebAuthn/offline/visual artifact was inspected. TD-014 is removed from the unresolved debt register.
- TD-012 remains OPEN. AISummary phase 2 is merged by PR #689; DocumentImport remains CLOSED by PR #692; Companion remains CLOSED by PR #695. Reports is CLOSED by PR #698 / `6920c20b67af466ac69a1be292a9afcd3b17ca91`, reducing `reports_screen.dart` from ~29.0k to ~3.8k characters while retaining DB/stream/period orchestration in the state file. Exact-head CI #4599, browser #970, geometry #855, Offline UI #97 and P5-5 #354 succeeded. Visual comparison: 390×844 pixel-identical; 768×1024 and 1280×900 differed only in the time-dependent timestamp text (158 pixels each), with no geometry change; visual score 9.9/10. IAmina chat remains CLOSED by PR #671; Profile remains CLOSED by PR #675.

---

# 6. CI / cost optimization

CI-FRUGAL-2 / #442 remains parallel and non-blocking. Runner-cost work must not weaken retained visual certification or safety/security gates.

---

# 7. Repository hygiene

Open GitHub items are not automatically active roadmap work. Historical Companion/OCR evidence issues and stale PRs remain evidence/hygiene until current-main reproduction proves forward work. Stale issue/PR state never changes product status without code + tests + retained evidence.

---

# 8. Closed workstreams retained as history

Closed unless a new reproduced regression opens a scoped lot: Gate A Secure Core; P0 foundations; product truthfulness; agent governance; global UX/Dashboard/Journal convergence; outbound AI/data-egress foundation; current sovereign-auth migration work recorded as merged; Companion intelligence/proactivity convergence; CGM gateway V1/V1.1/V2/V2.1; P4-FRUGAL PRE-PILOT; P5-0; P5-1; P5-2; P5-4A; P5-5; the P5-6 consent-evidence engineering atomic sublot; and TD-014 strong local app-lock.

Closed does not imply legal/CNDP authorization, physical-device proof, real-patient authorization or production approval unless that exact evidence is retained.

---

# 9. Execution order

1. **Current engineering:** continue auditing remaining `docs/TECHDEBT.md` items for staleness and prioritize reproduced security/reliability/accessibility defects solvable with synthetic/non-patient data.
2. Continue product/UX/reliability/security engineering while preserving fail-closed real-patient boundaries, the local-first runtime contract and the merged strong local app-lock boundary.
3. **Before the first identifiable real-patient health data:** explicitly re-freeze the chosen exact release SHA, reactivate P5-6A #318 and P5-6B #320, freeze the actual patient runtime topology, enumerate only genuinely enabled processors, and collect genuine restricted evidence/approvals.
4. If the pilot requires any remote deployment/distribution change, obtain separate explicit owner authorization before that deployment. Development Vercel deployment remains separately authorization-gated and is not patient production proof.
5. Freeze the actual pilot topology/residency evidence after every authorized deployment/distribution step relevant to patient processing.
6. Run the three exact-SHA fail-closed audits.
7. Explicit human real-patient release decision.
8. Controlled PWA pilot.
9. P5-7 observed evidence.
10. P5-8 go/no-go.

No Vercel deployment is authorized by this execution order.

---

# 10. Canonical governance

- `docs/ROADMAP.md` owns all forward status, priority, sequencing and completion percentages.
- `docs/LOCAL_FIRST_RUNTIME_BOUNDARY.md` owns the patient-runtime vs remote-dev/cert architecture boundary and is subordinate only to an explicit later change in this roadmap.
- Overall progress is the atomic 12-lot metric. Its denominator changes only through an explicit roadmap governance change.
- `docs/TECHDEBT.md` owns unresolved compromises only.
- `AGENTS.md` owns execution rules only and is subordinate to this roadmap for status.
- Issues/PRs are execution/evidence containers, not canonical portfolio status.
- Assessments/handovers/ADRs are evidence/history, not forward authority.
- Never declare a lot closed from a title, branch, PR state or old score alone.
- No Vercel deployment without explicit owner authorization; technical deployment authorization never implies real-patient release.
- Deferring P5-6A/P5-6B does not waive them. The boundary is before the first identifiable real-patient health data enters IAMINA.

## Current canonical snapshot

- repo: `hraaaaf/IAMINA-MVP`
- main reconciled for this lot: `6920c20b67af466ac69a1be292a9afcd3b17ca91`
- P5-4A AUTH-LOCAL-FIRST: **CLOSED**, PR #639 merged as `bd13e8ad0c6f3ff2c4376b00c43fb8c54068d053`
- TD-014 strong local app-lock: **CLOSED**, PR #649 merged as `df457cfdcc574439adb791fbfc44d484a1224417`; final candidate `fd5bc4392ceda6b411b72f3ceb9254119024ac5c` had 15/15 SUCCESS
- last explicitly frozen P5-6 SHA: `fb42e4d641b7b057607fe6a2de3d5104ccf15d0b` — **historical freeze evidence, not current release candidate**
- current release candidate: **NONE / PENDING EXPLICIT REFREEZE**
- historical freeze proof: PRs #602/#603; #603 post-merge CI #4190 / workflow `34773613905`; post-merge drift #3737 / workflow `34773613814`
- patient production runtime boundary: **LOCAL-FIRST; Vercel/Django/Neon excluded unless a future explicit architecture change says otherwise**
- proven predecessor remote dev/cert deployment: `dpl_8ex2k82KaozE6Fxc8wQBYJuRU43y`, source `5b27a22fc5c05a06e7eeeb0e841bb0e7dadce7f6`, Python function, `cdg1`, health HTTP 200 / `db=ok`
- dedicated remote dev/cert database proof: Neon `IAMINA` / `square-sun-82359137`, PG16, `aws-eu-central-1`, branch `production`, migrations current for the predecessor remote deployment
- safety fingerprint retained from historical freeze: `823d109b0ddd10d1874eec53027eafd9d65884f14810304af3681c57c82cf7e5`
- qualification wording: **professionnels qualifiés** — owner attestation reference `issue-318:owner-attestation:professionnels-qualifies`
- consent notice: `2026-09-12.1`
- canonical global progress: **6/12 = 50.0% with P5-4A closed**
