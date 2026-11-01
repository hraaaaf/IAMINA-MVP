# IAMINA — D7 / First User Experience — patient revenant modifier son profil

**Date :** 31 octobre 2026. **Décision : D7 — Déclaration du type de diabète et des traitements réellement pris, sans prescription ni inférence automatique.**
**Lot de consolidation :** [PR #1208](https://github.com/hraaaaf/IAMINA-MVP/pull/1208) (Web, Draft, sans merge). **Référence clinique / FUE :** [D7 gate canonique](2026-10-29-d7-web-fue-coverage-gate.md), [règles qualité](../QUALITY_SCORING_POLICY.md).

## Choix de la FUE et objectif

**Persona :** un patient déjà utilisateur d'IAMINA revient dans son espace pour corriger ce qu'il a *déclaré*. L'objectif n'est pas de valider un formulaire isolé : il doit pouvoir reconnaître ses choix, les modifier, les enregistrer, les retrouver après réouverture, sans changement de traitement imposé par IAMINA.

**Goal :** une personne peut distinguer et éditer indépendamment type de diabète, traitements effectivement pris et choix « rien à déclarer / je ne sais pas », avec un statut de sauvegarde exact et une conservation sûre des informations du bon coffre.

**Succès observable :** scénario sans erreur sur le **vrai produit Flutter Web** au SHA testé, sur données synthétiques, avec preuves par état avant/après, sauvegarde persistante, rechargement, sécurité du verrou, FR/AR RTL et viewports 390×844, 768×1024, 1280×900. La FUE doit couvrir aussi les erreurs et la récupération. **100 % des cas requis = PASS** pour la validation binaire D7 ; NOT_RUN ou FAIL implique FUE_NO_GO. Aucune conclusion médicale ni score inventé.

## Parcours utilisateur principal — FUE-D7-01

1. **F01 — Entrée et retour.** Ouvrir IAMINA Web sur navigateur neuf ; choisir le parcours local autorisé, configurer/déverrouiller le coffre, terminer l'onboarding ; revenir dans « Profil > Suivi médical ». Le formulaire et les actions doivent être accessibles sans blocage ni donnée médicale fictive.
2. **F02 — Déclaration initiale.** Choisir « Type 2 » et déclarer volontairement « Médicaments oraux » et « Insuline ». Enregistrer : vérifier l'absence de message « synchronisé serveur » sans acquittement ; les éléments sont bien deux choix distincts.
3. **F03 — Persistance.** Fermer/réouvrir l'écran, recharger physiquement la page, déverrouiller ; retrouver exactement type 2 et les deux traitements (ni perdu, ni dupliqué).
4. **F04 — Correction de type.** Passer de type 2 à type 1, enregistrer/recharger ; les deux traitements restent inchangés. Aucun conseil thérapeutique automatique.
5. **F05 — Incertitude puis décision explicite.** Passer de type 1 à « Je ne sais pas / plus tard » ; garder les traitements. Sélectionner explicitement « Aucun traitement à déclarer », sauvegarder/recharger ; la déclaration passe à « aucun », sans prétendre que l'utilisateur ne prend aucun médicament au sens clinique.
6. **F06 — Retour au choix.** Déclarer explicitement « Insuline », enregistrer/recharger : « aucun » est remplacé par la déclaration volontaire, sans restauration cachée d'anciens choix.
7. **F07 — Résilience réseau et statut.** Répéter une sauvegarde en local/pas de réseau, puis restaurer la connexion : le libellé ne doit pas annoncer un succès distant non vérifié ; aucune requête vers un domaine non autorisé, aucune erreur JS/PWA bloquante.
8. **F08 — Présentation et accessibilité.** Capturer les états initial, « type inconnu » et « aucun traitement » sur 390×844, 768×1024 et 1280×900 ; vérifier intégrité du formulaire, CTA visibles, clavier/focus, AR en RTL et FR, textes non prescriptifs. Même viewport/état pour les comparaisons BEFORE→AFTER.

## Parcours associé au correctif #1208 — FUE-D7-02 (consentement et verrou)

Ce parcours est **dans le périmètre produit** de la PR #1208 ; la FUE-D7-01 seule ne le clôt pas.

- **C01 — Choix libre.** Sur la Preview QA protégée et épinglée au SHA exact, sélectionner « Continuer sans IA » ; pas de consentement implicite, le profil reste utilisable.
- **C02 — Verrou explicitement ignoré.** Si « continuer sans verrouillage » a été choisi, le bouton « Accepter » ne doit pas enregistrer de consentement ; le parcours doit offrir « Activer le verrouillage ».
- **C03 — Consentement effectif.** Activer/déverrouiller le coffre, puis accepter explicitement la notice versionnée ; le serveur doit confirmer l'enregistrement, et la navigation doit être cohérente.
- **C04 — Échec et récupération.** Si l'API refuse/échoue, afficher un message explicite, sans fausse acceptation ni fuite de données ; « Continuer sans IA » reste possible.
- **C05 — Retrait / retour.** Vérifier que le retrait du consentement reste contrôlable, et que l'état ne se rétablit pas silencieusement.

**Attention :** le retour iPhone positif de l'utilisateur valide le parcours qu'il a réellement essayé sur la Preview `2fe625cf...`, **pas automatiquement les états négatifs, les viewports supplémentaires ou le SHA de #1208**. Pas d'accès à l'environnement protégé ni de déploiement sans permission spécifique. Les identifiants, tokens, captures nominatives et données de santé ne doivent jamais être versés dans les artifacts.

## Frontière conditionnelle — isolation A → B → A

Le cœur D7 est **un patient revenant sur son dossier**. Réutiliser la preuve W02 d'isolation lorsque son SHA/frontière reste applicable. Pour les frontières modifiées par #1208 (verrou/consentement), ajouter une vérification **ciblée et non destructive** de changement de session A→B→A si les preuves W02 ne couvrent pas le risque. Ne pas ouvrir `GET /api/v1/profile` dans le BFF simplement pour faire passer un test : le coffre clinique reste local-first et protégé.

## Exécution et registre de preuves (à compléter, sans présumer des résultats)

| Cas | Preuve attendue | Statut initial |
| --- | --- | --- |
| F01–F06 | Vrai Chrome + Flutter Web / WebAuthn / SQLite WASM IndexedDB, états avant/après et reload | NOT_RUN pour cette PR |
| F07 | Network egress/offline et vérité du statut de sauvegarde | NOT_RUN pour cette PR |
| F08 | 9 captures comparables 390/768/1280 ; FR/AR RTL ; clavier/focus et erreurs | NOT_RUN pour la FUE intégrée complète |
| C01–C05 | Recette vraie Preview QA du consentement, verrou et retrait sur le SHA correct | NOT_RUN sur cette PR |
| Isolation owner si applicable | Preuve W02 compatible ou A→B→A ciblé, sans données réelles | À justifier / NOT_RUN |
| Revue clinique/privacy | Choix non prescriptifs, sécurité, stockage, CNDP et absence de faux ACK | PENDING |
| Exécution et adversarial / Perfection Pass | Scores sur preuves, analyse des écarts, dernier passage de perfection | NOT_RUN |

### Banc automatisé de départ

Le test `scripts/d7_web_actual_profile_e2e.py` est repris de la branche QA D7 : **huit phases** sur le vrai Web local, un coffre synthétique, Chrome et WebAuthn, **neuf captures** (type 2 / inconnu / aucun × 3 viewports). Il peut prouver F01–F06 partiellement et une partie de F07/F08. Il utilise des libellés anglais pour les interactions automatisées ; les widgets FR/EN/AR et leurs responsive tests sont exécutés séparément. **Ce banc ne certifie ni FR/AR sur la navigation complète, ni consentement distant, ni permissions réelles, ni A→B→A authentifié.**

Le workflow `.github/workflows/d7-fue-returning-patient-web.yml` est **sans secrets**, uniquement Pull Request, avec conservation bornée des PNG synthétiques et du verdict JSON. Toute sortie `PASS` de ce banc est une **preuve partielle** et ne transforme pas la FUE globale en PASS.

**Décision de closeout :** ne pas sortir la PR #1208 de Draft et ne pas merger tant que la matrice complète n'est pas à 100 % PASS, que les dimensions critiques et le Perfection Pass de `docs/QUALITY_SCORING_POLICY.md` ne sont pas satisfaits et que le gate humain de fusion n'a pas été donné. Aucun déploiement Vercel autorisé par cette fiche.

## 31/10/2026 — Perfection Pass / adversarial finding: withdrawal must be fail-closed

**BEFORE — confirmed source finding on deployed main `ed8c67e0`:** `ProfileScreen._confirmWithdrawConsent()` discarded the bool result of `ApiClient.withdrawConsent()` and always showed the success Snackbar even when DELETE returned false/failed. This violated the C05 negative/recovery case and represented a **blocking privacy/truthfulness defect**. It also did not clear `ConsentEvidenceStore`, allowing stale local proof to remain. **No prod user records were read or modified to establish this code-level finding.**

**Goal:** a withdrawal click immediately disables the local AI gate, saves a durable *patient-vault-scoped* pending-withdrawal marker before network contact, explicitly validates the server's `ai_consent_given=false` receipt, clears local notice evidence and DB only after verified remote revocation, and preserves a visible retry action across page reload if remote withdrawal is unconfirmed. Never show `Consentement retiré` on a failed remote result. Clear pending only after both server and local writes are confirmed. An explicit new verified grant may clear a previous pending marker.

**Prepared patch under PR `fix/d7-consent-revocation-fue-20261031`:** introduces `d7_consent_withdrawal.dart`, owner-scoped marker in secure storage, fail-closed ConsentService, startup pending-state restoration, Profile retry CTA and explicit success/warning messages FR/EN/AR, exact server response check in ApiClient. New C05 tests exercise success, rejection, offline exception, marker failure, cleanup failure, retry and misleading 2xx receipt. Workflow D7 adds these synthetic cases before Chrome patient-profile FUE.

**Important limits / binary gates:** synthetic test suite on a PR can prove only these controlled conditions; it is not evidence for real hosted auth/WebAuthn/remote consent across FR/AR or an independent privacy signoff. **FUE D7 remains NOT_VERIFIED** until all required C01–C05 cases on a real permitted QA environment, profile persistence/negative states, actual viewport comparisons, and Perfection Pass score are reviewed with adequate evidence. Old production remains on `ed8c67e0` unless a separate authorized deployment follows.


## 01/11/2026 — D7 QA : runner A→B→A repointé, certification toujours NO-GO

**Décision :** corriger exclusivement la préparation du gate authentifié sur la branche QA, sans modifier le binaire Flutter/proxy déjà déployé, sans toucher à Production ni prétendre avoir exécuté une FUE réelle.

**Preview immuable vérifiée :** `dpl_9uEbft6CgxjtkEBjtvG6tiFjeZP8` READY, target Preview, SHA applicatif/proxy `55fa500f56d86d7fa014b5b1849d7e7cdad3ea59`; alias QA pointe toujours vers ce déploiement. Alias Production `iamina-review.vercel.app` pointe toujours vers `dpl_9LQqNzbj9RbN51cFLcajifxzq3dm` (SHA applicatif `a5d1c61`).

**Code de runner préparé (branche QA uniquement) :** `.github/workflows/d7-qa-hosted-auth-gate.yml`, `scripts/d7_qa_hosted_auth_gate.mjs`, `frontend/test/qa/d7_hosted_auth_gate.test.mjs`. Workflow manuel restreint à `refs/heads/qa/d7-c05-preview-a5d1c61-20261031` et à l'environnement protégé `d7-qa` ; origine QA immuable mise à jour et SHA de Preview épinglé. Contrôle synthétique avant réseau des adresses `example.invalid` ou `example.test`, A≠B, puis négatif Django et A→B→A. Contrôle préalable `git merge-base` contre `55fa500`. Correctif d'échappement regex fait avant clôture du patch. Diff GitHub `55fa500...cb116075` : **4 commits, exactement 3 fichiers** de runner/test/workflow ; aucun fichier Flutter, BFF, Vercel ou clinique changé par ces commits. Puis cette note documentaire sur la même branche.

**État des preuves :** sandbox réseau bloqué `iamina-d7-runner-20261101` (session `sbx_IeFJpQ1HClvaLHUSMiFF9GIra29o`, arrêtée) ; sur les deux fichiers réels du runner QA `node --check` PASS + `node --test frontend/test/qa/d7_hosted_auth_gate.test.mjs` **7/7 PASS, 0 FAIL, exit 0** (commande `cmd_e592e7a3c6fd4e85b8e1c4c39cde`) ; aucun secret réel envoyé ; exécution manuelle GitHub Action **NOT_RUN** ; secrets GitHub Environment `d7-qa` et approbation manuelle **UNKNOWN** ; vrai SSO + login A/B **NOT_RUN** ; C01–C05 / FR-AR / capture / reload / défaut réseau **NOT_RUN** ; certification clinique/privacy indépendante **PENDING**. Les 6/6 tests Node historiques du proxy sur `55fa500` restent une preuve séparée et ne valident pas le runner mis à jour.

**Next exact :** provisionner de façon sécurisée dans GitHub Environment `d7-qa` les secrets `D7_QA_A_EMAIL`, `D7_QA_A_PASSWORD`, `D7_QA_B_EMAIL`, `D7_QA_B_PASSWORD` et le Share Link de durée limitée `D7_QA_SSO_ACCESS` ; confirmer que l'environnement impose reviewer et branche QA ; lancer manuellement le workflow sur cette branche ; vérifier les logs/artefacts non sensibles puis réaliser Chrome FUE intégrée C01–C05 + F01–F08 sur FR/AR 390/768/1280, ISO A→B→A, retries/reload/offline. Toute défaillance bloque D7. Faire ensuite revue clinique/privacy indépendante et Perfection Pass. **Pas de merge/Prod/nouveau déploiement Vercel sans GO explicite.**


## 01/11/2026 — D7 F04 : reconstruction des preuves Chrome local

**Décision / Goal :** distinguer la preuve automatisée du changement type 2→type 1 et conservation des traitements, de la recette utilisateur iPhone déclarée « testée, résultat à confirmer ». Aucun nouveau test clinique ni authentifié n'est implicitement certifié.

**Preuve directe GitHub vérifiée le 01/11 :** le [run D7 Flutter Web #41210398830](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41210398830), associé au commit de test `fab1496f252f051efe1bb1724fa61883bc835818`, a son job `d7-real-web-fue` `completed/success`. Les logs réels montrent : `d7_profile_owner_save_widget_test.dart` PASS (1), `d7_web_type_transition_contract_test.dart` Chrome PASS (1), `d7_web_treatment_choice_responsive_test.dart` Chrome FR/EN/AR × 390/768/1280 PASS (9), puis les huit phases réelles du banc Chrome local, dont `patient_type1_without_automatic_treatment_change`, toutes exécutées. Artifact produit `d7-fue-actual-web-8phases-9png` (ID `13045104982`) ; les 9 captures sont destinées aux trois états type2, inconnu, aucun traitement, **pas à une capture spécifique type1**.

**Oracle du banc Chrome** : après sélection `Type 1 Diabetes` et sauvegarde, le script `scripts/d7_web_actual_profile_e2e.py` appelle `reload_and_unlock()`, puis exige explicitement que le résumé de la section médicale contienne `Type 1 Diabetes`, `Oral medicines` et `Insulin`. Il s'agit de la **vraie application Flutter Web construite en local**, mais avec authentificateur WebAuthn synthétique, sans backend Preview ni connexion Django A/B.

**Parité source vérifiée** : les blobs GitHub de ces fichiers sont identiques entre `fab1496f` testé et `55fa500f56d86d7fa014b5b1849d7e7cdad3ea59` déployé en Preview : `frontend/lib/features/profile/profile_screen.dart`, `frontend/lib/features/profile/medical_treatment_declaration_v1.dart`, `frontend/lib/features/profile/medical_treatment_multi_selector.dart`, `frontend/lib/data/drift/patient_treatment_declaration_store.dart`, les trois tests Flutter profil cités et `scripts/d7_web_actual_profile_e2e.py` (8/8 comparés). D'autres chemins auth/API ont évolué : l'égalité de ces blobs n'est **pas** une preuve E2E exacte du déploiement complet ni de la session utilisateur.

**Message orange iPhone** : source `profile_screen.dart` indique sauvegarde Drift locale et `syncLocalOnly` quand `canSyncClinicalData` est faux ; `ApiClient` maintient le transport clinique désactivé par défaut. Message cohérent ; **pas** une preuve de synchronisation serveur. La capture fournie ne montre pas le formulaire Type 1/traitements après rechargement.

**État binaire honnête** : `F04_SYNTHETIC_LOCAL_CHROME=PASS` (reconstruction code + job/logs) ; `F04_HOSTED_USER_IPHONE_AFTER_RELOAD=EVIDENCE_PENDING` ; `F04_HOSTED_AUTH_A_B=NOT_VERIFIED` ; `D7_GLOBAL_CERTIFIED=NO`. La déclaration manuelle des 7 scénarios reste « exécutés selon utilisateur, verdicts non communiqués » et ne peut pas être convertie en 7 PASS. Aucun changement Flutter/API, déploiement Vercel, migration ou fusion.

**Next exact** : confronter le résultat manuel iPhone après hard reload et garder une capture anonymisée de « Profil > Suivi médical » Type 1 + traitements ; ensuite exécuter les scénarios hébergés A/B, C01–C05, FR/AR et la revue indépendante clinique/privacy. Ne pas rouvrir le correctif F04 sans défaut démontré.


## 01/11/2026 — D7 F04 : validation manuelle explicite propriétaire

**Validation utilisateur explicite :** à la question « après avoir rechargé complètement la page, as-tu retrouvé Type 1 avec Médicaments oraux et Insuline toujours sélectionnés ? », le propriétaire répond « Oui ils le sont ! Je valide ». Il confirme donc **la persistance observée sur son iPhone après rechargement** des trois sélections, sur la Preview utilisée lors de sa recette manuelle D7.

**Verdict borné :** `F04_USER_IPHONE_RELOAD=PASS_MANUAL_OWNER_ATTESTED` (validation humaine déclarative et explicite) et `F04_SYNTHETIC_LOCAL_CHROME=PASS` (run CI #41210398830 déjà vérifié). **Ce n'est ni une capture de l'état post-reload, ni une preuve API/BDD de synchronisation distante ni une preuve cryptographique de l'identité A/B.** La capture antérieure confirme seulement le message « Pilote local · enregistré sur cet appareil, non synchronisé ». Ne pas extrapoler à tous les cas F01–F08/C01–C05.

**Décision :** clore uniquement le **sous-test manuel F04 changement type 2→type 1 / traitements conservés après rechargement** avec cette preuve de validation propriétaire. `D7_GLOBAL_CERTIFIED=NO` ; `HOSTED_AUTHENTICATED_A_B=NOT_VERIFIED` ; retrait/consentement/récupération réseau/FR-AR RTL et revue indépendante clinique/privacy toujours à certifier.

**Next exact :** recouper les résultats des six autres scénarios manuels et la preuve A→B→A authentifiée ; obtenir captures anonymisées en FR/AR aux viewports 390/768/1280, essais C01–C05 refus/retrait/retry et revue clinique/privacy indépendante. Aucun nouveau déploiement, merge ni modification de production demandé par cette validation.


## 01/11/2026 — D7 : validation propriétaire des sept scénarios manuels, prochain gate

**Décision / objectif :** enregistrer fidèlement la nouvelle déclaration propriétaire « Tout ça est confirmé ! Next » en réponse à la matrice de sept parcours manuels D7. Cette validation humaine explicite s'étend aux sept lignes de la checklist utilisateur (connexion A, modifications du profil, incertitude/aucun traitement, consentement + verrou, retrait, isolation A→B→A, FR/AR + affichage), **sans fabriquer de logs, captures manquantes ou verdict API**.

**Verdict manuel :** `MANUAL_OWNER_ATTESTED_7_OF_7=YES`. Pour F04 type 2→type 1, confirmation détaillée antérieure de la persistance après hard reload iPhone avec traitements oraux + insuline. Pour les six autres items, **PASS_MANUAL_OWNER_ATTESTED (déclaratif)** uniquement, sans états observés détaillés ni captures comparables communiquées. En particulier, l'affirmation générale ne prouve pas automatiquement les sous-états C04 négatifs (API erreur / offline / retry) ni une vraie session serveur A→B→A prouvée par logs.

**Preuves indépendantes préexistantes recontrôlées :** [Chrome local FUE #41210398830](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41210398830) SUCCESS à son SHA ; huit phases incluant hard reload, traitement conservé, neuf captures synthétiques. Runner QA contract 7/7 Node PASS en sandbox isolée sur fichiers exacts ; aucun exécution manuelle hébergée avec secrets QA prouvée. Vercel frontend Preview `dpl_9uEbft6CgxjtkEBjtvG6tiFjeZP8` READY sur commit `55fa500`, Production alias `iamina-review.vercel.app` toujours `dpl_9LQqNzbj9RbN51cFLcajifxzq3dm` au contrôle du 01/11.

**Revue statique interne (non indépendante) :** sur source `55fa500`, `ConsentEvidenceStore.forPatientVault` isole l'évidence et le marqueur de retrait par coffre ; `withdrawD7AiConsent` bloque le consentement local avant requête, maintient le pending si serveur non confirmé et ne retire le pending qu'après nettoyage local ; `ApiClient.withdrawConsent` exige un statut 2xx avec `ai_consent_given=false` + notice effacée ; backend `account.py` révoque consentement global et grants dérivés transactionnellement. Ces invariants sont **supportés par le code et des tests synthétiques**, mais **pas par une revue clinique/privacy indépendante ni des traces d'exécution SSO**.

**Risque à tester, non déclaré défaut :** bascule de session A→B pendant un `await` de consentement/retrait. Le host de coffres utilise `authEpoch` et des vérifications generation/scope, mais les callbacks `ConsentScreen._accept` et `ProfileScreen._confirmWithdrawConsent` ne vérifient pas explicitement l'epoch courant à chaque reprise asynchrone ; le flux complet auth/token/stockage/réponse doit être soumis à un test de concurrence ciblé. Ne pas déduire une fuite démontrée sans ce test.

**Statuts strictement séparés :** `D7_MANUAL_OWNER_CHECKLIST=ACCEPTED_7_OF_7`, `D7_HOSTED_AUTH_AUTOMATED_C01_C05=NOT_VERIFIED`, `D7_INDEPENDENT_CLINICAL_PRIVACY_SIGNOFF=PENDING`, `D7_GLOBAL_VERIFIED=NO`. `QUALITY_SCORING_POLICY` interdit le score final et la mention VERIFIED avant toutes les preuves/gates et un Perfection Pass ; aucun score final inventé.

**Next exact :** conserver le GO manuel du propriétaire ; achever le test automatisé protégé A→B→A + C01–C05 sur Preview `55fa500` avec GitHub Environment `d7-qa` et secrets non divulgués ; tester l'interleaving de session pendant le retrait/consentement ; obtenir l'avis indépendant clinique/privacy ; Perfection Pass et closeout D7. En parallèle autorisé, **préparer D22 par revue documentaire sans changer les cibles médicales**. D22 ne peut être implémentée/clôturée avant arbitrages D19 G1–G7. **Aucun merge / nouveau Vercel / migration / Production sans nouveau GO explicite.**
