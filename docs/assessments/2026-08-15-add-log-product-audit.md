# Add Log — product / functional / UX / UI / safety audit

Date: 2026-08-15
Baseline main: `8a2d42e3dd6e3787fe3d411d3c204afeb1208cac`
Lane: IAMINA patient-page product audit
Status: **OPEN — HUMAN GATE REQUIRED BEFORE DATA-MODEL CHANGE**

## A. Mission actuelle

Enregistrer rapidement une **mesure de glycémie réellement observée**, avec un contexte facultatif, sans inférer de cible, de cause, de traitement ou de dose.

La route et certains focus (`meal`, `activity`, `insulin`) suggèrent toutefois une mission plus large de journalisation d'événements. Le modèle persistant ne permet pas cette mission plus large car `LogEntries.bloodSugar` est obligatoire.

## B. Comportement réel actuel

- `/ajouter` ouvre `AddLogScreen`.
- `AddLogScreen` remplace visuellement le header interne de `AddLogSheet` par le header patient canonique via `AminaLegacyPageHeaderBridge`.
- La glycémie est obligatoire et stockée normalisée en mg/dL.
- L'unité affichée vient du profil (`mg/dL` par défaut, `mmol/L` converti à l'enregistrement).
- Le contexte glycémique est facultatif et jamais inféré.
- Le repas est facultatif et progressif.
- Les détails heure / insuline prise / contexte complémentaire sont masqués par défaut sur mobile.
- La date/heure est initialisée à maintenant, modifiable jusqu'à 90 jours dans le passé, jamais dans le futur.
- Une glycémie basse déclenche un avertissement déterministe avant sauvegarde.
- Après sauvegarde, un reçu factuel local est affiché puis le brouillon est remis à zéro.
- Quitter avec des données non sauvegardées déclenche une confirmation.

## C–D. Inventaire fonctionnel et verdicts

| Fonction | Utilité | Fréquence probable | Efficacité | Problème principal | Verdict | Action recommandée |
|---|---|---:|---|---|---|---|
| Saisie glycémie | Essentielle | Haute | Haute | Aucune anomalie structurelle | KEEP | Garder au premier plan, unité toujours visible |
| Unité profil + normalisation mg/dL | Essentielle | Permanente | Haute | Doit rester explicite | KEEP | Conserver l'unité visible et la conversion déterministe |
| Contexte à jeun / avant / après / autre | Utile | Haute | Haute | 4 choix toujours visibles mais charge faible | KEEP | Ne jamais préselectionner |
| Heure par défaut = maintenant | Essentielle | Permanente | Haute | Aucun | KEEP | Garder masquée dans les détails sauf backdating |
| Backdating date + heure | Utile | Occasionnelle | Moyenne | 2 pickers successifs | IMPROVE | À terme réduire la friction sans accepter le futur |
| Repas facultatif | Utile | Moyenne | Bonne | Peut devenir riche une fois ouvert | KEEP | Garder progressif et fermé par défaut |
| Type de repas | Utile | Moyenne | Haute | Doit rester indépendant du contexte glycémique | KEEP | Conserver indépendance et vocabulaire Ramadan contextuel |
| Recherche aliments | Utile | Moyenne | Bonne | Plus lente qu'un récent/habituel | KEEP | Récents/habituels avant recherche |
| Aliments récents / habituels | Haute valeur | Moyenne | Haute | Aucun si fondé uniquement sur historique réel | KEEP | Conserver comme accélérateur factuel |
| Reconnaissance photo repas | Secondaire | Occasionnelle | Moyenne | IA + consentement + confirmation nécessaires | KEEP | Conserver explicitement opt-in, jamais ajouter sans confirmation |
| Portions / nutrition documentée | Secondaire | Occasionnelle | Bonne | Risque si donnée nutritionnelle non sourcée | KEEP | Garder fallback « non chiffrée » et provenance |
| Note libre de repas | Faible à moyenne | Occasionnelle | Moyenne | Texte libre peu structuré | SIMPLIFY | Rester facultative, ne pas remonter au flow primaire |
| Détails secondaires | Utile | Occasionnelle | Haute | Aucun au repos | KEEP | Continuer progressive disclosure |
| Insuline prise dans Add Log | Utile en contexte | Moyenne | Techniquement rapide | **Double source de vérité avec `MedicationEvents`** | MOVE | Recommandation: une seule source canonique de prises; ne pas maintenir deux stockages parallèles |
| Activité physique booléenne | Contexte utile | Occasionnelle | Bonne comme contexte | Le focus `activity` ressemble à un événement autonome alors que ce n'en est pas un | IMPROVE | Renommer/présenter comme contexte de la mesure tant qu'aucun vrai modèle événement n'existe |
| Malade / stress / mauvais sommeil | Contexte utile | Occasionnelle | Bonne | Peut être pris à tort pour causalité si réutilisé ailleurs | KEEP | Conserver comme observation déclarative, jamais comme cause |
| Focus route `meal` | Navigation utile | Occasionnelle | Partielle | Ouvre le repas mais exige toujours glycémie | IMPROVE | Soit assumer « repas lié à une mesure », soit créer un vrai modèle d'événement après gate |
| Focus route `activity` | Faible actuellement | Rare | Faible | N'enregistre pas une activité autonome | REMOVE | Si aucun appel réel n'en dépend, supprimer ce faux raccourci; sinon human gate produit |
| Focus route `insulin` | Faible actuellement | Rare | Ambiguë | Duplique Medications | MOVE | Rediriger vers la source canonique de prise après décision produit |
| Confirmation hypo | Safety essentielle | Rare mais critique | Haute | Ne doit pas devenir prescription personnalisée | KEEP | Conserver classification déterministe et wording non prescriptif |
| Reçu post-save | Haute valeur | Haute | Haute | Aucun | KEEP | Conserver résumé factuel + accès Journal |
| Brouillon + confirmation de sortie | Haute valeur | Occasionnelle | Haute | Aucun | KEEP | Conserver |
| CTA fixe Enregistrer | Essentiel | Haute | Haute | Actif même à vide, l'erreur n'arrive qu'après tap | IMPROVE | Validation inline/état explicite sans cacher l'action aux technologies d'assistance |
| Header canonique via bridge de clipping | Présentation | Permanente | Visuellement correcte | Dette technique: second header toujours construit puis masqué | SIMPLIFY | Retirer le bridge lors d'un refactor sûr; ne pas modifier la logique métier pour du cosmétique |
| Symptômes génériques / note d'événement | Valeur non démontrée ici | Inconnue | Absente | Ajouter alourdirait le flow et nécessite un vrai modèle événement | REMOVE | Ne pas ajouter au formulaire glycémie actuel sans besoin prouvé |

