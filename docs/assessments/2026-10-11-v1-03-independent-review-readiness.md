# IAMINA V1-03 — Pack de revue indépendante et gates pré-intégration

**Date :** 2026-10-11 | **Statut :** PREPARATION / non approuvé | **Données :** code, tests et fixtures synthétiques exclusivement.
**Périmètre :** #923 OCR, #924 refus IA, #925/#927 SSE/CSRF/ingress, #929 P3 dormant (décision A). Aucun traitement patient, aucun accès à des logs de production, aucun merge ou déploiement.

## 1. Baseline reconstruite en lecture seule

- `main@13b7cce12c86daf60119fb703f22e8c6c192cf8d` (branche de base réelle, sans handover V1-03).
- #932 `15cfe25fcc93fff00a1198d705fb683c7a2eb960` : 16/16 workflows success.
- #933 `6b75ac3e4e88c9337ed480631859fa363f30f8bc` : branche documentaire, **zéro workflow pull_request trouvé sur ce HEAD exact** à la reprise ; anciens 16/16 = autres SHAs.
- #934 `f0b02165b478db6b6bb25d33f534a502ffa542f8` : 19/19 success ; refus IA persistant **par installation**, pas révocation globale.
- #935 `5f2378ee7935bb64b5af850b6bfb2e68a9a49ebe` : 16/16 success ; GET SSE legacy 405 sans Location/provider, OpenAPI POST JSON.
- #936 `62cc18bc0266838a98bbd7fe6b3ad8c794c82938` : 16/16 success ; trace ancienne de timing bootstrap.
- #937 `4d287bb1c8049b416b7e0f2c7ad5aa031c370ca7` : 16/16 success ; CI #38174457859 6/6 jobs success ; base #936, ahead 2 / behind 0, 7 fichiers. Toutes six PR DRAFT, ouvertes, fusionnables, **non fusionnées** lors du contrôle.
- ADR-0009 **ACCEPTED** : `/api/v1/diabetes/*` réservé/dormant pour V1 ; seul l'API canonique est exposée. Les tests #937 vérifient absence OpenAPI/resolver, 404 même avec urgence synthétique, absence d'appel fournisseur et triage du chat canonique.

Ces chiffres attestent des runs GitHub associés aux HEAD ci-dessus, **pas** d'une exécution locale dans cette reprise, ni d'un avis clinique, privacy ou sécurité indépendant. Toute mutation de HEAD invalide le transfert de preuve.

## 2. Vue adversariale A — transport, vie privée, compatibilité

| Risque à démontrer ou exclure | Preuve actuelle | Test / pièce de preuve à obtenir | Verdict |
| --- | --- | --- | --- |
| Ancien GET SSE transporte message dans URL | #935 : GET `?message=<marqueur synthétique>` refuse 405 sans redirect, sans réponse reflétée ni provider | Inventaire des clients **réellement diffusés**, SemVer/build, date de retrait GET ; plan d'upgrade vers POST JSON **sans jamais réactiver GET** | OPEN : clients non inventoriés |
| Proxy/CDN/WAF/APM conserve URL, body ou headers sensibles | `vercel.json` et CI ne décrivent pas les réglages effectivement en place ; inspection Vercel antérieure limitée aux identités de projets | Autorisation accès configs, export minimal des règles de collecte, redaction et rétention, puis requête synthétique à marqueur et contrôle de toutes les destinations ; ne pas ouvrir de log patient | OPEN : preuve infrastructure absente |
| Décision de compatibilité retourne une compatibilité fictive | `backend/core/app_compatibility.py` renvoie `version_unknown / compatible=None / update_required=False` si métadonnées absentes ; `frontend/pubspec.yaml` = `0.1.0+1` | Démontrer qu'un vrai ancien client envoie version/build, que le client actuel consulte la politique, et qu'aucune transition vers GET n'est suggérée | OPEN : distribution inconnue |
| Consentement/refus IA se perd au redémarrage ou sort du périmètre | #934 : tests Flutter/store/route et UI synthétique ; périmètre **installation**, pas cross-device | Matrice vrai iOS, Android, PWA : refus → redémarrage → hors ligne → appel chat/voix/image interdit ; second appareil indépendant ; réacceptation explicite ; changement d'identité et nettoyage local contrôlés | OPEN : appareils réels/non-patient |

