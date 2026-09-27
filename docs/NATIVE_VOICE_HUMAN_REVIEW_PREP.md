# IAMINA — Native Voice Human Review Preparation

Base : `main@dde986b218a4d91b4509fd1040d964f8a9cf7307`.

## Goal

Préparer un vrai packet blind A/B complet pour la double revue native obligatoire du benchmark Native Voice V2, sans inventer de référence native ni de score humain.

## Succès

- 70 paires V1↔V2 exactes ;
- mêmes scenario_id, turn_id, locale, script, synthetic_user et semantic_goal pour chaque paire ;
- 2 randomisations A/B indépendantes ;
- 6 groupes locale : ar-MA, ar-SA, ar-AE, ar-KW, ar-QA, ar-OM ;
- ar-MA contient Darija Arabic + Arabizi, soit 20 cas par reviewer ;
- autres locales : 10 cas par reviewer ;
- mapping V1/V2 séparé du packet reviewers ;
- rubric 10 dimensions + hard rejects + flags translation smell / forced dialect / would continue ;
- aucun score humain prérempli ;
- aucun verdict Native Voice prérempli.

## Baseline V1 Qatar/Oman

Workflow : `Native Voice V1 Qatar Oman baseline #1`.
Run ID : `36332545339`.

Le job global est rouge parce que l'ancien détecteur V1 signale des sorties qui ne passent pas ses anciens machine checks.

Preuve utile pour le blind A/B :
- tests pré-network : 8/8 PASS ;
- completed_calls : 2 ;
- completed_scenarios : 2 ;
- evaluated_rows : 20 ;
- Qatar : 10 réponses ;
- Oman : 10 réponses ;
- artifact ID : `10936590768`;
- artifact ZIP SHA256 : `0bb54f483a600c94908a56c2b9bdf7321ddc9bf97fb61dfdc64dcd0393b7d415`;
- coût observé : 1,110 microUSD = **$0.001110**.

Ces sorties sont utilisées uniquement comme **baseline précédente aveugle**, pas comme candidat de certification.

## Sources du packet

V1 :
- artifact `10914549322` : 50 réponses ;
- artifact `10936590768` : 20 réponses.

V2 candidat :
- artifact `10915462773` : 40 réponses ;
- artifact `10929988462` : 30 réponses.

Contrôle d'alignement :
- V1 replies = 70 ;
- V2 replies = 70 ;
- clé de paire = `scenario_id + turn_id` ;
- set de clés identique ;
- mismatch metadata/prompt/semantic_goal = **0**.

## Bundles générés

### Reviewer bundle — partage autorisé

`IAMINA_NATIVE_VOICE_REVIEWER_PACKETS.zip`

SHA256 :
`25b0c9186322b3ea59bafb0a623e44f272ad19a205ffb68e01232db1e87e8722`

Contenu :
- instructions ;
- public manifest ;
- reviewer_1 : 6 CSV locale ;
- reviewer_2 : 6 CSV locale.

Aucune clé V1/V2 dans ce bundle.

### Owner bundle — NE PAS PARTAGER

`IAMINA_NATIVE_VOICE_OWNER_KEY_DO_NOT_SHARE.zip`

SHA256 :
`b702ddf042f74b8485522dc3be9159bf48911349aec0d6205902de3a38ade962`

Contenu :
- answer key ;
- randomization seeds ;
- source manifest ;
- file hashes ;
- agrégateur de scores.

Partager ce bundle à un reviewer invalide le blind A/B.

## Randomisation

Reviewer 1 et Reviewer 2 ont une randomisation indépendante.

Le mapping n'est pas enregistré dans le repo ni dans cette documentation.

## Gate final

Par locale :
- 2 reviewers natifs indépendants ;
- blind A/B ;
- score moyen cible ≥ 9.5/10 ;
- aucun cas critique < 8.5/10 ;
- aucun hard reject candidat ;
- reviewer 3 si écart > 1.5 point ou verdict contradictoire ;
- absence de translation smell récurrent ;
- absence de forced dialect récurrent ;
- continuité multi-turn validée.

L'agrégateur owner calcule les gates numériques et les alertes, mais **ne peut jamais déclarer automatiquement Native Voice Certified**.

## Budget observé

Dépense benchmark connue cumulée après Qatar/Oman V1 :
**11,851 microUSD = $0.011851**.

Plafond autorisé :
**$0.05**.

## Statut

**HUMAN REVIEW PACKET READY.**

Le seul gate restant est l'exécution réelle des revues natives indépendantes.

Aucun runtime patient, UI, DB ou déploiement Vercel n'a été modifié.
