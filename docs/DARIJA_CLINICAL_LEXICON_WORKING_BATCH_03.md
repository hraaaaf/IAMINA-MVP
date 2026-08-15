# Darija Clinical Lexicon — Working Native Review Batch 03

Status: **WORKING / NON-RUNTIME / NOT CLINICALLY CERTIFIED**

Date: 2026-08-15
Locale target: Moroccan Darija / Arabizi (`ar-MA`)
Source: interactive native-speaker review session.

## Governance boundary

This document records native-language candidates accepted during an interactive review session. It is **not** a clinical approval, safety-corpus approval, release certification, or authorization to add these phrases to runtime triage/classification logic.

Before any runtime use, each candidate requires the applicable clinical-safety review, positive/negative/contextual tests, false-positive analysis, and the existing fail-closed release gates.

Naturalness acceptance below is linguistic only. It does not assign medical severity or authorize diagnosis, treatment advice, dose calculation, treatment optimization, or automated clinical action.

## Batch 03

### 41 — Low glucose / hypoglycemia in Arabizi
Accepted:
- `hbat lia sokkar bzaf`
- `sokkar habet lia`
- `3ndi hypo`

Not retained:
- `hbat lia glucose`

### 42 — High glucose / hyperglycemia in Arabizi
Accepted:
- `tla3 lia sokkar bzaf`
- `sokkar tale3 lia`
- `3ndi hyper`

Not retained:
- `tla3 lia glucose`

### 43 — Loss of consciousness
Accepted:
- `f9dt lwa3y`
- `ma b9itch wa3i`
- `t7t o ma 7ssit b walo`

Not retained:
- `ghma 3lia`

### 44 — Hyperbolic death language with cold
Accepted as natural hyperbolic formulations requiring contextual interpretation:
- `fia lmout dial lberd`
- `mout b lberd`
- `ghadi nmout mn lberd`
- `ana miet b lberd`

Safety boundary:
- tokens such as `lmout`, `mout`, `nmout`, and `miet` must not alone imply actual death, suicidality, or a life-threatening event.

### 45 — Chest pain / pressure in Arabizi
Accepted:
- `sdri kaydrni`
- `7ass b daght f sdri`
- `7ass b sdri mdi9 3lia`

Not retained:
- `sdri mkhno9`

### 46 — Dyspnea / choking sensation
Accepted:
- `ma 9adrch ntnaffes mzyan`
- `kan7ess brassi mkhno9`

Not retained:
- `nafass 9sir`
- `ma dakhlich lia lhwa`

### 47 — Vomiting / nausea wording
Accepted:
- `kanrdd bzaf`
- `t9yit bzaf`
- `rddit bzaf`
- `fia rda`

Semantic boundary:
- `fia rda` may describe nausea/retching rather than confirmed vomiting; runtime logic must not collapse these meanings without context.

### 48 — CGM / sensor vocabulary
Accepted:
- `3ndi capteur dial sokkar`
- `capteur dial sokkar ma khdamch`
- `3ndi cgm`
- `sensor dial sokkar ma khdamch`

### 49 — Motor deficit
Accepted:
- `ma b9itch 9ader n7rek ydi`
- `ma b9itch 9ader n7rek rjli`
- `ydi ma b9atch kat7rek mzyan`
- `rjli ma b9atch kat7rek mzyan`

### 50 — Facial asymmetry / facial sensory change
Accepted:
- `fmi t3wej lia`
- `wjhi t3wej lia`
- `nos wjhi ma b9itch kan7ess bih`

Not retained:
- `wjhi mayel ljiha wa7da`

Semantic boundary:
- facial asymmetry and reduced facial sensation are distinct findings and must remain separable.

### 51 — Confusion / disorientation
Accepted:
- `ma b9itch 3aref fin ana`
- `ma 3reft fin rani`
- `t5let lia kolchi`

Not retained:
- `7ass brassi daye3`

### 52 — Speech disturbance
Accepted:
- `ma b9itch kan9der nhder mzyan`
- `lhdra t5letat lia`
- `lsani t9el 3lia`
- `klami ma b9ach bayn`

### 53 — Loss of vision
Accepted:
- `ma b9itch kanchof`
- `mcha lia chof`
- `ma b9it kanchof walo`
- `3mit`

Native correction:
- for the third reviewed formulation use `ma b9it`, not `ma b9itch`.

### 54 — Severe sudden headache
Accepted:
- `chedni 7ri9 mjhed`
- `rassi kaydrni bzaf w bda 3la ghfla`
- `jani 7ri9 rrass mjhed 3la ghefla`

Not retained:
- `rassi tfre9e3 mn l wje3`

Native correction:
- the reviewed severe-pain wording uses `7ri9 ... mjhed`; sudden onset remains expressed with `3la ghfla` / `3la ghefla` in the accepted candidates.

### 55 — Hyperbolic emotional/laughter language
Accepted:
- `ghadi nmout b de7k`
- `hadchi kay9tel bdda7k`

Not retained:
- `moutni b de7k`
- `ana miet b de7k`

Safety boundary:
- `nmout` and `kay9tel` are potentially figurative here and must not alone imply death, self-harm, or emergency intent.

