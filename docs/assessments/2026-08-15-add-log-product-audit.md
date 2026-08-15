# Add Log — product / functional / UX / UI / safety audit

Date: 2026-08-15
Baseline main: `8a2d42e3dd6e3787fe3d411d3c204afeb1208cac`
Lane: IAMINA patient-page product audit
Status: **CLOSED — runtime + post-merge recertified**

## A. Mission actuelle

Add Log permet au patient d’enregistrer rapidement une glycémie et d’y rattacher uniquement des faits contextuels liés à cette mesure.

Action principale : saisir une glycémie puis l’enregistrer.

Information principale : la valeur et son unité explicite.

Fréquence attendue : élevée, souvent plusieurs fois par jour et sur mobile.

La page mérite d’exister, mais pas comme journal générique d’événements : le modèle persistant exige `bloodSugar`.

## B. Comportement réel actuel

Add Log est un écran plein écran autour de `AddLogSheet`.

Le chemin principal contient : glycémie, contexte de mesure facultatif, repas facultatif, puis détails progressifs pour heure et contexte additionnel.

Le repas peut inclure taxonomie, aliments récents/habituels, recherche, reconnaissance photo sous consentement, portions et note libre.

La sortie protège les données non enregistrées. L’enregistrement d’une glycémie basse déclenche un gate déterministe avant sauvegarde. Un reçu factuel est affiché après succès.

Décision produit A validée : les prises médicamenteuses, y compris l’insuline, sont canoniques dans Medications et ne sont plus saisies depuis Add Log.

## C-D. Inventaire fonctionnel et verdicts

| Fonction | Utilité | Fréquence | Efficacité | Problème | Verdict | Action |
|---|---|---:|---|---|---|---|
| Saisie glycémie | Essentielle | Haute | Haute | CTA auparavant actif à vide | IMPROVE | Save désactivé tant que la valeur positive n’est pas parsable |
| Unité visible | Essentielle | Haute | Haute | Aucun défaut majeur | KEEP | Unité du profil visible à côté de la valeur |
| Contexte glycémique | Haute | Haute | Haute | Aucun contexte ne doit être inféré | KEEP | Explicite et facultatif |
| Repas facultatif | Moyenne/haute | Moyenne | Bonne | Flow riche si développé | KEEP | Fermé par défaut |
| Type de repas | Moyenne | Moyenne | Bonne | Doit rester indépendant du contexte glycémique | KEEP | Persistance séparée |
| Recherche aliments | Moyenne | Moyenne | Bonne | Complexité acceptable seulement dans le flow repas | KEEP | Contextuelle |
| Récents / habituels | Moyenne | Moyenne | Haute | Dépend de l’historique | KEEP | Dans le repas |
| Reconnaissance photo | Moyenne | Faible/moyenne | Bonne | Risque si ajout automatique | KEEP | Consentement + confirmation humaine obligatoires |
| Portions | Moyenne | Faible/moyenne | Bonne | Peut alourdir | KEEP | Seulement après sélection d’aliments |
| Note libre repas | Faible/moyenne | Faible | Acceptable | Donnée non structurée | SIMPLIFY | Facultative et secondaire |
| Heure | Essentielle | Moyenne | Haute | Modification rare | KEEP | Défaut = maintenant, édition en détails |
| Maladie / stress / activité / sommeil | Moyenne | Faible/moyenne | Bonne | Charge si toujours visible | KEEP | Disclosure progressif |
| Insuline prise dans Add Log | Forte isolément | Moyenne | Dupliquée | Deux sources de vérité avec MedicationEvents | REMOVE | Medications devient la source canonique |
| Focus Add Log `insulin` | Faible / legacy | Rare | Trompeur | Ouvre un flow non canonique | MOVE | Routé vers Medications |
| Protection brouillon | Haute | Moyenne | Haute | Aucun | KEEP | Confirmation de sortie |
| Gate glycémie basse | Critique safety | Événementiel | Haute | Doit rester déterministe et non prescriptif | KEEP | Seuils et wording factuel conservés |
| Reçu post-save | Haute | Haute | Haute | Ne doit pas réintroduire l’insuline dupliquée | IMPROVE | Reçu glucose/contexte uniquement pour les nouvelles entrées |

