# IAMINA V1-03 — Gate de transition clients SSE et confidentialité (12 octobre 2026)

> **État : PRE-RELEASE / NOT_RELEASE_AUTHORIZED.** Audit sur code et métadonnées seulement, **aucun** patient réel ou journal contenant PHI consulté. Le gate ne s'ouvre pas parce que les workflows sont verts.

## 1. Goal, succès, preuves

**Goal exact :** remplacer les consommateurs déployés de `GET /api/v1/ai/chat/stream?message=...` par le `POST /api/v1/ai/chat/stream` JSON authentifié, **sans** exposer de texte patient en URL lors du cutover, sans perdre refus IA local ni données offline et sans réintroduire des appels LLM dans les résumés locaux.

**Succès observable :** ancienne installation réaliste `0.1.0+1` → client `0.1.0+2` mise à jour sans perte de données et sans GET patient ; cookies/CSRF et Bearer fonctionnent ; anciennes requêtes GET ne redirigent jamais et ne déclenchent pas de fournisseur ; aucune collecte de query patient aux points d'entrée selon politique documentée et essai **uniquement à marqueurs synthétiques** ; revue privacy/security écrite ; preuve sur vrais PWA, iOS et Android représentatifs.

**Preuve déjà acquise** : PR [#941](https://github.com/hraaaaf/IAMINA-MVP/pull/941) HEAD exact `d3562e814e39d412516f421e66cb285fa7df50ce`, **25/25 workflows GitHub SUCCESS**. CI [`38252290789`](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38252290789) 6/6 ; P5-4A Chrome update [`38252290695`](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38252290695) relance ciblée réussite ; Android TD-008 [`38252291102`](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38252291102) émulateur CI réussite. **Ces validations sont synthétiques, pas un recensement ni une migration d'installations existantes.**

## 2. Provenance vérifiée (Git SHA source + métadonnées Vercel)

| Surface | Production déployée / SHA | Code vérifié dans ce SHA | Candidat certifié #941 |
| --- | --- | --- | --- |
| Frontend `iamina-review` | Vercel prod `dpl_CJpLFLEQngvjsZXj23FinoXYoH1t`, commit `1e44ba57ad63638b1eb15af916adc54d0f8c15fc` | `frontend/pubspec.yaml` **`0.1.0+1`** ; `frontend/lib/services/api_client.dart::chatStream` construit encore GET avec texte patient dans query ; SW `IAMINA_CACHE_SCHEMA='0.1.0+1'` et application shell cache-first | `0.1.0+2`, `buildPatientSseRequest()` **POST corps JSON**, SW `IAMINA_CACHE_SCHEMA='0.1.0+2'` |
| Backend `iamina-certified` | Vercel prod `dpl_7SogpUMHNHd9rF7s7rfALccKduv7`, commit `df004bcb25d2ae5c9004825ebee092306696b9e5` | `backend/ai/api/v1/ai.py` expose **GET** SSE ; `DEFAULT_LATEST_BUILD=1` | **POST** SSE authentifié avec urgence après auth/CSRF ; **GET ancien 405 sans redirect/provider** testé ; `DEFAULT_LATEST_BUILD=2`, minimum conservé `0.1.0+1` |
| Hébergement / visibilité | Vercel `get_project` (lecture seule) : frontend password/SSO IP protection **non activés** ; backend SSO **activé pour `all_except_custom_domains`**, pas de preuve d'autorisation effective de l'API | `list_project_routes` retourne `routes=[]` pour les deux projets ; **cela ne prouve pas l'absence de `vercel.json` ou de rewrites déployées.** `list_drains` répond HTTP **404**, `list_project_connector_connections` HTTP **404**. Aucun inventaire rétention/sinks établi. | Aucun déploiement ; sans autorisation Vercel explicite, **ne pas** modifier/prober des données patients ou logs réels. |

**Limite fondamentale :** les commits des deux déploiements prouvent le code associé aux artefacts Vercel ; ils **ne** prouvent **ni** combien de PWA restent installées, **ni** quels stores iOS/Android ont distribué quelles versions, **ni** le volume de messages en URL, **ni** une fuite patient observée.

## 3. Conflit de séquencement qu'un CI 25/25 ne résout pas

- **Backend d'abord** : anciens `0.1.0+1` continueront d'émettre le GET **avec query patient** jusqu'à mise à jour. Le serveur nouveau répond 405, mais cette réponse n'efface ni la requête URL déjà partie, ni les traces ingress possibles.
- **Frontend d'abord** : nouveau `0.1.0+2` émet POST JSON alors que le backend actuel n'a que GET SSE ; rupture de service prévisible. Ne pas inventer de fallback GET ni redirection.
- **PWA cache-first** : l'application installée peut utiliser un ancien `main.dart.js` après diffusion du nouveau HTML/bootstrap ; le seul numéro SW distinct ne prouve pas une éviction immédiate de tous les onglets et profils.
- **Compatibilité** : le backend candidat marque l'ancien build `update_available` et non `update_required`; un client ancien qui ne consulte pas l'endpoint de compatibilité ne peut pas être mis à jour par ce mécanisme. Ne pas activer un `forced update` sans distribution/inventaire et parcours de récupération prouvés.
- **Résumé/Doctor Brief** : reprendre `backend/ai/api/v1/ai.py` de #938 dans son intégralité serait une régression (appel LLM au lieu de narration déterministe). #941 est la base exacte à préserver.

**Conclusion de séquencement :** aucun ordre de deux bascules aveugles ne garantit à la fois zéro GET préexistant et zéro indisponibilité. Le cutover demande une **décision humaine structurée**, un inventaire, une stratégie de mitigation des URLs au point d'entrée avant bascule si nécessaire et une fenêtre de transition/coupure documentée. Pas de déploiement autonome.

## 4. Collecte de preuves nécessaire — sans PHI

| Piste parallèle | Responsable / décision nécessaire | Exécution de validation | Critère Go/No-Go |
| --- | --- | --- | --- |
| **A — Parc clients** | Responsable distributions PWA / Android / iOS et build signing | Inventaire **agrégé uniquement** par version/build, canal, OS, date, mécanisme de mise à jour et nombre d'installations actives ; confirmer si legacy consulte `app-compatibility`. Ne jamais lire requêtes ou identifiants réels. | Tous canaux connus et politique de migration vérifiée ; si version inconnue, **NO-GO** |
| **B — Cache PWA authentique** | QA frontend avec profil Chrome synthétique neuf | Installer l'**ancien code réellement compilé depuis SHA `1e44ba57`** sur origine d'essai, établir SW `0.1.0+1`, fermer et garder onglet ouvert en deux cas, servir nouvelle build #941, tester mise à jour, reprise offline, données Drift, refus AI, requêtes réseau. Le workflow P5-4A actuel reconstruit son « v1 » depuis le même build de probe : ce n'est **pas** la transition historique réelle. | Aucun GET envoyé depuis nouvelle version ; tout client restant ancien explicitement détecté/mitigé ; offline/consentement préservés |
| **C — Appareils physiques** | QA native + security/privacy | Installer builds précédents effectivement distribués, puis nouveau build signé sur appareils iOS/Android autorisés ; redémarrage, hors ligne, multi-comptes, refus IA persistant, réacceptation explicite, absence requêtes IA après refus et auth/CSRF. Données synthétiques uniquement. | Parcours fonctionnels + zéro IA réseau non consentie ; preuve appareil/version ; sinon **NO-GO** |
| **D — Ingress / logs** | Responsable infrastructure + DPO/privacy | Fournir configuration Vercel/CDN/edge/WAF/APM/redirect/proxy, drains, accès aux logs, rétention et éventuels traitements URL/query ; essais `SYNTHETIC_V103_URL_CANARY` uniquement, mesure de présence *sans afficher contenu des URLs*. Corriger/purger selon politique autorisée et avis privacy, pas sur simple hypothèse. | Redaction/suppression démontrée et signée avant bascule ; `list_drains` 404 = **INCONNU**, donc **NO-GO** |
| **E — Revue clinique OCR** | Clinicien qualifié + product safety | Maintenir OCR OFF ; vérifier un corpus autorisé avec unité réellement affichée `mg/dL`/`mmol/L`, `HI/LO`, plage 401–600 mg/dL, absence d'hallucination et confirmation explicite avant écriture. Revue UI BEFORE/AFTER mêmes viewports si activation modifie l'écran. | Signature clinique et traçabilité ; sans signature **OCR OFF** |

## 5. Point de validation et séquence restante

**Avant tout changement patient** : consigner pour chaque piste la version et l'environnement d'essai, l'auteur de la validation, la date, les cas exécutés, leurs pièces non sensibles et `PASS/FAIL/BLOCKED`. Réconcilier avec la matrice CI du HEAD #941. **La lecture des métadonnées Vercel n'est pas un audit logs**.

**Décision à obtenir** : autorisation et stratégie de **cutover** après preuves A–D, revue indépendante security/privacy et clinique E. Puis **autorisation explicite de merge**, CI post-merge ; **autorisation Vercel distincte** avant tout deployment ; validation déployée sur trafic **synthétique uniquement**, surveillance de métadonnées sans PHI, document closeout/roadmap/Notion.

**Go/No-Go actuel : NO-GO PATIENT / NOT_RELEASE_AUTHORIZED.** Succès CI #941 25/25 ≠ succès de déploiement, de migration ni de revue humaine. P5 historique 6/12 = 50 %, n'inférer aucun % V1-03.
