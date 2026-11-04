# IAMINA — L01 / D37-A + D18 — preflight Web visiteur/identité/coffres

**Date :** 2026-11-04 · **Type :** audit statique / contrat de tests, sans patients.  
**Base de preuve :** `main@d7d650a082300486764019c8238f591057210d54` (code actuel, pas la PR documentaire #1270).  
**Roadmap adoptée :** `docs/ROADMAP.md` sur PR Draft #1270, non fusionnée ; L01 après onboarding L00.  
**Statut :** **IN PROGRESS / NO-GO CLINIQUE** ; aucune implémentation D37, aucune certification, aucun test navigateur exécuté dans ce preflight.

## 1. Goal, succès et limites

**Goal :** distinguer strictement (i) vrai visiteur volatile et shell 100 % statique/fictif, (ii) compte patient distant vérifié, (iii) utilisateur legacy device-local à conserver sans réattribution, et (iv) session QA audit synthétique explicitement isolée.

**Succès observable requis, non encore obtenu :** un visiteur peut parcourir les écrans sans login, **sans** ouverture/écriture d'une base clinique, auto-fetch métier ni service tiers ; la première opération métier exige connexion **avant** toute persistance ou requête ; anciens coffres et protections app-lock restent intacts ; A→déconnexion→B→A ne révèle jamais de données A à B ; contrôles API indépendants du simple routeur.

**Hors périmètre de ce preflight :** migrations D18, correction du chiffrement legacy, nouvelles clés, backend/Neon prod, implémentation de shell, activation IA/CGM, patient réel, Preview/Production Vercel, fusion. Aucun « test vert » documentaire ne valide le runtime.

## 2. Inventaire des chemins observés dans le code

| Point | Preuve code à la base SHA | État / risque à traiter |
|---|---|---|
| Route d'entrée | [`app_router.dart` L118–L152](https://github.com/hraaaaf/IAMINA-MVP/blob/d7d650a082300486764019c8238f591057210d54/frontend/lib/routes/app_router.dart#L118-L152) | `!isLoggedIn && !isLoginPage → '/login'`. **D37-A non implémentée**. Ne pas désactiver les gates app-lock/consentement en ouvrant le shell. |
| Construction DB audit | [`patient_vault_app_host.dart` L69–L85](https://github.com/hraaaaf/IAMINA-MVP/blob/d7d650a082300486764019c8238f591057210d54/frontend/lib/services/patient_vault_app_host.dart#L69-L85) | `AppDatabase.forPatientVault(PatientVaultScope.auditOnly())` créée au montage. Ce n'est pas une preuve d'écriture, mais le **vrai visiteur** devra n'avoir aucun handle clinique. |
| Provider non connecté | [`patient_vault_app_host.dart` L262–L286](https://github.com/hraaaaf/IAMINA-MVP/blob/d7d650a082300486764019c8238f591057210d54/frontend/lib/services/patient_vault_app_host.dart#L262-L286) | `Provider<AppDatabase>` injecté sur la branche non authentifiée. Séparer le shell public de la session audit synthétique ; ne pas injecter une DB de démonstration dans le vrai visiteur. |
| Inspection coffre historique | [`main.dart` L49–L91](https://github.com/hraaaaf/IAMINA-MVP/blob/d7d650a082300486764019c8238f591057210d54/frontend/lib/main.dart#L49-L91) | `AppDatabase.defaults()` inspectée pour détecter un état protégé / app-lock. **Ne pas supprimer ce fail-closed** sans analyse D18 : risque anciens clients IDB/VFS. |
| Auth vs compte vérifié | [`auth_service.dart` L142–L182](https://github.com/hraaaaf/IAMINA-MVP/blob/d7d650a082300486764019c8238f591057210d54/frontend/lib/services/auth_service.dart#L142-L182) | `isAuthenticated` couvre audit, enrollment local et Firebase. Une simple vérité booléenne ne prouve pas identité Django/native autorisée. Vérifier `hasRemoteApiCredential` ET attestation d'identité / scope. |
| Auto-fetch langue | [`main.dart` L109–L130](https://github.com/hraaaaf/IAMINA-MVP/blob/d7d650a082300486764019c8238f591057210d54/frontend/lib/main.dart#L109-L130) et [`locale_preference_service.dart` L144–L173](https://github.com/hraaaaf/IAMINA-MVP/blob/d7d650a082300486764019c8238f591057210d54/frontend/lib/services/locale_preference_service.dart#L144-L173) | `LocalePreferenceService(... )..refresh()` peut tenter `GET /api/v1/profile/locale` au bootstrap si hors audit/démo. **Tentative dans le code**, réseau réel non observé ; intercepteurs peuvent bloquer. La langue UI statique doit marcher sans profil serveur. |
| Modules à l'ouverture patient | [`patient_vault_app_host.dart` L238–L259](https://github.com/hraaaaf/IAMINA-MVP/blob/d7d650a082300486764019c8238f591057210d54/frontend/lib/services/patient_vault_app_host.dart#L238-L259) | `ModulesProvider(widget.api)..refresh()` dans le binding **patient** ; prouver qu'aucun chemin visiteur ne déclenche cet auto-fetch. |
| Coffre de compte / epoch | [`patient_vault_session_controller.dart` L52–L105](https://github.com/hraaaaf/IAMINA-MVP/blob/d7d650a082300486764019c8238f591057210d54/frontend/lib/services/patient_vault_session_controller.dart#L52-L105) | Protection partielle existante : retirer scope/DB à changement d'auth, fermer l'ancien et rejeter ouverture obsolète. Conserver et tester. |
| Intercepteurs API | [`api_client.dart` L95–L151](https://github.com/hraaaaf/IAMINA-MVP/blob/d7d650a082300486764019c8238f591057210d54/frontend/lib/services/api_client.dart#L95-L151) | App-lock, scope/consentement et epoch doivent rester fail-closed ; l'absence de fetch visible en UI ne suffit pas. |
| DB nommées | [`database.dart` L118–L145](https://github.com/hraaaaf/IAMINA-MVP/blob/d7d650a082300486764019c8238f591057210d54/frontend/lib/data/drift/database.dart#L118-L145) | `defaults()` legacy et `forPatientVault(scope)` patient sont deux chemins distincts. Ne pas utiliser le nom de l'ancien coffre comme identité du futur compte. |

**Important :** cet inventaire vise les **points d'entrée prioritaires vérifiés** ; il ne prétend **pas** avoir énuméré tous les appels réseau du dépôt ou toutes les anciennes versions PWA. Prochaine passe nécessaire sur l'ensemble des modules, hooks et endpoints avec recherche exhaustive.

## 3. Matrice de tests négatifs FUE D37 / D18 — à exécuter

Utiliser **uniquement identités, mesures, photos et coffres synthétiques**, sans données patient. État de toutes les cases ci-dessous : **NOT RUN**. Collecter console/browser-network/IndexedDB/OPFS/storage + vidéos/screenshots des parcours et logs API sur SHA exact.

| ID | Scénario réel Web/PWA | Attendu | État |
|---|---|---|---|
| V01 | Premier chargement, jamais connecté | Shell navigable, 0 coffre clinique, 0 fetch métier | NOT RUN |
| V02 | Naviguer Accueil → Journal → Paramètres sans compte | Écrans vides ou exemple fictif explicite ; aucun profil réel | NOT RUN |
| V03 | Refresh/route directe du shell invité | Même navigation et zéro accès médical | NOT RUN |
| V04 | Clic Ajouter mesure sans compte | Connexion avant lecture/écriture, retour à la tâche après login sans donnée invitée | NOT RUN |
| V05 | Historique, photo, documents, appareils, appels IA sans compte | Aucune requête ou persistance métier avant login | NOT RUN |
| V06 | Langue FR / AR RTL sans compte | Assets/traductions statiques ; aucun `GET /profile/locale` transmis | NOT RUN |
| V07 | Compte patient distant vérifié | Scope patient stable + app-lock ; seules ses données | NOT RUN |
| V08 | Ancien marqueur local/Firebase anonyme | Ne pas être promu silencieusement compte distant, anciens coffres isolés | NOT RUN |
| V09 | A connecté → logout → B → logout → A | Aucun état, brouillon, cache ou donnée croisés | NOT RUN |
| V10 | Deux onglets A/B, anciens onglets non rafraîchis | Epoch invalide l'accès de l'ancien compte, côté API et UI | NOT RUN |
| V11 | Déconnexion offline / reconnexion différée | Aucune réattribution legacy ; échecs fermés pour opérations non autorisées | NOT RUN |
| V12 | Vieille version PWA/worker, VFS legacy v1 | Coffre original préservé ; tout opener/migration dangereux bloqué | NOT RUN |
| V13 | Tests requêtes directes API sans UI | Anonymous/expired bearer/cross-account → 401/403 sans données patient | NOT RUN |
| V14 | Consentement IA OFF / absent | 0 flux externe IA ; saisie manuelle accessible | NOT RUN |
| V15 | Démo audit locale autorisée vs vrai visiteur public | Audit seul peut créer des données **synthétiques** séparées ; zéro accès clinical invité | NOT RUN |
| V16 | Safari iPhone / Chromium ; 390, 430, 768, 1280, zoom 200 %, clavier, AR RTL | Parité des restrictions, navigation et accessibilité | NOT RUN |

### Conditions d'arrêt

- Toute fuite inter-comptes, migration automatique, perte de coffre ou ouverture persistante au vrai invité ⇒ **STOP / NO-GO**.
- Si vieux onglet/worker continue à accéder à la VFS historique malgré les nouvelles protections ⇒ **D18 P0-A reste NO-GO clinique**, sans exception.
- Un consentement manquant, une réponse API de patient au visiteur, un fetch métier transmis au chargement ⇒ échec D37.
- Des tests qui ne tournent pas sur Safari/WebKit ne peuvent pas certifier l'expérience iPhone. Une CI documentaire ne certifie pas les flux cliniques.

## 4. Ordre exact d'exécution proposé après ce preflight

1. Faire une recherche de code **exhaustive** des créations de `AppDatabase`/Drift/IndexedDB/OPFS, accès `ApiClient`/HTTP/service tiers, initialisations `refresh()`, scopes d'auth, importations de profil/legacy et provider construction. Indexer chaque point et justifier sa classe public / patient / legacy / audit.
2. Construire un **visitor shell sans provider de base clinique** sur branche L01 isolée **seulement** après examen des exigences app-lock/legacy, avec navigation statique et CTA connexion avant toute fonction protégée. Garder les anciens coffres intacts.
3. Ajouter tests Flutter + navigateur ciblant V01–V16, fixtures synthétiques et captures BEFORE/AFTER aux mêmes viewports (pas de « FUE PASS » avant exécution).
4. Faire vérifications API directes et tests adversariaux A→B→A / stale-opener, résolution locale offline, sauvegarde/reprise.
5. Réévaluer D18 et W01 via revue de sécurité et preuves dédiées, **sans lever les NO-GO par CI verte uniquement**.
6. Prendre les décisions de fusion et de déploiement **séparément et explicitement** ; aucun merge ni Vercel autorisé dans ce preflight.

**Chemin canonique :** L00 plan adopté → **L01 audit/implémentation sous gates** → L02, puis L03–L09.  
**Closeout courant :** baseline documentaire + preuve Chrome bornée ajoutée ci-dessous ; **FUE V01–V16 non certifiée** ; aucune modification de code patient.

## 5. Résultats navigateur ciblés — preuve supplémentaire sur PR #1272

**Source vérifiée :** [PR Draft #1272](https://github.com/hraaaaf/IAMINA-MVP/pull/1272), HEAD `e2391fc0ca4acab9c8d64cdcf8942d6fbba1de06`, [run Chrome #41860217964 SUCCESS](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41860217964), [artefact JSON et PNGs](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41860217964/artifacts/13339751419). La preuve a été extraite et `proof.json` lu.

| Preuve | Observation | Portée |
|---|---|---|
| Chrome réel, profil neuf, Flutter Web local | `real_web_boot = PASS` ; rechargement fonctionnel | Bootstrap réel uniquement, pas d'usage patient |
| Trafic réseau CDP au démarrage et après reload | `api_requests_observed = []`, `profile_locale_request_count = 0` | **Succès borné** pour l'egress au bootstrap invité ; aucun parcours de navigation connecté |
| IndexedDB dans ce Chrome vierge | `synthetic_fresh_browser_idb_names = ["amina"]` | **Anomalie de frontière à investiguer** : existence d'une base legacy ; contenu ou données médicales non démontrés |
| BEFORE UI | PNGs 390×844, 430×932, 768×1024, 1280×900 ; « Set up IAmina here / Continue without an account » | Parcours d'enrôlement local **différent** du shell invité intégral D37-A ; aucun AFTER ni score visuel |
| CI Web sur ce SHA | [#41860217686 SUCCESS](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41860217686) ; frontend analyse/tests/build vert | **977 tests PASS, 7 SKIPPED** ; ne certifie ni D18 ni D37 |

**Verdict par scénario :** V06 **PARTIEL** (absence d'egress profil dans le parcours Chrome, pas de validation FR/AR complète) ; V01 **NON CONCLUANT** (une DB `amina` existe au démarrage, aucune preuve de contenu patient) ; V02–V05/V07–V16 **NOT RUN**. Les 16 cas FUE ne sont donc **pas PASS**. Les contrôles API directs, vieux service workers/PWA, Safari/WebKit et A→B→A restent ouverts.

**Observation architecture bloquante :** `main.dart` appelle `AppDatabase.defaults()` pour inspecter le coffre legacy dans le but de **fail-closed app-lock**. Le nom IndexedDB observé est compatible avec ce chemin ; ceci reste une **hypothèse de cause**, pas une trace instrumentée de l'opération d'ouverture. Ne jamais retirer cette inspection avant une alternative sûre et testée sur vieux coffres. Le nouveau shell visiteur doit être dépourvu de provider patient et ne doit jamais lier les données legacy à un nouveau compte automatiquement.

**Next L01 :** instrumenter l'origine exacte de `amina` sans mutation d'un coffre réel ; isoler cette sonde des écrans publics, définir mockup et cas FUE avant modification UI ; maintenir **D18 SAFE-HOLD / W01 NO-GO** et autorisations séparées merge/Vercel.
