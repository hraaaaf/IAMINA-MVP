# Medications — product / functional / UX / UI / safety audit

Date: 2026-08-15
Lane: IAMINA patient-page product audit
Status: runtime merged — post-merge recertification pending

## Mission

Medications est la surface canonique pour journaliser les prises médicamenteuses réellement effectuées, y compris l’insuline. Elle ne prescrit, ne recommande et ne calcule aucune dose.

## Baseline observée

Chrome réel 390×844 :

- header canonique `Médicaments` ;
- carte `Nouvelle prise` ;
- disclaimer explicite : IAmina ne recommande ni médicament ni dose ;
- nom du traitement ;
- dose facultative ;
- unité ;
- heure de prise ;
- CTA `Enregistrer la prise` ;
- liste `Prises récentes`.

La hiérarchie visuelle est claire et calme, sans overflow visible.

## Findings corrigés

### BLOCKER — intégrité de dose saisie

Avant correction, une dose invalide pouvait être perdue ou persistée de façon incohérente. Une unité pouvait aussi survivre sans dose.

Verdict : **IMPROVE**.

Correctif : si une dose est saisie, elle doit être parsable, finie et strictement positive. Une unité sans dose est refusée. Aucun seuil thérapeutique ni recommandation de dose n’est ajouté.

### HIGH — CTA actif sans traitement

Avant correction, le CTA restait actif même si le nom était vide ; `_save()` échouait silencieusement.

Verdict : **IMPROVE**.

Correctif : CTA désactivé tant que le nom du traitement est vide.

### HIGH — suppression immédiate

Avant correction, une prise pouvait être supprimée par un tap unique sans confirmation.

Verdict : **IMPROVE**.

Correctif : confirmation explicite avant suppression.

## Verdicts fonctionnels

| Fonction | Verdict | Motif |
|---|---|---|
| Nom du traitement libre | KEEP | fait réellement pris, sans catalogue prescriptif |
| Dose facultative | KEEP + IMPROVE | utile mais validation factuelle obligatoire |
| Unité libre | KEEP + IMPROVE | compatible avec plusieurs traitements, mais jamais orpheline |
| Heure de prise | KEEP | factuelle, éditable jusqu’à 365 jours |
| Disclaimer non-prescriptif | KEEP | safety essentielle |
| Liste récente | KEEP | vérification immédiate du journal |
| Suppression | IMPROVE | confirmation requise |
| Suggestion de médicament/dose | REMOVE / ne pas ajouter | hors périmètre et prescriptif |

## Safety / truthfulness

- aucune recommandation de médicament ;
- aucune recommandation ou calcul de dose ;
- aucune normalisation clinique automatique ;
- seules les données déclarées par l’utilisateur sont journalisées ;
- la validation ajoutée contrôle uniquement la cohérence syntaxique et structurelle de la donnée saisie.

## UI / UX

Le rendu mobile est fort : carte unique, champs essentiels, heure visible, CTA dominant, historique immédiatement sous le formulaire. Aucun redesign structurel n’est justifié.

Inspection manuelle Chrome #28, 390×844 : aucun overflow, aucune collision, CTA bien désactivé à vide, disclaimer visible, hiérarchie intacte.

## Tests / gates exact-head

Head certifié avant merge : `eec071e712c3f295378a849045ee264ea45c9249`

- CI #2430 ✅
- Django migration drift #2242 ✅
- UI screenshot audit #69 ✅
- UI browser screenshot certification #28 ✅
- artefact Chrome : `iamina-ui-browser-cert-390x844`
- digest artefact : `sha256:7458e44b7f85bcd68a0842b400ac99079c32273abf877145dfaef0ac6be4c7c8`
- runtime merge PR #248 : `12f47a42cd3d2419e922416f4b81e533786815d6`

Le harness de test widget+Drift initial était instable ; après deux échecs similaires, il a été remplacé par des contrats ciblés sans stream vivant, tandis que Chrome réel couvre le rendu.

## Score

Baseline : **7.8/10**.

Score final : **en attente de recertification post-merge main**. Aucun 9.5+ déclaré avant cette preuve.

## Scope technique

Aucune migration, aucun changement de schéma, aucun seuil clinique, aucune logique thérapeutique, aucun changement du numerator MENA.
