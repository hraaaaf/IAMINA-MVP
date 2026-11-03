# IAMINA — D22 Web : acceptation technique bornée, transfert scientifique à D32

**Décision explicite du propriétaire, 03/11/2026 :** retirer de D22 les arbitrages scientifiques/cliniques G1–G7 et les transférer à [D32 #1248](https://github.com/hraaaaf/IAMINA-MVP/issues/1248). **État D22 : TECHNICALLY_ACCEPTED / UNMERGED / NOT_DEPLOYED.** Il s'agit de l'acceptation des comportements Web démontrés par tests synthétiques au SHA exact, **pas** de l'approbation d'une politique de soin, d'une migration, d'un export médical ni d'une mise en service patient.

## Nom, goal, succès, preuve

**Nom :** D22 — unités d'affichage et confinement des objectifs glycémiques non vérifiés (Web uniquement).

**Goal borné :** permettre de sélectionner l'unité d'affichage mg/dL ou mmol/L ; persister cette préférence après reload ; traiter les objectifs historiques/provenance inconnue en **« non vérifiés »**, sans classification ni modification silencieuse ; préserver la glycémie brute lors d'une édition non glycémique ; observer que les comptes locaux fictifs A et B ne mélangent pas leurs mesures ; maintenir les interfaces FR/AR réactives dans les scénarios testés.

**Succès vérifié :** 86/86 workflows GitHub `completed/success` sur les six PR de code/QA ci-dessous, et 1/1 sur la PR documentaire antérieure #1247 lors du contrôle du 03/11/2026. Les scénarios Chrome utiles sont détaillés ; leur portée ne vaut pas validation des fonctionnalités non testées.

| Sous-lot | HEAD exact | CI et preuve | Verdict borné |
| --- | --- | --- | --- |
| Gate A Web fail-closed [#1225](https://github.com/hraaaaf/IAMINA-MVP/pull/1225) | `8e7a081a252848f10b785c2b2729b189c217a659` | **18/18 SUCCESS** ; masque les objectifs non autorisés sur surfaces prioritaires | TECHNICAL PASS |
| F01/F03/F07 QA Chrome [#1231](https://github.com/hraaaaf/IAMINA-MVP/pull/1231) | `36aab03329ad969fd441bb9cbcab542204368233` | **20/20 SUCCESS** ; Chrome EN/FR/AR, unités après reload, legacy « non vérifié », vues 390/768/1280 et clavier FR/AR | PASS_BOUNDED |
| F04 intégrité brute [#1238](https://github.com/hraaaaf/IAMINA-MVP/pull/1238) | `a69e91eee10e925d3e83046f2e8a8834ffb6cd6f` | **7/7 SUCCESS** ; tests Flutter/SQLite et Chrome Web IndexedDB synthétiques. Valeur brute 103.25 inchangée lors de l'édition du contexte aux 390/1280. 4 captures SHA256 vérifiées | PASS_BOUNDED |
| F05 rapport descriptif [#1240](https://github.com/hraaaaf/IAMINA-MVP/pull/1240) | `a3c75f116d25ba3c75457b4007ae74a5d796d41c` | **19/19 SUCCESS** ; [Chrome #41659326395](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41659326395), 4/4 FR/AR 390/1280, 4 PNG SHA256, 22 requêtes de polices externes refusées ; pas de classification legacy 70/180 | PASS_BOUNDED |
| F06 coffre local A/B [#1241](https://github.com/hraaaaf/IAMINA-MVP/pull/1241) | `b04ea588f3b1ac68c3f0f8ed591c92248a4e7068` | **2/2 SUCCESS** ; navigateur Chrome, vrai contrôleur Drift/IndexedDB mais principaux simulés A/B ; A=103.25, B=222.5, logout et reload | PASS_BOUNDED |
| F07 texte FR/AR 200 % [#1242](https://github.com/hraaaaf/IAMINA-MVP/pull/1242) | `aa7c64abced94fce18b0729f44e0bfb8cd5d0f88` | **20/20 SUCCESS** ; six tests Flutter `TextScaler.linear(2.0)` FR/AR × 390/768/1280, RTL et rendu sans exception | PASS_BOUNDED |

**Important : toutes les PR de cette table restent DRAFT et NON FUSIONNÉES au dernier relevé.** `main` ne contient donc pas encore nécessairement ces correctifs ; l'état ici est une **acceptation de candidat**, pas une livraison réelle. Ne pas fusionner automatiquement les PR superposées (#1240 est basée sur le travail de #1225 ; #1242 dépend du travail de #1231). Aucune autorisation de déploiement Vercel découle de cette acceptation.

## Ce qui est TRANSFÉRÉ et retiré du périmètre de clôture D22

**[D32 — recherche, arbitrage et certification clinique/sécurité #1248](https://github.com/hraaaaf/IAMINA-MVP/issues/1248)** prend exclusivement en charge :

- Anciennes dénominations **G1–G7** : provenance et unité de source, autorité de cibles patient, legacy, facteur/arrondi, CGM/TIR vs manuels, accessibilité/UX complète, isolation/sécurité/migration et rollback.
- **F02 positif** : cibles explicitement autorisées, conversion et persistance de quantité sans perte avec facteur/version définis.
- Restes **F05** : exports PDF/CSV, API/KPI producteurs, vraies données CGM, GMI/AGP/TIR à source traçable.
- Restes **F06** : identité et authentification réelles, API distante, consentement et séparation physique après reconnect.
- Restes **F07** : zoom **natif** Chrome 200 %, lecteur d'écran, validation indépendante de l'arabe, BEFORE/AFTER mêmes viewports.
- Migration Drift additive/versionnée, restauration réelle, audit, sécurité, approbation clinique et décision distincte de mise en service.

**Ces points ne sont PAS réputés validés**, même si D22 est techniquement acceptée sur son scope borné. Le module de modèles G1/G4/G7 [#1221](https://github.com/hraaaaf/IAMINA-MVP/pull/1221) et le banc de migration synthétique [#1222](https://github.com/hraaaaf/IAMINA-MVP/pull/1222), déjà fusionnés sans intégration clinique, constituent des PREUVES d'ingénierie réutilisables pour D32, pas une permission de prescrire.

## Conclusion de D22 et chemin opérationnel

**Décision : D22 `TECHNICALLY_ACCEPTED / SCOPED_CLOSED / UNMERGED / NOT_DEPLOYED`.** Aucun chiffre d'avancement global n'est inventé. Aucun nouveau test d'un lot vert n'est requis par le simple changement de périmètre. La protection « objectifs non vérifiés » doit rester fail-closed ; elle n'est pas contournée pour accélérer D32.

**Next exact de la phase livraison, séparé de la décision D22 :** conserver les six PR candidates jusqu'à un plan d'intégration non contradictoire/autorisé et une CI postmerge réelle. Si un merge déclenche un déploiement Vercel automatique, **obtenir une autorisation explicite AVANT** ; ne jamais annoncer « livré » ou « production-ready » à l'avance.

**Next décision de recherche :** D32 [#1248](https://github.com/hraaaaf/IAMINA-MVP/issues/1248), recherche scientifique documentée et tests réels avant politique clinique ; aucun GO patient implicite.

**Origines historiques (conservées, mais supersédées pour l'allocation de périmètre) :** `docs/assessments/2026-10-29-d19-d22-web-clinical-decision-gate.md`, `2026-11-02-d22-g1-g4-g7-evidence-contract-gate.md`, `2026-11-02-d22-g7-synthetic-migration-rehearsal.md`.