## E. Charge cognitive

**Bonne au repos.**

La page expose une valeur dominante, un contexte facultatif, un repas facultatif et un seul accès aux détails. Les fonctions rares sont masquées. Le défaut principal était l’ambiguïté de périmètre : Add Log semblait pouvoir journaliser plusieurs événements alors que le modèle exige une glycémie. Cette ambiguïté est supprimée.

## F. UX / flow

Chemin fréquent final :

1. ouvrir Add Log ;
2. saisir la glycémie ;
3. éventuellement choisir un contexte ;
4. enregistrer.

Le CTA est inactif tant que la glycémie n’est pas une valeur positive parsable. L’heure reste préremplie à maintenant. Le repas et les contextes quotidiens restent facultatifs. La sortie avec brouillon demande confirmation.

## G. UI / hiérarchie

Le shell/header global certifié n’a pas été redessiné. La glycémie reste le contrôle dominant. Repas et détails restent secondaires et progressifs.

Capture Chrome réelle exact-head pré-merge `14d4e9102a054a8c6f3702585e6bd39af31caa57` : Chrome #24 SUCCESS. Artefact ID `9250581070`, digest `sha256:f6b059b90d3e4faf74a0dfd779ef0f1990e9c6c948d6db0c8d403c66f6f02067`.

Capture Chrome réelle post-merge sur `main` `78f9a7d26640a4fa734317ba52501c9b18a69055` : Chrome #25 SUCCESS. Artefact ID `9250831118`, digest `sha256:23f83e2d7cc28eb46ebc4e4a3109fdb697f03cd0d18aafa7acf4920c48ed0719`.

Inspection manuelle post-merge 390×844 : hiérarchie propre, glycémie dominante, CTA correctement désactivé à vide, détails simplifiés « Détails : heure et contexte… », aucune dose d’insuline visible, aucun overflow ni collision visible.

## H. Accessibilité

Forces certifiées :

- clavier numérique pour glycémie ;
- unité visible ;
- semantics sur la zone glycémie ;
- actions tactiles dimensionnées ;
- alerte basse avec texte, pas uniquement couleur ;
- contenu arabe RTL réel ;
- UI screenshot audit #65 SUCCESS pré-merge ;
- UI screenshot audit #66 SUCCESS post-merge ;
- Chrome réel #24 SUCCESS pré-merge ;
- Chrome réel #25 SUCCESS post-merge.

## I. Safety / truthfulness / intégrité

- aucune glycémie n’est préremplie ou inférée ;
- aucun contexte glycémique n’est inféré ;
- aucun repas n’est inféré ;
- la reconnaissance photo ne persiste rien sans confirmation ;
- aucune dose recommandée n’est calculée ;
- le gate d’hypoglycémie reste déterministe ;
- l’insuline n’est plus saisie depuis Add Log ;
- Medications est la surface canonique des prises ;
- le champ legacy nullable `LogEntries.insulinUnits` reste pour compatibilité historique ; les nouvelles entrées Add Log écrivent `null`.

## J. Ce qui manque

Aucune nouvelle fonctionnalité n’est justifiée pour ce lot.

La répétition automatique d’une valeur récente n’est pas ajoutée : une glycémie ne doit pas être silencieusement réutilisée.

## K. À supprimer complètement

- saisie de dose d’insuline dans Add Log — **supprimée** ;
- `AddLogFocus.insulin` — **supprimé**.

## L. À fusionner

Aucune fusion supplémentaire nécessaire dans Add Log.

## M. À déplacer

Toute prise médicamenteuse, y compris insuline → Medications — **effectif**.

