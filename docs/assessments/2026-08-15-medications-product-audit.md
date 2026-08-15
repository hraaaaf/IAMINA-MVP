# Medications — product / functional / UX / UI / safety audit

Date: 2026-08-15
Lane: IAMINA patient-page product audit
Status: implementation awaiting exact-head certification

## Mission

Medications est la surface canonique pour journaliser les prises médicamenteuses réellement effectuées, y compris l’insuline. Elle ne prescrit, ne recommande et ne calcule aucune dose.

## Baseline observée

Chrome réel 390×844 post-merge Add Log :

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

## Findings

### BLOCKER — intégrité de dose saisie

Avant correction, `double.tryParse(...)` pouvait transformer silencieusement une dose invalide en `null`, tandis qu’une valeur négative/non finie pouvait ne pas être correctement rejetée. Une unité pouvait aussi être persistée sans dose.

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

Le rendu mobile baseline est déjà fort : carte unique, champs essentiels, heure visible, CTA dominant, historique immédiatement sous le formulaire. Aucun redesign structurel n’est justifié.

## Tests ajoutés

- CTA désactivé sans nom ;
- dose négative/invalide rejetée ;
- unité sans dose rejetée ;
- décimale `4,5` persistée factuellement en `4.5` ;
- suppression confirmée avant effacement.

## Score baseline

**7.8/10** : UI solide, périmètre produit juste, mais intégrité de dose et suppression insuffisamment protégées pour une surface canonique.

Aucun score final avant CI exact-head + drift + Chrome réel + inspection manuelle + merge + post-merge.

## Scope technique

Branche : `agent/medications-product-audit`

Aucune migration, aucun changement de schéma, aucun seuil clinique, aucune logique thérapeutique, aucun changement du numerator MENA.
