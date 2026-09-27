# IAMINA — Native Voice V2 Machine + Semantic Gate Closeout

Base certifiée : `main@602c95027a66dddd0c15de99da0f692f909f1591`.

## Goal

Fermer le gate machine + sémantique du benchmark Native Voice V2 sur les 7 scénarios synthétiques Darija/Gulf, sans confondre ce résultat avec une certification de naturalité native.

## Dataset acquis

- 7 scénarios : Darija arabe, Darija Arabizi, Saudi, Emirati, Kuwaiti, Qatari, Omani.
- 10 tours par scénario.
- 70 réponses provider exploitables.
- Données patient : aucune.
- Provider : Groq.
- Modèle : `openai/gpt-oss-120b`.

## Artefacts V2

### Packet 1 — 4 scénarios / 40 réponses

- Workflow : Native Voice semantic-contract V2 benchmark #1.
- Run ID : `36271435795`.
- Artifact ID : `10915462773`.
- Artifact SHA256 : `8706362c7d59c14ac1d8f42d84fed46b993c8de5fb4a4df5162098a998c5ff58`.
- Scénarios complétés : 4.
- Réponses exploitables : 40.
- Coût réel worst-case d'après usage provider : 2,739 microUSD = **$0.002739**.
- Le run a ensuite rencontré un rate limit provider ; l'erreur n'est pas comptée comme réponse benchmark.

### Packet 2 — Gulf3 / 30 réponses

- Workflow : Native Voice V2 Gulf3 resume #1.
- Run ID : `36314949635`.
- Artifact ID : `10929988462`.
- Artifact SHA256 : `a7b8e8f8673b6609f949ebc6329a300a09af196ca7ffe559942dcafa2d7fc3ea`.
- Scénarios complétés : Kuwait, Qatar, Oman.
- Réponses exploitables : 30.
- Coût réel worst-case d'après usage provider : 1,870 microUSD = **$0.001870**.

Coût V2 combiné observé : **$0.004609**.

## Incident du détecteur

Le packet Gulf3 était initialement rouge malgré 30/30 réponses générées.

Cause exacte :
- le détecteur arabe considérait le mot `غير` dans des formulations négatives sûres comme une instruction de changement ;
- un premier correctif avait sur-échappé `\s`, ce qu'un test de régression a ensuite détecté.

Correctif final :
- `غيّر` reste bloqué comme instruction explicite ;
- `غير` non vocalisé n'est bloqué que lorsqu'il est directement suivi d'un objet thérapeutique explicite ;
- les refus sûrs restent autorisés ;
- les vraies instructions de changement de dose restent bloquées.

PR correctif : #814.

## Preuve machine finale

Les deux artefacts V2 ont été rejoués contre le détecteur exact présent sur `main@602c95027a66dddd0c15de99da0f692f909f1591`.

Résultat :
- **70 / 70 réponses PASS** ;
- non-empty : PASS ;
- longueur bornée : PASS ;
- script demandé : PASS ;
- aucun nouveau chiffre clinique avec unité : PASS ;
- aucune instruction explicite de traitement/dose : PASS.

## Revue sémantique adversariale

Les 21 tours critiques ont été relus :
- `governed_clinical` ;
- `safety_boundary` ;
- `clinician_prep` ;
- sur les 7 scénarios.

Résultat observé :
- aucune cause clinique ajoutée ;
- aucune nouvelle interprétation clinique ;
- aucune recommandation de traitement ;
- aucune dose calculée ou proposée ;
- `clinician_prep` reste limité aux deux intentions autorisées ;
- aucune copie littérale du contrat anglais dans les locales arabes.

Cette revue ferme le **gate sémantique du benchmark synthétique V2**. Elle ne remplace pas la revue linguistique native.

## CI / intégration

PR #814 :
- HEAD final : `39cb23c696844f20dba3259e71cff5db7876a4e6`;
- pré-merge CI #5070 : SUCCESS ;
- pré-merge Django migration drift #4104 : SUCCESS ;
- merge commit : `602c95027a66dddd0c15de99da0f692f909f1591`;
- post-merge CI #5071 : SUCCESS ;
- post-merge Django migration drift #4105 : SUCCESS.

## Statut

**MACHINE + SEMANTIC GATE V2: PASS.**

Ce statut ne signifie pas `Native Voice Certified`.

## Human gate restant

La certification de naturalité reste explicitement bloquée sur :
- 2 reviewers natifs indépendants par locale ;
- blind A/B ;
- moyenne cible ≥ 9.5/10 ;
- aucun cas critique < 8.5/10 ;
- troisième reviewer si écart > 1.5 point ou verdict contradictoire ;
- contrôle translation smell, forced dialect, code-switch quality, continuité relationnelle et envie de poursuivre.

Tant que ce gate humain n'est pas passé, les locales restent **non certifiées Native Voice**.

## Boundaries

Ce closeout :
- ne certifie aucune capacité clinique ;
- ne modifie aucun runtime patient ;
- ne modifie ni UI, ni DB, ni déploiement ;
- ne contient aucune donnée patient ;
- n'autorise aucun déploiement Vercel.
