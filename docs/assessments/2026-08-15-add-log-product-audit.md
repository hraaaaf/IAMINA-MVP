# Add Log — product / functional / UX / UI / safety audit

Date: 2026-08-15
Baseline main: `8a2d42e3dd6e3787fe3d411d3c204afeb1208cac`
Lane: IAMINA patient-page product audit
Status: runtime merged; post-merge main recertification pending

## A. Mission actuelle

Add Log existe pour permettre au patient d’enregistrer rapidement une glycémie et d’y rattacher uniquement des faits contextuels liés à cette mesure.

Action principale : saisir une glycémie puis l’enregistrer.

Information principale : la valeur et son unité explicite.

Fréquence attendue : élevée, souvent plusieurs fois par jour et sur mobile.

Sans cette page, la saisie manuelle serait enfouie dans Journal ou Dashboard et mélangerait capture et consultation.

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
| Saisie glycémie | Essentielle | Haute | Haute | CTA auparavant actif à vide | IMPROVE | Désactiver Save tant que la valeur positive n’est pas parsable |
| Unité visible | Essentielle | Haute | Haute | Aucun défaut majeur | KEEP | Garder l’unité du profil à côté de la valeur |
| Contexte glycémique | Haute | Haute | Haute | Aucun contexte ne doit être inféré | KEEP | Garder explicite et facultatif |
| Repas facultatif | Moyenne/haute | Moyenne | Bonne | Flow riche si développé | KEEP | Garder fermé par défaut |
| Type de repas | Moyenne | Moyenne | Bonne | Doit rester indépendant du contexte glycémique | KEEP | Persistance séparée |
| Recherche aliments | Moyenne | Moyenne | Bonne | Complexité acceptable seulement dans le flow repas | KEEP | Garder contextuelle |
| Récents / habituels | Moyenne | Moyenne | Haute | Dépend de l’historique | KEEP | Garder dans le repas |
| Reconnaissance photo | Moyenne | Faible/moyenne | Bonne | Risque si ajout automatique | KEEP | Consentement + confirmation humaine obligatoires |
| Portions | Moyenne | Faible/moyenne | Bonne | Peut alourdir | KEEP | Montrer seulement après sélection d’aliments |
| Note libre repas | Faible/moyenne | Faible | Acceptable | Donnée non structurée | SIMPLIFY | Garder facultative et secondaire |
| Heure | Essentielle | Moyenne | Haute | Modification rare | KEEP | Défaut = maintenant, édition en détails |
| Maladie / stress / activité / sommeil | Moyenne | Faible/moyenne | Bonne | Charge si toujours visible | KEEP | Disclosure progressif |
| Insuline prise dans Add Log | Forte isolément | Moyenne | Fonctionnelle mais dupliquée | Deux sources de vérité avec MedicationEvents | REMOVE | Medications devient la source canonique |
| Focus Add Log `insulin` | Faible / legacy | Rare | Trompeur | Ouvre un flow non canonique | MOVE | Rediriger vers Medications |
| Protection brouillon | Haute | Moyenne | Haute | Aucun | KEEP | Garder confirmation de sortie |
| Gate glycémie basse | Critique safety | Événementiel | Haute | Doit rester déterministe et non prescriptif | KEEP | Conserver seuils et wording factuel |
| Reçu post-save | Haute | Haute | Haute | Ne doit pas réintroduire l’insuline dupliquée | IMPROVE | Reçu glucose/contexte uniquement pour les nouvelles entrées |

## E. Charge cognitive

**Correctement chargée au repos.**

La page expose une valeur dominante, un contexte facultatif, un repas facultatif et un seul accès aux détails. Les fonctions rares sont masquées. Le défaut principal n’était pas la densité visuelle mais l’ambiguïté de périmètre : Add Log semblait pouvoir journaliser plusieurs événements alors que le modèle exige une glycémie.

## F. UX / flow

Chemin fréquent visé :

1. ouvrir Add Log ;
2. saisir la glycémie ;
3. éventuellement choisir un contexte ;
4. enregistrer.

