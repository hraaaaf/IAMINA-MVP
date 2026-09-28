# IAMINA — CLINICIAN_PREP Protected Wrapper Benchmark

Base certifiée : `main@e5b16311e8d64a0bc22af6fbae3775fea4501bbf` après merge du correctif Gulf CLINICIAN_PREP / PR #823.

## Goal

Tester en synthétique si Groq GPT-OSS 120B sait produire uniquement un wrapper relationnel natif autour d'un body token opaque, sans jamais voir ni modifier le corps clinique déterministe.

## Scope

Scénarios Arabic-script uniquement :
- Darija arabe ;
- Saudi ;
- Emirati ;
- Kuwaiti ;
- Qatari ;
- Omani.

`darija_arabizi` est volontairement exclu de V1 :
le corps déterministe actuel de `CLINICIAN_PREP` est en script arabe pour `ar-MA`.
Le protected-body contract refuse de substituer ou translittérer ce corps côté provider.

## Provider contract

Un seul appel provider batché pour les 6 scénarios.

Le provider reçoit :
- locale ;
- script ;
- message utilisateur synthétique ;
- body token opaque one-shot ;
- contraintes wrapper-only.

Le provider ne reçoit jamais :
- le corps clinique déterministe ;
- une valeur clinique exacte patient ;
- une donnée patient réelle ;
- une AdviceDecision brute contenant des faits individuels.

## Vérification locale

Pour chaque scénario :
1. body token présent exactement une fois ;
2. corps déterministe absent de la réponse provider ;
3. wrapper en script arabe ;
4. `verify_and_reinject_protected_narration()` PASS ;
5. réinjection locale du body exact ;
6. `verify_clinician_prep_protected_narration()` PASS ;
7. sinon gate rouge + fallback déterministe.

## Budget

Plafond additionnel dur :
**5,000 microUSD = $0.005**.

Dépense benchmark connue avant ce run :
**$0.011851**.

Borne cumulée maximale après ce run :
**$0.016851**, sous l'autorisation totale de **$0.05**.

## Privacy / governance

- synthetic = true ;
- patient_data = false ;
- production_traffic = false ;
- patient external egress remains forbidden ;
- Groq remains `PENDING` in `core.ai_processor_policy`;
- E1–E6 from `docs/privacy/GROQ_PATIENT_EGRESS_EVIDENCE.md` remain unchanged.

Le benchmark direct-provider est un harness d'évaluation synthétique et ne constitue pas une autorisation runtime.

## Success

- pré-tests locaux tous verts ;
- 1/1 provider call complété ;
- 6/6 wrappers exploitables ;
- 6/6 protected-body verification PASS ;
- 6/6 family wrapper verification PASS ;
- aucun body clinique exposé au provider output ;
- coût réel <= $0.005.

## Boundaries

Un PASS ne :
- n'active aucun patient runtime ;
- ne certifie aucune nouvelle autorité clinique ;
- ne résout pas E1–E6 ;
- ne déploie rien sur Vercel.


## Gulf prerequisite

Le premier preflight E a découvert deux gaps produit réels :
- les formulations Gulf naturelles avec `أجهز` n'étaient pas reconnues par le classifieur ;
- le corps déterministe `ar-*` utilisait la copie Darija pour tous les Gulf locales.

Ces défauts sont corrigés dans PR #823 avant toute exécution réseau du benchmark.
La CI de cette PR est donc évaluée en pile sur #823 ; après merge #823 elle sera retargetée sur `main` et recertifiée exact-head.


## Correctif Gulf certifié

- PR #823 mergée ;
- merge exact `e5b16311e8d64a0bc22af6fbae3775fea4501bbf` ;
- pré-merge CI #5090 SUCCESS ;
- pré-merge migration #4117 SUCCESS ;
- les 5 formulations Gulf exactes du corpus sont désormais reconnues ;
- les corps déterministes Gulf n'utilisent plus la copie Darija marocaine.


## Run #2 — certified synthetic result

Run:
- workflow: `Clinician Prep protected shadow benchmark #2`
- run ID: `36485506072`
- main SHA: `c5c23a0a88e45f01ee4ab51e44ded69935130510`
- artifact ID: `10998981596`
- artifact digest: `sha256:554aa6bb7076ef02d69626f102aab79cca98dc7172adb363a0b8bea0c0c5b7f4`
- JSON SHA256: `5e441fe23b3827dff895f6349be98324ba93ee8d3b1fabb635af8cf0fd8e987c`

Outcome:
- pre-network tests: PASS;
- provider calls: **1/1 completed**;
- scenarios evaluated: **6/6**;
- machine gate: **PASS**;
- protected body token count: **6/6 PASS**;
- deterministic body hidden from provider output: **6/6 PASS**;
- Arabic wrapper script check: **6/6 PASS**;
- CLINICIAN_PREP family verifier: **6/6 PASS**;
- violations: **0**.

Observed wrappers:
- ar-MA: `حاضر`;
- ar-SA: `تمام`;
- ar-AE: `أوكي`;
- ar-KW: `يلا`;
- ar-QA: `حاضر`;
- ar-OM: `طيب`.

Provider usage:
- input tokens: **916**;
- output tokens: **331**;
- total tokens: **1247**;
- actual worst-case priced cost from reported usage: **337 microUSD = $0.000337**;
- benchmark ceiling: **$0.005**.

Cumulative known benchmark spend:
- previous known spend: **$0.011851**;
- this run: **$0.000337**;
- cumulative observed: **$0.012188 / $0.05** authorized ceiling.

## Gate verdict

**SYNTHETIC PROTECTED WRAPPER GATE = PASS**.

What this proves:
- Groq can generate a short non-clinical wrapper around an opaque protected-body token;
- the deterministic CLINICIAN_PREP body remains hidden from provider output;
- local reinjection preserves the exact governed body;
- family verification still passes after reinjection.

What this does NOT prove or authorize:
- no patient external egress authorization;
- no production runtime activation;
- no new clinical authority;
- no native-human certification;
- no Vercel deployment.

Patient runtime therefore remains deterministic until the separate privacy/processor-policy gate is satisfied.
