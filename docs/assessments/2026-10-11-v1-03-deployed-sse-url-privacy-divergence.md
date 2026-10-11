# IAMINA V1-03 — Divergence SSE des alias Vercel et du code corrigé

Date : 2026-10-11. Statut : **RISQUE CONFIRMÉ DANS LA SOURCE ASSOCIÉE AUX DÉPLOIEMENTS, FUITE NON ÉTABLIE**. Domaine : confidentialité des messages de conversation. Aucun accès ni génération de données patient ; aucun déploiement, aucune modification Vercel. Les preuves ci-dessous sont des métadonnées de déploiements et des fichiers source vérifiés aux commits exacts, pas un replay HTTP en production.

## Goal, succès, preuve

- **Goal** : établir si le correctif SSE POST JSON de V1-03 est effectivement servi derrière les deux alias publics de revue et du backend, sans requête porteuse de PHI.
- **Succès souhaité, non atteint** : alias courants pointant vers un frontend sans message en URL et un backend POST-only, avec anciens clients explicitement contenus, plus vérification ingress et vrais appareils non patients.
- **Preuve obtenue** : `get_alias` Vercel authentifié pour chaque alias, `get_deployment` avec métadonnées Git, `fetch_file` GitHub aux SHA exacts, comparaison au correctif de PR #935 / #934. Pas de test de runtime.

## 1. État réel des alias (Vercel en lecture seule)

| Alias vérifié | Deployment ID (READY) | Commit source de la build, selon metadata Vercel | Contrat actuel dans la source |
|---|---|---|---|
| `iamina-review.vercel.app` | `dpl_CJpLFLEQngvjsZXj23FinoXYoH1t` | `main` : `1e44ba57ad63638b1eb15af916adc54d0f8c15fc` | **Frontend Flutter GET avec `?message=`** |
| `iamina-certified.vercel.app` | `dpl_E3fMNHmVk2iH5Qsz9GAUxv8MpGzH` | `preview/intent-envelope-v1-demo` : `b13b44e7d1fe23ae22fb17a31b64d7297b764786` | **Backend Django-Ninja GET avec argument `message: str`** |

Vercel `get_alias` a confirmé que les alias renvoient précisément à ces deux deployment IDs. `get_deployment` confirme `READY`, les références Git et les SHA cités. La protection **projet** du frontend review montre SSO OFF, password OFF, trusted IP OFF ; cela ne démontre ni absence de session/auth API ni exposition de patient. Le backend certified a SSO ON en mode `all_except_custom_domains` ; l'efficacité concrète sur chaque route et le comportement de bout en bout nécessitent un test autorisé.

La configuration `frontend/vercel_build.sh` au SHA `1e44ba57` définit `IAMINA_CERTIFIED_API_BASE_URL="https://iamina-certified.vercel.app"` et force cette valeur si `VERCEL_PROJECT_ID` vaut l'ID du projet de review (`prj_AYaUi32KTDHak8I7dmdQpDrqd8SI`). **Limite** : la variable effective du build et les octets réellement servis du bundle JS n'ont pas été inspectés ; il s'agit du chemin attendu selon la configuration source.

## 2. Chaîne de portée Flutter, source exacte

- Frontend à `1e44ba57`, `frontend/lib/features/journal/widgets/amina_chat_view.dart`, méthode `_send` : reçoit le texte utilisateur, puis appelle `apiClient.chatStream(msg).listen(...)`.
- Même commit, `frontend/lib/services/api_client.dart`, `chatStream(String message)` : `Uri.parse('$baseUrl/api/v1/ai/chat/stream').replace(queryParameters: {'message': message})`, puis `http.Request('GET', uri)` et header `Authorization: Bearer` lorsque le token est disponible. **L'ajout d'un header Authorization n'empêche pas la présence du message en URL.**
- Backend à `b13b44e7`, `backend/ai/api/v1/ai.py` : `@router.get("/ai/chat/stream")`, `def chat_stream(request, message: str, context_days: int = 14)`, docstring `GET /api/v1/ai/chat/stream?message=...`.