### 56 — Hyperbolic hunger language
Accepted:
- `ghadi nmout b jou3`
- `miet b jou3`
- `kay9telni jou3`
- `fya lmout dial jou3`

Safety boundary:
- lethal vocabulary is potentially hyperbolic; token presence alone is insufficient for emergency or self-harm classification.

### 57 — Hyperbolic fatigue language
Accepted:
- `ghadi nmout b l3ya`
- `miet b l3ya`
- `kay9telni l3ya`
- `fya lmout dial l3ya`

### 58 — Hyperbolic heat language
Accepted:
- `ghadi nmout b ssehd`
- `miet b ssehd`
- `kay9telni ssehd`
- `fya lmout dial ssehd`

Native lexical correction:
- use `ssehd` for ambient heat in this context, not `skhana`.
- preserve the distinction between ambient heat (`ssehd`) and fever/being febrile (`skhana`) established by the native review.

### 59 — Figurative “this is killing me” language
Accepted:
- `hadchi kay9telni`
- `hadchi ghadi y9telni`
- `hadchi mredni`
- `hadchi hlekni`

Safety boundary:
- these expressions can be figurative. Context is mandatory before any literal danger interpretation.

### 60 — “I cannot take it anymore” wording
Accepted:
- `ma b9itch 9ader`
- `ma b9a fia ma ndir`
- `safi ma b9itch 9ader`

Not retained:
- `t3yit`

Safety boundary:
- these phrases may express exhaustion or frustration and must not automatically be mapped to suicidality or immediate danger without contextual evidence.

### 61 — CGM LOW reading / alarm
Accepted:
- `capteur 3tani low`
- `cgm 3tani low`
- `capteur kaygol lia low`
- `sensor kaygol lia low`

### 62 — CGM HIGH reading / alarm
Accepted:
- `capteur 3tani high`
- `cgm 3tani high`
- `capteur kaygol lia high`
- `sensor kaygol lia high`

Safety boundary for 61–62:
- these describe a device reading/alarm. They do not by themselves prove a biologically confirmed glucose value.

### 63 — CGM reading discordant with symptoms
Accepted:
- `capteur kaygol low walakin ana mzyan`
- `cgm kaygol high walakin ma 7ass b walo`
- `capteur kay3tini ra9m ma kaytla9ach m3a li kan7ess bih`
- `sensor kaygol haja w ana 7ass b haja khra`

Safety boundary:
- preserve device reading and patient-reported symptoms as distinct evidence when they conflict.

### 64 — CGM / sensor failure wording
Accepted:
- `capteur ma khdamch`
- `cgm ma khdamch`
- `sensor ma kay9rach`
- `capteur kay3tini ar9am ghalta`

Semantic boundary:
- `ar9am ghalta` is a patient report of suspected inaccurate readings, not proof of a hardware failure.

### 65 — Insulin forgotten / not taken
Accepted:
- `nsit l’insuline`
- `ma dertch l’insuline`
- `nsit ndir l’insuline`

Not retained:
- `fout lya l’insuline`

### 66 — Accidental double insulin / dose event
Accepted:
- `dert l’insuline juj mrat`
- `3awdt dert l’insuline bla ma n9sed`
- `dert dose jouj mrat`
- `khdit l’insuline mratin b ghalat`

Safety boundary:
- this is medication-event vocabulary only. It does not authorize dose calculation, corrective dosing, treatment advice, or automated treatment action.

### 67 — Uncertainty about insulin administration
Accepted:
- `ma 3reftch wach dert l’insuline`
- `ma 3a9elch wach khdit l’insuline`
- `chkit wach dert l’insuline wela la`
- `ma mt2akedch wach dert dose`

Safety boundary:
- uncertainty must remain uncertainty. These formulations must not be normalized into a confirmed administered or missed dose.

## Cross-batch safety observations

1. Arabizi is not a mechanical transliteration layer. Only reviewed forms belong in this working evidence set.
2. Hyperbolic lethal vocabulary (`mout`, `lmout`, `nmout`, `miet`, `kay9tel`, `kay9telni`, `y9telni`) requires contextual disambiguation and must not be treated as a standalone death/self-harm/emergency trigger.
3. Ambient heat `ssehd` and fever/being febrile `skhana` remain lexically distinct in the reviewed usage.
4. CGM LOW/HIGH and numerical readings are device reports, not automatically confirmed biological values.
5. CGM/symptom discordance must preserve both evidence channels rather than overwrite one with the other.
6. Medication-event language must preserve event type and uncertainty without generating dose or treatment advice.
7. Facial asymmetry, sensory change, chest pain/pressure, dyspnea, motor deficit, speech disturbance, and visual loss remain semantically distinct even when they can co-occur clinically.

## Review rules carried forward

1. Preserve native corrections exactly as reviewed.
2. Keep broad expressions distinct from specific clinical events when ambiguity exists.
3. Record rejected candidates because false-positive control matters as much as positive recall.
4. Do not promote any item into runtime triage from this working document alone.
5. Before runtime promotion, build positive, negative, contextual, hyperbole, ambiguity, code-switch, and device-discordance regression cases for each promoted concept.
6. Runtime promotion requires the applicable clinical-safety review and existing fail-closed release gates.
