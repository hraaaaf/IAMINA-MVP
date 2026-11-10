# IAMINA B / D15 — Brouillon repas multimodal unique (Web) — Préflight autonome, 03/11/2026

## Décision et limites
**Goal :** démontrer que les données du repas, quelles que soient leurs entrées (sélection manuelle, note saisie ou issue d'une dictée, quantité en grammes, suggestions photo synthétiques explicitement confirmées) convergent vers un seul brouillon éditable. **Succès :** aucun insert en cours de saisie ou de proposition, puis **exactement un** insert local Drift après un **vrai clic Save** ; contenu fidèle au choix utilisateur, pas de prescription ni d'inférence de dose. **Preuve :** nouveaux tests Flutter à faire réussir sur ce HEAD exact, avec suite CI et rapport après run.

**Arbitrage propriétaire 03/11 : D14 mise en STAND-BY.** Le préflight D14 est favorable sur scénario synthétique mais l'utilisation de photos réelles dépend de D24 (consentement IA/egress), D18 coffre Web (traitée dans une autre fenêtre), gouvernance fournisseur, sécurité/privacy et revue clinique. Ne rien modifier dans D14/D18/D24, ne jamais activer de fournisseur réseau. D15 **dépend de D14 et D13** pour clôture ; seul le sous-lot **test-only autonome** est ici autorisé. Voir [ordre canonique B](https://app.notion.com/p/40777c6633628177b325d3cb5412fc18) et [journal chantier B](https://app.notion.com/p/40777c66336281729c03c9bb294e71b7).

## Baseline, vérifications et delta
- Base Git vérifiée : `main@c2fc32bbd31a24fe17542e6abda96d937905737b`.
- Ancienne [PR D15 #978](https://github.com/hraaaaf/IAMINA-MVP/pull/978) : OPEN/DRAFT, `mergeable=false`, base historique `13b7cce`. Elle prouve un contrat synthétique avec 4 tests, mais son insert local Drift est **simulé directement dans le test**, pas déclenché par le bouton Save de l'écran Web. Ne pas fusionner ce candidat ancien.
- **Delta candidat** : restaurer le test de convergence synthétique de #978 sur main courante (4 tests, fake vision uniquement), puis **nouveau test** `D15 real Save` dans la suite `frontend/test/features/add_log_sheet_test.dart` : Web layout 390×844, saisie glucose 126, repas facultatif, note FR/AR, recherche catalogue "oeuf" et sélection de l'aliment canonique `egg`, 75 grammes saisis manuellement, **0 ligne Drift avant Save**, appui sur vrai bouton `save-log-button`, **1 ligne**, champs et réception exacts, insuline nulle.
- Aucun écran visuel ni code de production changé : pas de mockup obligatoire ; les essais couvrent le rendu widget mais **ne remplacent pas un E2E navigateur d'une photo/voix réelle**. Pas de snapshots clinique, pas de photo ou audio patient.

## Risques / gates
1. **D14 bloquée** : injection photo synthétique dans le test uniquement ; aucun droit d'envoyer une image, aucune proposition non confirmée ne peut persister.
2. **D13 brouillons** : la navigation/abandon et les sauvegardes en vol nécessitent la preuve d'intégration D13 avant toute clôture réelle de D15 ; l'ancienne PR D13 #1215 est CLOSED sans merge.
3. **Voix** : l'interface de dictée et ses contrôles de sauvegarde restent soumis à D24 et à la politique audio ; ce lot ne teste que le stockage d'une note volontaire, non une vraie transcription fournisseur.
4. **Clinique** : la portion en grammes est saisie par le patient, non déduite d'une photo ; tout calcul de glucides/insuline et seuil de validation clinique restent hors de ce test.
5. **Gouvernance** : revue privacy/clinique humaine requise avant activation, pas de merge ni Vercel sans accord exprès.

## Séquence restante
Test Flutter ciblé -> CI complète du SHA exact -> correction si rouge -> preuve GitHub/Notion -> STAND-BY fonctionnel D15 jusqu'à levée D14/D13 -> véritable recette Web ensuite, approbation humaine. **État historique à l'ouverture : CI non vérifiée.** Verdict exact-SHA prouvé dans le closeout ci-dessous.

## Closeout du préflight autonome D15 — 03/11/2026 (HEAD correctif `b90e5480`)

**Résultat — preuves exécutées :** [PR Draft #1258](https://github.com/hraaaaf/IAMINA-MVP/pull/1258), branche `test/iamina-b-d15-web-single-draft-20261103`, commit testé exact `b90e54804c601e7bf23832ce76a9e89cb77b46c2`. **2/2 workflows complets SUCCESS** : [CI Frontend #41734935481](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41734935481) et [P5-5 #41734935492](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41734935492). Job Frontend `126261647770` SUCCESS (analyze Flutter, **972 tests PASS, 7 skipped, 0 failed**, build Web release). Jobs backend SQLite et PostgreSQL **skipped, pas PASS**, car seuls tests/doc Flutter sont modifiés.

**Contrat D15 effectivement observé dans logs** : cinq tests D15 PASS : nouveau test du formulaire `AddLogSheet` qui sélectionne `egg` à l'écran 390×844, saisi note FR/AR et 75g, vérifie 0 ligne Drift avant un vrai tap `save-log-button` puis 1 ligne avec `mealDescription`, `mealItemsJson`, `mealPortionsJson` vérifiés et insuline nulle ; quatre tests synthétiques hérités #978 (candidats photo seulement après confirmation, fallback sans mutation, IDs inconnus éliminés, source path unique pour note/voix/items/portions/Save). **Photo et voix fournisseur réelles NON testées** ; la sélection photo est mockée en mémoire dans un autre test et l'insertion du contrat image n'est pas un test navigateur de Save.

**Incident corrigé sans altérer le produit** : CI antérieure [#41733967630](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41733967630) = 971 PASS, 1 FAIL, 7 SKIPPED. Cause : l'ancien helper de tap faisait un drag −175px après `ensureVisible`, plaçant `meal-search-egg` à Y=−143px hors écran. Patch `b90e5480` uniquement dans `frontend/test/features/add_log_sheet_test.dart` : recentrage conditionnel et `hitTestable()` avant clic. La CI a confirmé le test au second SHA ; 0 fichier produit modifié par D15.

**Conclusion bornée** : **D15 sous-lot préflight autonome TEST-ONLY PASS sur `b90e5480`** ; la **D15 globale reste ouverte / dependency-blocked** jusqu'à D13 (brouillons / sauvegarde en cours) + D14 (photo / consentement), privacy/clinique et vérification Web autorisée. D14 officiellement STAND-BY ; aucun merge, aucune preview Vercel, aucune activation patient. La mise à jour documentaire présente constitue un SHA Git ultérieur distinct : ne pas propager mécaniquement 2/2 sans contrôler ses workflows.

**Next exact** : vérifier les CI éventuelles du commit documentaire, figer dossier et Notion en préflight PASS, puis attendre levée vérifiée de D13/D14 pour D15 fonctionnelle ; pas de travaux sur D14, D18 ou D24 dans cette PR.