## E. Charge cognitive

**Verdict: correctement chargée au repos.**

La capture Chrome 390×844 montre uniquement: glycémie, unité, contexte facultatif, bouton repas facultatif, bouton détails, CTA fixe. Les fonctions riches sont progressives. Ajouter davantage de types ou de cartes au premier niveau dégraderait le flow.

## F. UX / flow

### Glycémie fréquente

Depuis Add Log ouvert:
1. tap champ glycémie;
2. saisie numérique;
3. tap Enregistrer.

Contexte connu: +1 tap sur une chip.

Points forts:
- heure sûre préremplie à maintenant;
- unité visible;
- contexte jamais supposé;
- CTA fixe utilisable à une main;
- confirmation avant perte du brouillon;
- reçu de sauvegarde vérifiable.

Friction:
- CTA ne reflète pas la validité avant le tap;
- backdating utilise date puis heure séparément;
- les focus meal/activity/insulin promettent plus que ce que le modèle sait réellement enregistrer.

## G. UI / hiérarchie

La hiérarchie primaire est correcte et le shell visuel certifié doit être conservé. Aucun redesign global n'est justifié.

Le bridge de header est une dette d'implémentation, pas une raison de redessiner l'écran.

## H. Accessibilité

Points vérifiés dans le code:
- boutons principaux >= 48/50/52/54 px selon les contrôles;
- tooltip sur retour;
- `Semantics` autour du bloc glycémie;
- localisation FR/EN/AR et tests RTL existants;
- navigation scrollable et CTA fixe.

À certifier avant PASS:
- ordre VoiceOver du champ glycémie + unité + helper;
- focus lors de l'ouverture du clavier;
- annonce du warning hypo et des erreurs;
- absence de masquage sémantique causé par le header bridge.

## I. Safety / truthfulness / intégrité

### PASS vérifiés

- aucune glycémie inventée;
- aucune cible déduite de la valeur saisie;
- aucun contexte sélectionné par défaut;
- insuline explicitement décrite comme **déjà prise**;
- aucune recommandation de dose;
- photo repas opt-in avec consentement et confirmation;
- reçu post-save factuel;
- seuils hypo implémentés de manière déterministe: niveau 1 `<70 et >=54 mg/dL`, niveau 2 `<54 mg/dL`.

### BLOCKER produit/data

`LogEntries.insulinUnits` et `MedicationEvents` permettent deux enregistrements indépendants d'une prise médicamenteuse/insuline. Add Log et Medications n'ont pas de source de vérité commune ni de mécanisme de déduplication.

Par ailleurs `LogEntries.bloodSugar` est non nullable. Un repas, une activité ou une prise d'insuline **ne peut donc pas être un événement autonome** dans Add Log, malgré les focus de route existants.