Le CTA est maintenant inactif tant que la glycémie n’est pas une valeur positive parsable. L’heure reste préremplie à maintenant. Le repas et les contextes quotidiens restent facultatifs. La sortie avec brouillon demande confirmation.

## G. UI / hiérarchie

Le shell/header global certifié n’est pas redessiné. La glycémie reste le contrôle dominant. Repas et détails restent secondaires et progressifs.

Capture Chrome réelle exact-head `14d4e9102a054a8c6f3702585e6bd39af31caa57` certifiée via Chrome #24. Artefact `iamina-ui-browser-cert-390x844`, ID `9250581070`, digest `sha256:f6b059b90d3e4faf74a0dfd779ef0f1990e9c6c948d6db0c8d403c66f6f02067`.

L’inspection manuelle 390×844 confirme : hiérarchie propre, glycémie dominante, CTA désactivé à vide, détail simplifié « Détails : heure et contexte… », absence d’input insuline, aucun overflow/collision visible.

## H. Accessibilité

Forces certifiées :

- clavier numérique pour glycémie ;
- unité visible ;
- semantics sur la zone glycémie ;
- actions tactiles dimensionnées ;
- alerte basse avec texte, pas uniquement couleur ;
- contenu arabe RTL réel ;
- UI screenshot audit #65 SUCCESS ;
- Chrome réel #24 SUCCESS.

## I. Safety / truthfulness / intégrité

- aucune glycémie n’est préremplie ou inférée ;
- aucun contexte glycémique n’est inféré ;
- aucun repas n’est inféré ;
- la reconnaissance photo ne persiste rien sans confirmation ;
- aucune dose recommandée n’est calculée ;
- le gate d’hypoglycémie reste déterministe ;
- l’insuline n’est plus saisie depuis Add Log ;
- Medications devient la surface canonique des prises ;
- le champ legacy nullable `LogEntries.insulinUnits` reste uniquement pour compatibilité historique ; les nouvelles entrées Add Log écrivent `null`.

## J. Ce qui manque

Aucune nouvelle fonctionnalité n’est justifiée pour ce lot.

La répétition automatique d’une valeur récente n’est pas ajoutée : une glycémie ne doit pas être silencieusement réutilisée.

## K. À supprimer complètement

- saisie de dose d’insuline dans Add Log ;
- `AddLogFocus.insulin`.

## L. À fusionner

Aucune fusion supplémentaire nécessaire dans Add Log.

## M. À déplacer

Toute prise médicamenteuse, y compris insuline → Medications.

Le legacy `/ajouter?focus=insulin` ouvre Medications.

## N. À simplifier

- CTA Save désactivé tant que la glycémie n’est pas valide ;
- détails limités à heure + contexte factuel ;
- aucune exposition de dose dans ce flow.

## O. Version idéale proposée

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

Double source d’insuline Add Log / Medications. **Résolu.**

### HIGH VALUE

- Save conditionné à une valeur valide. **Résolu.**
- Legacy insulin focus déplacé vers Medications. **Résolu.**

### MEDIUM

- Conserver le disclosure progressif. **Conservé.**

### POLISH

Aucun polish supplémentaire requis par l’inspection Chrome.

## Q. Score actuel

Score baseline avant implémentation : **7.9/10**.

Score final interdit tant que la recertification post-merge de `main` n’est pas terminée. L’exact-head candidat a satisfait tous les gates pré-merge requis.

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

Aucune migration, aucun seuil clinique, aucune logique de dose et aucun numerator MENA modifiés.

## S-Y. Certification restante

Reste avant fermeture réelle :

1. CI / drift / UI / Chrome post-merge sur le vrai `main` `78f9a7d26640a4fa734317ba52501c9b18a69055` ;
2. score final fondé sur preuve ;
3. closeout documentaire mergé.

## Z. Closeout documentaire

`docs/ROADMAP.md` et `docs/TECHDEBT.md` ont été inspectés pendant le lot. Aucun changement de vérité forward ne justifie de modifier leur contenu à ce stade : le numerator MENA reste 32/41 et les dettes frontend ouvertes ne sont pas entièrement closes par Add Log.

README/ARCHITECTURE/SPECS/MEDICAL_DATA_PLAN : aucune vérité affectée justifiant une modification.