**Contrôles négatifs requis en contexte autorisé :** cookie+Bearer falsifié, CSRF absent/invalide, chat urgent, déconnexion ou rupture SSE au milieu d'un flux, scope fournisseur relâché en erreur, et vérification que les journaux ne conservent pas de marqueur synthétique. Respecter le modèle de menace sur redirects et paramètres de requête ; un HTTP 405 **n'efface pas** la query déjà visible à l'ingress.

## 3. Vue adversariale B — provenance, clinique, UX

| Risque | Observation issue des sources | Gate de preuve |
| --- | --- | --- |
| OCR invente unité/mesure | #932 exige unité explicite, backend et Dart ; aucune preuve optique réelle | Corpus de photos glucomètres synthétiques/autorisées, unité visible, double/aucune unité, valeurs multiples, confusion date/série/mesure, résultat `null` quand non prouvé |
| HI/LO présenté comme concentration exacte | `GlucoseOcrShield` fournit `value=null`, drapeau HI/LO, confidence 1.0 de détection textuelle | Revue clinicien : copie, urgence/triage, refus d'une valeur numérique fabriquée |
| 401–600 mg/dL interprété silencieusement | Regex Dart `([4-9]\\d|[1-3]\\d{2}|400)` ne couvre pas 401–600 malgré commentaire | Arbitrage clinique avant toute correction de plage ; ne pas accepter via simple assouplissement regex |
| Texte reconnu sauvegardé sans confirmation | `needsConfirmation` peut être `false` sur valeur unitaire à confiance forte ; aucun parcours UI connecté prouvé dans l'inventaire ciblé | Si une activation future est approuvée : UI séparée de confirmation, annulation = zéro écriture DB, suivi provenance/unités et journaux sans PHI |
| Module dormant rouvert accidentellement | #937 retire montage dynamique, aligne manifeste/triage | Test HTTP et schéma sur branche intégrée, ne jamais interpréter l'absence de route comme validation CSRF d'une route future |

**Avant activation UI :** feature flag OFF par défaut, BEFORE/target/AFTER mêmes 390×844, 768×1024 et 1280×900, FR/AR/Darija et RTL pertinent, text scaling/accessibilité, tests vrai appareil. Aucun score visuel/clinique ne peut être attribué avant rendu observé et approbation.

## 4. Plan d'intégration sans merge — conflits et preuves