Aucune migration ou modification de cette signification persistée ne doit être faite sans human gate.

## J. Ce qui manque

Aucune nouvelle fonction ne doit être ajoutée au flow glycémie tant que le contrat produit « mesure de glycémie » versus « journal générique d'événements » n'est pas tranché.

Manque réellement utile après décision:
- une source canonique unique pour les prises;
- si IAMINA veut de vrais événements autonomes: un modèle typé qui n'exige pas artificiellement une glycémie.

## K. À supprimer complètement

- Ne pas ajouter de symptôme générique, note générique ou autre champ visible par défaut au flow actuel.
- `AddLogFocus.activity` est candidat REMOVE si aucun appel réel n'en dépend et si l'activité reste seulement un contexte.

## L. À fusionner

- La capture de prise d'insuline doit être fusionnée conceptuellement avec la source de vérité des prises de Medications, pas dupliquée.

## M. À déplacer

- Recommandation: MOVE la création d'une prise d'insuline vers la source canonique de Medications, ou faire consommer cette même source par Add Log après arbitrage.

## N. À simplifier

- dette de header bridge;
- feedback de validité du CTA;
- note libre repas doit rester secondaire;
- ne pas exposer des focus qui ne correspondent pas à de vrais événements persistables.

## O. Version idéale proposée

### Variante recommandée tant que le modèle reste « mesure de glycémie »

1. Header canonique.
2. Carte glycémie avec unité, saisie numérique et feedback factuel.
3. Chips contexte facultatives.
4. Actions progressives:
   - Ajouter un repas;
   - Ajouter des détails.
5. Détails:
   - heure;
   - contexte complémentaire;
   - lien vers « Enregistrer une prise » si nécessaire, mais **pas deuxième stockage**.
6. CTA fixe.
7. Reçu factuel avec correction / Journal.

Cette version ne transforme pas Add Log en formulaire médical générique.

### Variante événement générique

Nécessite un changement de modèle persisté et une décision produit explicite. Elle n'est pas implémentable comme simple amélioration UX.

## P. Priorisation

### BLOCKER

1. Double source de vérité pour insuline / prise (`LogEntries.insulinUnits` vs `MedicationEvents`).
2. Contrat produit ambigu: route/focus générique versus glycémie obligatoire.

### HIGH VALUE

1. Rendre cohérente la navigation `meal/activity/insulin` avec la réalité persistée.
2. Feedback de validation avant sauvegarde invalide.
3. Certifier l'accessibilité réelle du champ principal et des alertes.

### MEDIUM

1. Réduire la friction du backdating.
2. Simplifier la dette du header bridge sans changer le rendu canonique.

### POLISH

Aucun redesign cosmétique prioritaire.

## Q. Score actuel

### Score provisoire fondé sur le code + tests existants + capture Chrome baseline: **7.9/10 — FAIL**

Le score ne peut pas être élevé malgré une UI/UX primaire solide, car l'intégrité inter-pages et la mission produit ne sont pas résolues.

Grille provisoire:
- mission produit: 6.5/10;
- fonctionnalités / cohérence: 6.5/10;
- efficacité: 8.5/10;
- utilité / fréquence: 8.5/10;
- charge cognitive: 9.0/10;
- UX / flow: 8.5/10;
- UI / hiérarchie: 9.0/10;
- safety / truthfulness / intégrité: 7.0/10 à cause du double stockage potentiel;
- accessibilité: 7.5/10 avant certification assistive complète;
- opportunités produit maîtrisées: 8.0/10.

Moyenne: 7.9/10.

## R–Z. État d'exécution

- R. Implémentation améliorations sûres: **en cours; aucune signification persistée modifiée**.
- S. Tests: tests Add Log existants inspectés; nouveaux tests à produire après décision de contrat.
- T. Capture baseline: Chrome réel 390×844, artifact post-merge précédent `9248830522`.
- U. Avant/après: en attente du changement runtime.
- V. Nouveau scoring: en attente.
- W. Exact-head: en attente.
- X. Merge: en attente.
- Y. Post-merge: en attente.
- Z. Closeout docs: en attente.

## Human gate

Décision requise avant toute modification du modèle ou déplacement définitif de la prise d'insuline:

**IAMINA doit-il garder Add Log comme saisie rapide d'une mesure de glycémie avec contexte, et faire de Medications l'unique source de vérité pour les prises, ou transformer Add Log en vrai journal générique d'événements avec un modèle persistant typé ?**

Recommandation produit: **garder Add Log centré sur la glycémie + contexte et rendre Medications canonique pour les prises**. C'est plus simple, moins ambigu, plus sûr et cohérent avec le principe « moins de décisions, moins de taps ». Un journal événementiel générique ne doit être créé que si un besoin utilisateur réel le justifie.
