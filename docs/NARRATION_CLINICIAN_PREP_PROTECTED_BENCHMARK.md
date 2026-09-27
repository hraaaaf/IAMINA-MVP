# IAMINA — CLINICIAN_PREP Protected Wrapper Benchmark

Base certifiée : `main@6fce50a58a13c5a4059223c24926cb99fe833a89`.

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
