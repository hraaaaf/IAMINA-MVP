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


## 6. D18 — analyse ciblée de l'origine d'IndexedDB `amina` (04/11/2026)

**Décision d'ingénierie : NE PAS SUPPRIMER la sonde legacy et NE PAS ouvrir le shell public via une DB d'audit.** La correction la plus simple (supprimer `AppDatabase.defaults()`) serait imprudente : le mécanisme est utilisé comme garde d'anti-rollback du verrou local. Toute refonte nécessite un protocole non destructif et des tests sur coffres synthétiques de versions anciennes.

### Constat code + comportement

1. `frontend/lib/main.dart` L61–69 : **à chaque démarrage**, crée `AppDatabase.defaults()`, appelle `_hasProtectedLocalState(...)` puis ferme le handle. La sonde est exécutée avant `runApp` ; la fermeture du handle n'efface pas un IndexedDB créé.
2. `frontend/lib/data/drift/database.dart` L119–129 : `AppDatabase.defaults()` ouvre le stockage Drift Web **nommé exactement `amina`**, sans scope patient. Il s'agit du nom historique, distinct de `amina_vault_v1_audit` et des coffres nommés par propriétaire.
3. `main.dart` L25–39, `medical_vault_protected_state.dart` L4–25 : si la fonction de politique ne conclut pas à une session locale déjà protégée, la sonde **effectue des SELECT** sur `patientProfiles`, `logEntries`, `chatMessages`, `medicationEvents`, `reminders` et les déclarations. **Une requête Drift déclenche potentiellement l'ouverture et la gestion du schéma** `database.dart` L157–212 (`onCreate` / `onUpgrade`). Une sonde dite « présence seulement » n'est donc **pas garantie strictement read-only** sur un vieux schéma ; ce risque est à démontrer ou réfuter avant activation publique.
4. [Chrome L01 #41860217964](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41860217964), `proof.json` : sur profil navigateur neuf, IndexedDB énumère `["amina"]` après boot, et **0 requête `/api/`** observée au boot/reload. **Attribution :** la concordance du nom et du chemin d'exécution rend cette sonde la **cause la plus probable**, mais l'artefact n'enregistre pas l'événement `indexedDB.open` dans le worker : ne pas annoncer une causalité instrumentée ni une écriture clinique.
5. `frontend/lib/services/patient_vault_app_host.dart` L69–85 et L270–285 : un **autre** chemin crée `AppDatabase.forPatientVault(PatientVaultScope.auditOnly())` et injecte ce handle au non-authentifié. Ce handle a un nom **différent** et n'explique pas directement la présence de `amina` ; il reste incompatible avec la cible D37-A d'un vrai shell invité **sans provider clinique**.

**Conclusion vérifiée :** `amina` apparaît au bootstrap d'un navigateur vierge, et le code ouvre par conception le stockage historique au démarrage ; **aucune fuite ni donnée patient ni mutation de schéma n'est démontrée dans ce run**. **Risque à traiter :** double frontière (legacy anti-rollback et DB d'audit invitée) et éventuelle migration involontaire lors d'un SELECT. La CI #41860217686 reste verte pour le correctif de locale, mais ne résout pas ces risques.

### Prochain protocole de preuve — tout synthétique, aucun patient

| ID | Scénario | Preuve exigée | Statut |
|---|---|---|---|
| LEG-01 | Chrome vierge : inspecter IndexedDB **avant** tout bootstrap puis après la sonde | Nom, moment d'apparition et attribution au chemin d'ouverture ; **aucune API métier** | NOT RUN |
| LEG-02 | Ancienne base `amina` synthétique avec tables/valeurs/hachages de contrôle | Inspection ne change **aucun** octet/ligne/schema_version ni journal de migrations, ou test FAIL | NOT RUN |
| LEG-03 | Ancien coffre protégé / clé de lock absente | Doit rester **locked/recovery_required**, jamais interprété comme un premier usage | NOT RUN |
| LEG-04 | Ancien coffre ambigu/corrompu ou IndexedDB bloqué | **Fail closed** sans effacer, réinitialiser ni s'approprier un coffre | NOT RUN |
| LEG-05 | Chrome/Safari/WebKit privé, mode offline, ancienne PWA et onglet A→B→A | Détection compatible ou échec fermé, aucune identité déduite de la DB `amina` | NOT RUN |
| LEG-06 | Vrai visiteur après détection protégée | Shell statique séparé, **aucun** `Provider<AppDatabase>`, requête, sauvegarde médicale ou adoption legacy | NOT RUN |
| LEG-07 | Audit QA explicite | DB synthétique `amina_vault_v1_audit` isolée ; jamais offerte à un visiteur ordinaire | NOT RUN |

### Architecture cible proposée, non implémentée

**Frontière 1 — détection d'un historique :** présence/métadonnées **sans ouverture-migration**, si la plateforme le permet ; toute absence de preuve ou incohérence doit maintenir le verrou / récupération. Évaluer précisément Safari/IndexedDB/OPFS avant de choisir la technique. Le read-only doit être vérifié avec des empreintes synthétiques avant/après ; ne jamais inférer l'identité à partir de `amina`.

**Frontière 2 — UI visiteur :** coque Web/PWA statique sans `AppDatabase`, `ModulesProvider` patient, `SyncService` ou appel API métier, mais conservant l'écran/verrou de sécurité nécessaire aux installations existantes ; première action clinique ⇒ connexion puis autorisation explicite. Ne pas faire passer une session locale anonyme pour un compte distant vérifié.

**Gates :** le développement de ces frontières reste **NO-GO clinique D18/W01** tant que tests anciens coffres/sessions et revue sécurité indépendants sont manquants. Aucune migration, merge, Vercel Preview/Production ou accès patient autorisé. **Next exact :** instrumenter les ouvertures IndexedDB en CI synthétique et mesurer la non-mutation d'un vieux schéma avant toute modification runtime de la sonde.