- **Empilement démontré :** #932 → #936 → #937. **Parallèles :** #933 (OCR/doc/ADR/roadmap), #934 (consentement UI), #935 (SSE). Ne pas concaténer les verts individuels comme un run d'intégration.
- Les changements partagés de `frontend/lib/services/api_client.dart` (#934 et composants parent) et des contrats auth/triage nécessitent une **comparaison diff effective sur branche candidate intégrée** ; aucun test d'intégration croisée n'a été lancé ici.
- Une intégration future doit disposer de : décision/autorisation de merge ; ordre de dépendances explicitement revu ; branche d'intégration ou cherry-picks traçables ; tests réels collectés au **nouveau HEAD** (Django SQLite/PostgreSQL, CSRF/egress, Flutter, OCR refus, UI, CI, migrations) ; audits indépendants privacy/sécurité/clinique ; confirmation finale.
- **Ne pas** basculer des bases vers `main` pour les laisser ainsi après CI ; éviter aussi tout merge, Vercel, accès PHI, activation P3 ou patient réel sans human gate.
- Les gates P5-6A/#318 et P5-6B/#320, le gel de release, réglementation/processor et autorisation patient restent distincts.

## 5. Critères de sortie / propriétaire des preuves

1. **Sécurité/privacy (humain qualifié) :** confirmer ingress/processeurs/consentement/CSRF, prouver minimisation et rétention, statuer sur les résidus. Toute détection de PHI non autorisé = BLOCKER.
2. **Clinicien qualifié :** matrice OCR HI/LO/401–600, unité, validation du libellé et de l'absence d'autosave ; aucune règle clinique inventée par test/code.
3. **QA vraie plateforme :** iOS, Android et PWA hors ligne, redémarrage, multi-instance, réacceptation ; résultats identifiés appareil/build/HEAD, sans patient réel.
4. **Certifieur indépendant :** comparer exigences→tests réellement exécutés, skips, HEAD, preuves visuelles, restrictions, décisions/risques ; autorisation de fusion séparée.
5. **Avant patient réel :** gates P5 et décision clinique/privacy/légale/release expressément validés.

**Verdict de cette reprise :** préparation de review pack uniquement ; **aucune nouvelle exécution de tests**, aucune preuve de vrais appareils/infra/clinique ; `NOT_RELEASE_AUTHORIZED`.

**Fichier de reprise :** `docs/handovers/2026-10-11-iamina-v1-03-option-a-p3-dormant-handover.md`. **Roadmap :** `docs/ROADMAP.md`, dans PR DRAFT #933, distinct du `main` en cours.

## 6. Contre-vérification des tests et artefacts — 2026-10-11

- **Opt-out #934 :** lecture source de `frontend/test/services/v1_03_local_decline_network_gate_test.dart` : les méthodes chat, voice, stream, transcription, média sont invoquées avec refus local ou absence de consentement ; `AuthService.getIdToken()` est instrumenté pour échouer s'il est appelé, et `MockClient` compte les requêtes sur Companion. Le test borne le réseau au niveau de ces méthodes simulées, **pas** un pare-feu universel, une vraie navigation réseau OS, ni un test multi-appareil.
- **Persistance #934 :** `consent_local_decline_store_test.dart` recrée deux instances `ConsentEvidenceStore` avec le **même mock `FlutterSecureStorage`** : preuve du contrat logique de lecture/écriture/effacement, pas preuve de persistance iOS/Android/PWA après fermeture réelle, backup ou réinstallation.
- **SSE #935 :** `test_v1_03_legacy_sse_no_provider.py` fait une requête Django `Client` avec marqueur synthétique, vérifie 405, zéro `Location`, zéro reflet et zéro instanciation d'IAmina, plus OpenAPI `post`/JSON sans `get`. Le test Dart `v1_03_sse_privacy_contract_test.dart` vérifie une requête HTTP construite avec POST et body JSON et une assertion statique de délégation au builder. **Aucun proxy/CDN traversé.**
- **OCR #933 :** le test Dart de non-activation balaie `frontend/lib` et protège l'absence de nouveaux appels OCR hors définitions. HI/LO demeurent `value=null`; valeurs multiples réclament confirmation. Le test reste une caractérisation sans images réelles ni certification patient.
- **Artefacts UI #934 :** le workflow `UI browser screenshot certification` run **38155284106** est vert et publie trois archives : `iamina-ui-browser-cert-390x844` (ID 11708623777), `768x1024` (11709220054) et `1280x900` (11708735983), non expirées lors de la lecture metadata. Ce contrôle **n'a ni téléchargé ni comparé les images**, donc aucun score visuel indépendant ne peut être attribué. Le workflow first-use run **38155284173** a aussi réussi, archive `iamina-first-use-mobile-390x844` ID 11708448310.
- **GitHub releases :** API releases de `hraaaaf/IAMINA-MVP`, première page, renvoie zéro release publiée ou draft dans cette collection. **Cela ne prouve pas** qu'aucun ancien APK/PWA/IPA n'a été distribué hors GitHub, ni qu'aucun client utilise encore l'ancien GET SSE ; obtenir un registre de distribution/installation autorisé reste nécessaire.

**Verdict :** les assertions sources et leurs workflows sont contrôlés ; aucun nouveau test réellement exécuté ici. Les preuves infra, optiques, appareils et clinique demeurent ouvertes. Ne pas assimiler ce travail à une seconde revue humaine indépendante.


## 7. Reprise approfondie — frontière LLM et Vercel en lecture seule (2026-10-11)

### A. Constat source sur la barrière de sortie effective

- Dans `backend/companion/conversation.py`, `_build_runtime_prompt` rassemble encore message, historique local et `DomainContext`. Les chemins `chat()` et `stream_chat()` passent ces prompts à `GatewayLLM.complete()` lorsque la narration est autorisée. Ces descriptions ne constituent **pas** une preuve que les prompts ont été envoyés à un tiers.
- `backend/core/llm_gateway.py` applique pseudonymisation et règles de gouvernance, puis appelle `LLMPipeline`. **Ce filtrage seul serait insuffisant** pour assurer « zéro contexte patient ».
- `backend/llm/factory.py::_enforce_text_payload_policy` impose le contexte, le contrat processeur et, pour tout provider externe, `_execute_external_complete` invoque **avant** `original_complete` la garde `assert_v1_external_text_generic_only`. `backend/core/external_text_v1.py` n'accepte qu'une **paire exacte, immuable, non-patient** : `GENERIC_SYSTEM_PROMPT` + `GENERIC_USER_PROMPT` ; les prompts dynamiques sont rejetés. Le chemin external `stream` / `think` reste refusé dans la fabrique. La porte externe `backend/llm/runtime.py` refuse aussi tout média patient via `assert_v1_external_media_egress_denied`.
- Test existant `backend/llm/tests/test_runtime_finops_wiring.py::test_v1_03_last_network_hop_denies_patient_context_even_with_approved_policy` : **six fixtures** FR/AR/EN et statistiques/historique/insuline ; le test simule un processeur externe approuvé + budget configuré, attend `AIProcessorPolicyDenied`, affirme `provider.calls == 0`. Les workflows CI du parent #932 sont verts sur leur HEAD. **Aucun nouveau test lancé à cette reprise**.
- **Exception bornée distincte :** `backend/companion/protected_provider_shadow.py` dispose d'un chemin `complete_text` vers Groq, sous feature flag OFF par défaut, réservé à un sujet interne/staff dans son mode live, et limité par vérification stricte au triplet `locale/script/opaque token`. Les tests `test_protected_provider_shadow.py` examinent refus des tokens non opaques, locales interdites et sujets non autorisés. Cette exception demande une revue des corrélations de locale/script et de sa configuration *réelle* avant toute activation ; elle **n'autorise pas** d'egress patient standard.
- **Verdict de portée :** la preuve source et les tests préexistants étayent le refus des **prompts patients dynamiques** avant l'ultime appel externe des chemins parcourus ; cela ne certifie pas tous les environnements, les processus externes, une config future ou une conformité réglementaire. Les docstrings anciennes d'AI endpoint décrivent encore « call LLM » et doivent être lues comme descriptions historiques, non comme preuve d'egress effectif.

### B. Observation Vercel liée aux journaux, sans lecture de contenu patient

Deux projets ont été revérifiés via `get_project` authentifié : `iamina-certified` et `iamina-review`. Sur `iamina-certified`, indicateur Vercel `ssoProtection.enabled=true` avec `all_except_custom_domains`; sur `iamina-review`, `ssoProtection.enabled=false`, `passwordProtection.enabled=false`, `trustedIps.enabled=false`. Ces **flags projet** ne prouvent pas que l'application est accessible sans son propre contrôle d'accès, ni que des données patient sont présentes. C'est un **point de revue de l'exposition des surfaces review**, pas un incident de fuite établi.

`list_project_routes` renvoie `routes=[]` pour les deux projets ; cette API représente les règles de routage Vercel contrôlées par elle, **pas** nécessairement toutes les rewrites définies dans les fichiers `vercel.json`. `list_drains` renvoie HTTP 404 pour les projets, **y compris avec teamId explicite** : configuration des drains **UNKNOWN**, jamais « aucun drain ». Les réponses `get_project` ne fournissent ni politique de collecte des URLs, ni masquage du corps/headers, ni durée de rétention.

Source technique primaire Vercel : [documentation du format Log Drains](https://vercel.com/docs/llms-full.txt) contient un exemple de champ `proxy.path` incluant `?page=1`. Cette **possibilité documentaire** rend important l'audit des anciennes URL GET avec query ; ce n'est pas une preuve qu'une URL patient IAMINA a été enregistrée. Sources de surface : [protection des déploiements Vercel](https://vercel.com/docs/deployment-protection/methods-to-protect-deployments/vercel-authentication).

**Gate technique non substituable :** obtenir une vue autorisée et minimisée des réglages réels des collecteurs, rétention, redaction et sites de destination ; évaluer les réglages de protection du projet review ; tester avec une marque synthétique unique seulement dans un environnement expressément autorisé, sans consulter de PHI ni déclencher de déploiement. Aucun test live ni modification d'infrastructure dans cette reprise.

### C. Recommandation de la revue indépendante

**Perspective sécurité :** ne pas lever le gate SSE tant que l'inventaire de distribution et des collecteurs est UNKNOWN ; ne pas considérer HTTP 405 comme une suppression rétroactive d'une query reçue à l'ingress.

**Perspective clinique et privacy :** ne pas élargir la barrière générique en se fondant sur des regex de pseudonymisation. Conserver la comparaison exacte au dernier appel externe, les refus média et la dormance P3 ; examiner séparément l'exception staff/opaque avant toute activation. Aucun essai sur vrais patients.

**Statut :** audit source/read-only et caractérisation de preuve existante, **pas** qualification indépendante humaine, pas de test exécuté ici, pas de CI déclenchée sur HEAD documentaire #933.


## 8. Inventaire Flutter ciblé de consommation app-compatibility (2026-10-11)

**Baseline du scan :** PR #934, `f0b02165b478db6b6bb25d33f534a502ffa542f8`, sans modifier le code.

- Sous `frontend/lib/services`, la liste Git tree de **33 fichiers Dart** a été reconstruite puis chacun de ces fichiers a été lu. Inclut `api_client.dart`, `companion_service.dart`, `auth_service.dart`, `consent_service.dart`, `sync_service.dart` et les fichiers `api/generated`.
- Six points d'entrée supplémentaires inspectés : `frontend/lib/main.dart`, `routes/app_router.dart`, `features/auth/consent_screen.dart`, `features/auth/local_device_enrollment_screen.dart`, `features/profile/profile_screen.dart`, `features/profile/profile_screen_presentation.dart`.
- Recherche ciblée et insensible à la casse : `app-compatibility`, `appCompatibility`, `version_unknown`, `update_required`, `minimumSupported`, `clientBuild`, `client_version`. **Zéro référence trouvée dans ces 39 fichiers Dart source.** Ceci est un inventaire statique de chemins choisis, **pas** une preuve d'absence sur tous les modules/features, ressources natives, distributions et versions historiques.
- En parallèle, `backend/core/app_compatibility.py` expose déjà une logique déterministe version/build ; `version_unknown` ne force pas de mise à jour lorsque les métadonnées manquent. `backend/core/tests/test_app_compatibility.py` couvre ces états serveur. **Pas de preuve d'un appel Flutter associé** dans le périmètre inspecté.
- **Finding pré-distribution (à traiter)** : le backend peut annoncer une version minimale, mais le mécanisme observable de consultation, affichage et reprise côté client reste **NON PROUVÉ**. Ne pas inventer une migration automatique, un parc historique distribué, ou une compatibilité assurée. Si un client ancien envoie toujours GET avec contenu patient, le nouveau serveur le bloque à 405, mais le contenu a déjà été présenté en URL à l'ingress.

**Next engineering proposé, non implémenté :** établir la liste des canaux de distribution et versions effectivement installées (sans PHI), puis concevoir une consultation facultative/non bloquante de l'API de compatibilité tenant compte du **local-first**. Une transition de sécurité/upgrade vers POST ne doit **jamais réactiver** GET avec message en query, et un état `version_unknown` ne doit pas être présenté comme « client sûr/à jour ». Toute modification UX exige BEFORE/target/AFTER et tests de panne offline, anciens clients, iOS/Android/PWA. Aucune politique de mise à jour forcée n'a été autorisée ici.

**Validation :** vérification de source sur 39 chemins au SHA indiqué, aucune compilation, test nouveau, audit de distribution ou validation de CI supplémentaires à ce HEAD.

## 9. Vérification des alias réellement servis et contre-preuve au risque GET actif (11 octobre 2026)

**Audit dédié :** [`2026-10-11-v1-03-deployed-sse-url-privacy-divergence.md`](2026-10-11-v1-03-deployed-sse-url-privacy-divergence.md). Les alias Vercel pointent bien vers le frontend `1e44ba57` et le backend `b13b44e7`, antérieurs aux PR #934/#935. Les sources historiques contiennent `GET /ai/chat/stream?message=...` dans `ApiClient.chatStream` et dans l'endpoint Django. **Mais la contre-vérification du JS compilé réellement servi** par `iamina-review.vercel.app` (`HTTP 200`, 5 066 376 caractères) ne trouve aucune chaîne `chat/stream`; elle trouve `POST /api/v1/ai/chat`. Le routage Flutter actif `/companion/chat` mène à `CompanionConversationScreen` et à `CompanionService.sendChatMessage` en POST, non au widget historique `AminaChatView`. La fuite par le parcours web actif est donc **NON DÉMONTRÉE** et ne doit pas être affirmée. Le backend répond `401` via connecteur à une requête anonyme sans message ; ce n'est pas un test de GET authentifié. Restent inconnus les anciens clients/PWA, ingress logs et usage réellement authentifié. Une protection par simple rejet GET 405 ne supprime pas des URLs déjà émises par d'anciens clients. Pas de patient ni de mutation Vercel. La remédiation du contrat GET reste requise avant pilote, sur décision humaine de rollout.
