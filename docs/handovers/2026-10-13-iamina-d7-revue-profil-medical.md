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
