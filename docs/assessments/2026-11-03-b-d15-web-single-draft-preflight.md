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
Test Flutter ciblé -> CI complète du SHA exact -> correction si rouge -> preuve GitHub/Notion -> STAND-BY fonctionnel D15 jusqu'à levée D14/D13 -> véritable recette Web ensuite, approbation humaine. **État du présent fichier : candidat rédigé, CI non vérifiée.** Aucune certification anticipée.