**Conclusion source** : si le bundle et l'API réellement servis correspondent à ces sources, le flux utilisateur atteignable construit encore une URL à contenu libre, et le backend déployé contient la route GET qui le reçoit. Une URL peut figurer dans les historiques intermédiaires, journaux d'accès, outils de monitoring ou traces ; **nous n'avons pas vérifié** si un de ces systèmes l'a retenue sur IAMINA. Rien ne permet d'affirmer « fuite de PHI avérée ».

## 3. Correctifs présents dans le code non déployé

- PR #934 à `f0b02165b478db6b6bb25d33f534a502ffa542f8` : `ApiClient.chatStream` utilise `buildPatientSseRequest` et un contrôle de consentement local. Le builder envoie le message dans un POST JSON ; test `frontend/test/services/v1_03_sse_privacy_contract_test.dart`.
- PR #935 à `5f2378ee7935bb64b5af850b6bfb2e68a9a49ebe` : `@router.post("/ai/chat/stream")`, `ChatRequest` JSON ; tests Django de GET legacy refusé (405), sans redirect, sans provider et sans écho de query. La CI 16/16 précédemment vérifiée vaut **uniquement** pour son SHA et ne prouve pas l'état live.
- La correction backend seule peut retourner 405 aux anciens clients, **mais n'empêche pas leur émission de PHI dans l'URL avant l'ingress**. La correction frontend seule cesse l'émission dans ce flux, **mais serait incompatible** avec le vieux backend GET. Ne jamais réintroduire GET PHI comme compromis de compatibilité.

## 4. Deux examens contradictoires, décisions et prochaines preuves

**Sécurité / red team :** classer la divergence live comme **risque de confidentialité prioritaire avant tout pilote patient**. Il faut une mesure d'exposition temporaire et une fenêtre de coupure coordonnée ou un contrôle d'accès aux surfaces review. Vérifier la protection effective des domaines, le build JS servi, les captures en ingress avec marque synthétique, et les politiques réelles de retention/redaction. Aucune donnée patient pour le test.

**Release / blue team :** ne pas confondre code corrigé et code déployé ; préserver la fonction local-first/hors ligne, expliciter la perte possible de chat lors du remplacement GET→POST et la gestion des clients déjà installés. Le backend `app-compatibility` peut décrire `version_unknown` mais la consultation côté Flutter n'était pas démontrée dans les 39 fichiers inspectés de #934. Aucun signal de parc installé fiable : GitHub Releases renvoie 0 release dans la première page, ce qui **ne prouve pas** aucune diffusion PWA/APK/TestFlight/App Store.

**Décision humaine requise et non exécutée :** autoriser **A)** restriction immédiate de la surface `iamina-review` / de l'accès API certifié le temps du basculement, ou **B)** plan explicite de coupure de chat et promotion coordonnée des builds déjà revus avec vérification runtime et rollback. Une modification de protection Vercel, d'alias ou un déploiement est un changement de production interdit sans autorisation.

## 5. Validation croisée et closeout

- Métadonnées Vercel : `get_project` et `get_alias` pour les deux projets, `get_deployment(...withGitRepoInfo=true)` pour chacun.
- Source GitHub : fichiers cités, aux deux SHA de déploiement, et chemins corrigés aux SHA #934/#935.
- `vercel.json` des deux refs frontend indique `git.deploymentEnabled=false` et une rewrite SPA `/(.*)→/index.html`. L'API Vercel de routes projet renvoyant [] n'était donc pas un inventaire de ces rewrites fichier.
- **Aucun HTTP live avec PHI, aucune lecture de logs, aucun test de sécurité en prod.** Accès HTTP statique externe au site non accessible par outil web, donc **aucune preuve binaire** que le JS en production est exactement identique à celui compilé des sources.
- Suites : alerte dans GitHub/Notion, gate de permission Vercel, preuve de bundle réel et de journaux sans PHI, essais synthétiques et multi-device, validation CI de la pile exacte après approbation d'intégration.

**Statut final du présent audit :** `DEPLOYED_SOURCE_SSE_GET_QUERY_RISK_CONFIRMED` / `LIVE_DATA_LEAK_NOT_VERIFIED` / `NOT_RELEASE_AUTHORIZED`. Ne pas utiliser le site de review avec de vraies conversations sensibles avant le gate d'exposition.