Le legacy `/ajouter?focus=insulin` ouvre Medications.

## N. À simplifier

- CTA Save conditionné à une glycémie valide — **effectif** ;
- détails limités à heure + contexte factuel — **effectif** ;
- aucune exposition de dose dans ce flow — **effectif**.

## O. Version idéale retenue

1. glycémie + unité explicite ;
2. contexte glycémique facultatif ;
3. repas facultatif progressif ;
4. détails facultatifs : heure + contexte quotidien ;
5. CTA persistant activé seulement avec glycémie valide ;
6. gate déterministe si glycémie basse ;
7. reçu factuel après sauvegarde.

Pas de dose médicamenteuse et pas de prétention de journal générique.

## P. Priorisation

### BLOCKER

Double source d’insuline Add Log / Medications — **résolu**.

### HIGH VALUE

- Save conditionné à une valeur valide — **résolu**.
- Legacy insulin focus déplacé vers Medications — **résolu**.

### MEDIUM

- Disclosure progressif — **conservé**.

### POLISH

Aucun polish supplémentaire requis par l’inspection Chrome post-merge.

## Q. Score final

Baseline avant implémentation : **7.9/10**.

**Score final : 9.6/10 — PASS.**

Fondement :

- fonctionnalité / intégrité des données : 9.7 ;
- safety / truthfulness : 9.7 ;
- UX / efficacité : 9.6 ;
- UI / hiérarchie mobile : 9.6 ;
- accessibilité / localisation : 9.5 ;
- maintenabilité : 9.3, pénalisée uniquement par le bridge de header legacy et la compatibilité de route conservée.

Aucun finding BLOCKER/HIGH non résolu dans le scope Add Log.

## R. Implémentation et preuve pré-merge

Branche runtime : `agent/add-log-product-audit`
PR runtime : #243
Head exact certifié : `14d4e9102a054a8c6f3702585e6bd39af31caa57`
Merge runtime : `78f9a7d26640a4fa734317ba52501c9b18a69055`

Implémenté :

- suppression de l’input insuline d’Add Log ;
- suppression de `AddLogFocus.insulin` ;
- redirection du focus legacy insulin vers Medications ;
- nouvelles entrées Add Log avec `insulinUnits = null` ;
- Save désactivé avant glycémie valide ;
- tests ciblés mis à jour ;
- contrat de routage legacy ajouté.

Gates exact-head pré-merge :

- CI #2408 — SUCCESS ;
- Django migration drift #2220 — SUCCESS ;
- UI screenshot audit #65 — SUCCESS ;
- UI browser screenshot certification Chrome #24 — SUCCESS.

## S-Y. Recertification post-merge

Sur le vrai `main` `78f9a7d26640a4fa734317ba52501c9b18a69055` :

- CI #2412 attempt 2 — SUCCESS ;
- Backend ruff + pytest — SUCCESS ;
- Backend PostgreSQL source-of-truth — SUCCESS ;
- Secret hygiene — SUCCESS ;
- Frontend analyze + tests — SUCCESS ;
- Django migration drift #2224 — SUCCESS ;
- UI screenshot audit #66 — SUCCESS ;
- UI browser screenshot certification Chrome #25 — SUCCESS ;
- inspection manuelle Chrome #25 — PASS.

La première tentative de CI #2412 avait été annulée ; elle a été relancée et l’attempt 2 est verte. Aucune correction runtime post-merge n’a été nécessaire.

## Z. Closeout documentaire

`docs/ROADMAP.md` et `docs/TECHDEBT.md` ont été inspectés pendant le lot. Aucun changement de vérité forward ne justifie de modifier leur contenu : le numerator MENA reste 32/41 et les dettes frontend ouvertes ne sont pas entièrement closes par Add Log.

README/ARCHITECTURE/SPECS/MEDICAL_DATA_PLAN : aucune vérité affectée justifiant une modification.

**Conclusion : Add Log CLOSED et recertifié.**
